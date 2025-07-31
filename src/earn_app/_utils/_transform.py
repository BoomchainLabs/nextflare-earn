from __future__ import annotations

import io
import base64
import pathlib
from typing import Any, Mapping, TypeVar, cast
from datetime import date, datetime
from typing_extensions import Literal, get_args, override, get_type_hints as _get_type_hints

import anyio
import pydantic

from ._utils import (
    is_list,
    is_given,
    lru_cache,
    is_mapping,
    is_iterable,
)
from .._files import is_base64_file_input
from ._typing import (
    is_list_type,
    is_union_type,
    extract_type_arg,
    is_iterable_type,
    is_required_type,
    is_annotated_type,
    strip_annotated_type,
)
from .._compat import get_origin, model_dump, is_typeddict

_T = TypeVar("_T")


# TODO: support for drilling globals() and locals()
# TODO: ensure works correctly with forward references in all cases


PropertyFormat = Literal["iso8601", "base64", "custom"]


class PropertyInfo:
    """Metadata class to be used in Annotated types to provide information about a given type.

    For example:

    class MyParams(TypedDict):
        account_holder_name: Annotated[str, PropertyInfo(alias='accountHolderName')]

    This means that {'account_holder_name': 'Robert'} will be transformed to {'accountHolderName': 'Robert'} before being sent to the API.
    """

    alias: str | None
    format: PropertyFormat | None
    format_template: str | None
    discriminator: str | None

    def __init__(
        self,
        *,
        alias: str | None = None,
        format: PropertyFormat | None = None,
        format_template: str | None = None,
        discriminator: str | None = None,
    ) -> None:
        """
        Initialize PropertyInfo with optional metadata for property aliasing, formatting, and discrimination.
        
        Parameters:
            alias (str | None): Alternative key name to use during serialization.
            format (PropertyFormat | None): Format to apply to the property value (e.g., 'iso8601', 'base64', or 'custom').
            format_template (str | None): Custom format string for date/time formatting when format is 'custom'.
            discriminator (str | None): Optional discriminator string for distinguishing between types.
        """
        self.alias = alias
        self.format = format
        self.format_template = format_template
        self.discriminator = discriminator

    @override
    def __repr__(self) -> str:
        """
        Return a string representation of the PropertyInfo instance, including its alias, format, format template, and discriminator.
        """
        return f"{self.__class__.__name__}(alias='{self.alias}', format={self.format}, format_template='{self.format_template}', discriminator='{self.discriminator}')"


def maybe_transform(
    data: object,
    expected_type: object,
) -> Any | None:
    """
    Transforms the input data according to the expected type annotation, returning None if the input is None.
    
    Returns:
        The transformed data structure, or None if the input data is None.
    """
    if data is None:
        return None
    return transform(data, expected_type)


# Wrapper over _transform_recursive providing fake types
def transform(
    data: _T,
    expected_type: object,
) -> _T:
    """
    Transforms a data structure according to the provided type annotation, applying key aliasing and value formatting based on `Annotated` metadata.
    
    Keys and values without type information are left unchanged. Transformations such as renaming keys or formatting values (e.g., date serialization, base64 encoding) are applied only when specified by `PropertyInfo` in the type annotation.
    
    Returns:
        The transformed data structure matching the expected type annotation, with applicable serialization rules applied.
    """
    transformed = _transform_recursive(data, annotation=cast(type, expected_type))
    return cast(_T, transformed)


@lru_cache(maxsize=8096)
def _get_annotated_type(type_: type) -> type | None:
    """
    Returns the `Annotated` type if present, unwrapping `Required[Annotated[T, ...]]` if necessary; otherwise, returns `None`.
    """
    if is_required_type(type_):
        # Unwrap `Required[Annotated[T, ...]]` to `Annotated[T, ...]`
        type_ = get_args(type_)[0]

    if is_annotated_type(type_):
        return type_

    return None


def _maybe_transform_key(key: str, type_: type) -> str:
    """
    Returns the alias for a key if specified in the type's `PropertyInfo` annotation; otherwise, returns the original key.
    
    If the provided type is an `Annotated` type containing `PropertyInfo` with an `alias`, the alias is used for the key transformation.
    """
    annotated_type = _get_annotated_type(type_)
    if annotated_type is None:
        # no `Annotated` definition for this type, no transformation needed
        return key

    # ignore the first argument as it is the actual type
    annotations = get_args(annotated_type)[1:]
    for annotation in annotations:
        if isinstance(annotation, PropertyInfo) and annotation.alias is not None:
            return annotation.alias

    return key


def _no_transform_needed(annotation: type) -> bool:
    """
    Return True if the annotation is a primitive numeric type that does not require transformation.
    """
    return annotation == float or annotation == int


def _transform_recursive(
    data: object,
    *,
    annotation: type,
    inner_type: type | None = None,
) -> object:
    """
    Recursively transforms data according to the provided type annotation, applying property aliasing and formatting as specified by metadata.
    
    This function handles complex types such as TypedDicts, dictionaries, lists, iterables, unions, and Pydantic models. It applies key renaming and value formatting based on `PropertyInfo` metadata found in `Annotated` types. For container types, it recursively transforms each element or value. For union types, it applies transformations for each subtype. If formatting is specified (e.g., ISO8601 for dates, base64 for files), it is applied to the relevant data.
    
    Parameters:
        data (object): The input data to be transformed.
        annotation (type): The type annotation describing the expected structure and metadata.
        inner_type (type | None): The element type for container types; defaults to `annotation` if not provided.
    
    Returns:
        object: The transformed data structure, with keys and values modified according to the type annotation and metadata.
    """
    if inner_type is None:
        inner_type = annotation

    stripped_type = strip_annotated_type(inner_type)
    origin = get_origin(stripped_type) or stripped_type
    if is_typeddict(stripped_type) and is_mapping(data):
        return _transform_typeddict(data, stripped_type)

    if origin == dict and is_mapping(data):
        items_type = get_args(stripped_type)[1]
        return {key: _transform_recursive(value, annotation=items_type) for key, value in data.items()}

    if (
        # List[T]
        (is_list_type(stripped_type) and is_list(data))
        # Iterable[T]
        or (is_iterable_type(stripped_type) and is_iterable(data) and not isinstance(data, str))
    ):
        # dicts are technically iterable, but it is an iterable on the keys of the dict and is not usually
        # intended as an iterable, so we don't transform it.
        if isinstance(data, dict):
            return cast(object, data)

        inner_type = extract_type_arg(stripped_type, 0)
        if _no_transform_needed(inner_type):
            # for some types there is no need to transform anything, so we can get a small
            # perf boost from skipping that work.
            #
            # but we still need to convert to a list to ensure the data is json-serializable
            if is_list(data):
                return data
            return list(data)

        return [_transform_recursive(d, annotation=annotation, inner_type=inner_type) for d in data]

    if is_union_type(stripped_type):
        # For union types we run the transformation against all subtypes to ensure that everything is transformed.
        #
        # TODO: there may be edge cases where the same normalized field name will transform to two different names
        # in different subtypes.
        for subtype in get_args(stripped_type):
            data = _transform_recursive(data, annotation=annotation, inner_type=subtype)
        return data

    if isinstance(data, pydantic.BaseModel):
        return model_dump(data, exclude_unset=True, mode="json")

    annotated_type = _get_annotated_type(annotation)
    if annotated_type is None:
        return data

    # ignore the first argument as it is the actual type
    annotations = get_args(annotated_type)[1:]
    for annotation in annotations:
        if isinstance(annotation, PropertyInfo) and annotation.format is not None:
            return _format_data(data, annotation.format, annotation.format_template)

    return data


def _format_data(data: object, format_: PropertyFormat, format_template: str | None) -> object:
    """
    Format data according to the specified property format and template.
    
    Supports formatting date and datetime objects to ISO 8601 strings or custom formats, and encoding file-like inputs as base64 strings. Returns the original data if no applicable formatting is performed.
    
    Parameters:
        data (object): The value to format, which may be a date, datetime, or file-like object.
        format_ (PropertyFormat): The desired format type ('iso8601', 'custom', or 'base64').
        format_template (str | None): Custom format string for date/time formatting, used when format_ is 'custom'.
    
    Returns:
        object: The formatted value, or the original data if no formatting was applied.
    
    Raises:
        RuntimeError: If base64 encoding is requested but the input cannot be read as bytes.
    """
    if isinstance(data, (date, datetime)):
        if format_ == "iso8601":
            return data.isoformat()

        if format_ == "custom" and format_template is not None:
            return data.strftime(format_template)

    if format_ == "base64" and is_base64_file_input(data):
        binary: str | bytes | None = None

        if isinstance(data, pathlib.Path):
            binary = data.read_bytes()
        elif isinstance(data, io.IOBase):
            binary = data.read()

            if isinstance(binary, str):  # type: ignore[unreachable]
                binary = binary.encode()

        if not isinstance(binary, bytes):
            raise RuntimeError(f"Could not read bytes from {data}; Received {type(binary)}")

        return base64.b64encode(binary).decode("ascii")

    return data


def _transform_typeddict(
    data: Mapping[str, object],
    expected_type: type,
) -> Mapping[str, object]:
    """
    Transforms a TypedDict-like mapping according to its type annotations, applying key aliasing and value transformations.
    
    Fields with a value marked as `NotGiven` are omitted. Keys are renamed if an alias is specified in their `PropertyInfo` annotation, and values are recursively transformed based on their annotated types.
    
    Parameters:
        data (Mapping[str, object]): The input mapping to transform.
        expected_type (type): The TypedDict type providing field annotations.
    
    Returns:
        Mapping[str, object]: The transformed mapping with aliased keys and processed values.
    """
    result: dict[str, object] = {}
    annotations = get_type_hints(expected_type, include_extras=True)
    for key, value in data.items():
        if not is_given(value):
            # we don't need to include `NotGiven` values here as they'll
            # be stripped out before the request is sent anyway
            continue

        type_ = annotations.get(key)
        if type_ is None:
            # we do not have a type annotation for this field, leave it as is
            result[key] = value
        else:
            result[_maybe_transform_key(key, type_)] = _transform_recursive(value, annotation=type_)
    return result


async def async_maybe_transform(
    data: object,
    expected_type: object,
) -> Any | None:
    """
    Asynchronously transforms data according to the expected type annotation, returning None if the input is None.
    
    Returns:
        The transformed data, or None if the input data is None.
    """
    if data is None:
        return None
    return await async_transform(data, expected_type)


async def async_transform(
    data: _T,
    expected_type: object,
) -> _T:
    """
    Asynchronously transforms a data structure according to the provided type annotation, applying key aliasing and value formatting based on `Annotated` metadata.
    
    Any keys or values without type information are included unchanged. Transformations such as key renaming and value formatting (e.g., date serialization, base64 encoding) are applied only when specified in the type annotation metadata.
    
    Returns:
        The transformed data structure with applied type-driven modifications.
    """
    transformed = await _async_transform_recursive(data, annotation=cast(type, expected_type))
    return cast(_T, transformed)


async def _async_transform_recursive(
    data: object,
    *,
    annotation: type,
    inner_type: type | None = None,
) -> object:
    """
    Recursively transforms data according to the provided type annotation, applying asynchronous formatting and property metadata.
    
    This function processes complex data structures (including TypedDicts, dictionaries, lists, iterables, unions, and Pydantic models) based on type annotations, especially those using `Annotated` with `PropertyInfo` metadata. It applies key aliasing, value formatting (such as date/time and base64 encoding), and recursively transforms nested elements. Asynchronous formatting is used for file-like inputs and paths.
    
    Parameters:
        data (object): The input data to be transformed.
        annotation (type): The type annotation describing the expected structure and metadata.
        inner_type (type | None): The element type for container types (e.g., the item type for lists). Defaults to the same value as `annotation`.
    
    Returns:
        object: The transformed data structure, with all applicable formatting and metadata applied.
    """
    if inner_type is None:
        inner_type = annotation

    stripped_type = strip_annotated_type(inner_type)
    origin = get_origin(stripped_type) or stripped_type
    if is_typeddict(stripped_type) and is_mapping(data):
        return await _async_transform_typeddict(data, stripped_type)

    if origin == dict and is_mapping(data):
        items_type = get_args(stripped_type)[1]
        return {key: _transform_recursive(value, annotation=items_type) for key, value in data.items()}

    if (
        # List[T]
        (is_list_type(stripped_type) and is_list(data))
        # Iterable[T]
        or (is_iterable_type(stripped_type) and is_iterable(data) and not isinstance(data, str))
    ):
        # dicts are technically iterable, but it is an iterable on the keys of the dict and is not usually
        # intended as an iterable, so we don't transform it.
        if isinstance(data, dict):
            return cast(object, data)

        inner_type = extract_type_arg(stripped_type, 0)
        if _no_transform_needed(inner_type):
            # for some types there is no need to transform anything, so we can get a small
            # perf boost from skipping that work.
            #
            # but we still need to convert to a list to ensure the data is json-serializable
            if is_list(data):
                return data
            return list(data)

        return [await _async_transform_recursive(d, annotation=annotation, inner_type=inner_type) for d in data]

    if is_union_type(stripped_type):
        # For union types we run the transformation against all subtypes to ensure that everything is transformed.
        #
        # TODO: there may be edge cases where the same normalized field name will transform to two different names
        # in different subtypes.
        for subtype in get_args(stripped_type):
            data = await _async_transform_recursive(data, annotation=annotation, inner_type=subtype)
        return data

    if isinstance(data, pydantic.BaseModel):
        return model_dump(data, exclude_unset=True, mode="json")

    annotated_type = _get_annotated_type(annotation)
    if annotated_type is None:
        return data

    # ignore the first argument as it is the actual type
    annotations = get_args(annotated_type)[1:]
    for annotation in annotations:
        if isinstance(annotation, PropertyInfo) and annotation.format is not None:
            return await _async_format_data(data, annotation.format, annotation.format_template)

    return data


async def _async_format_data(data: object, format_: PropertyFormat, format_template: str | None) -> object:
    """
    Asynchronously formats data according to the specified property format.
    
    If the format is "iso8601" and the data is a date or datetime, returns its ISO 8601 string. If the format is "custom" and a template is provided, formats the date or datetime using the template. For "base64" format and supported file-like inputs, reads the bytes (asynchronously for pathlib.Path), encodes them in base64, and returns the ASCII string. Returns the original data if no formatting applies.
    
    Returns:
        The formatted data, or the original data if no formatting was performed.
    
    Raises:
        RuntimeError: If bytes cannot be read from the provided file-like input for base64 encoding.
    """
    if isinstance(data, (date, datetime)):
        if format_ == "iso8601":
            return data.isoformat()

        if format_ == "custom" and format_template is not None:
            return data.strftime(format_template)

    if format_ == "base64" and is_base64_file_input(data):
        binary: str | bytes | None = None

        if isinstance(data, pathlib.Path):
            binary = await anyio.Path(data).read_bytes()
        elif isinstance(data, io.IOBase):
            binary = data.read()

            if isinstance(binary, str):  # type: ignore[unreachable]
                binary = binary.encode()

        if not isinstance(binary, bytes):
            raise RuntimeError(f"Could not read bytes from {data}; Received {type(binary)}")

        return base64.b64encode(binary).decode("ascii")

    return data


async def _async_transform_typeddict(
    data: Mapping[str, object],
    expected_type: type,
) -> Mapping[str, object]:
    """
    Asynchronously transforms a TypedDict-like mapping according to its type annotations, applying key aliasing and value transformations based on metadata.
    
    Fields without type annotations are left unchanged. Values marked as not given are omitted from the result.
    """
    result: dict[str, object] = {}
    annotations = get_type_hints(expected_type, include_extras=True)
    for key, value in data.items():
        if not is_given(value):
            # we don't need to include `NotGiven` values here as they'll
            # be stripped out before the request is sent anyway
            continue

        type_ = annotations.get(key)
        if type_ is None:
            # we do not have a type annotation for this field, leave it as is
            result[key] = value
        else:
            result[_maybe_transform_key(key, type_)] = await _async_transform_recursive(value, annotation=type_)
    return result


@lru_cache(maxsize=8096)
def get_type_hints(
    obj: Any,
    globalns: dict[str, Any] | None = None,
    localns: Mapping[str, Any] | None = None,
    include_extras: bool = False,
) -> dict[str, Any]:
    """
    Return type hints for the given object, optionally including extra metadata such as `Annotated` information.
    
    Parameters:
        obj: The object (typically a class or function) to inspect for type hints.
        globalns: Optional dictionary of global namespace for resolving forward references.
        localns: Optional mapping of local namespace for resolving forward references.
        include_extras: If True, includes extra type information such as `Annotated` metadata.
    
    Returns:
        A dictionary mapping attribute or parameter names to their annotated types.
    """
    return _get_type_hints(obj, globalns=globalns, localns=localns, include_extras=include_extras)
