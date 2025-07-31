from __future__ import annotations

import os
import inspect
import traceback
import contextlib
from typing import Any, TypeVar, Iterator, cast
from datetime import date, datetime
from typing_extensions import Literal, get_args, get_origin, assert_type

from earn_app._types import Omit, NoneType
from earn_app._utils import (
    is_dict,
    is_list,
    is_list_type,
    is_union_type,
    extract_type_arg,
    is_annotated_type,
    is_type_alias_type,
)
from earn_app._compat import PYDANTIC_V2, field_outer_type, get_model_fields
from earn_app._models import BaseModel

BaseModelT = TypeVar("BaseModelT", bound=BaseModel)


def assert_matches_model(model: type[BaseModelT], value: BaseModelT, *, path: list[str]) -> bool:
    """
    Validates that a Pydantic model instance matches the expected model type by recursively asserting each field's value against its declared type.
    
    Parameters:
        model: The expected Pydantic model class.
        value: The model instance to validate.
        path: The hierarchical path used for error reporting.
    
    Returns:
        True if all fields in the model instance conform to their declared types.
    """
    for name, field in get_model_fields(model).items():
        field_value = getattr(value, name)
        if PYDANTIC_V2:
            allow_none = False
        else:
            # in v1 nullability was structured differently
            # https://docs.pydantic.dev/2.0/migration/#required-optional-and-nullable-fields
            allow_none = getattr(field, "allow_none", False)

        assert_matches_type(
            field_outer_type(field),
            field_value,
            path=[*path, name],
            allow_none=allow_none,
        )

    return True


# Note: the `path` argument is only used to improve error messages when `--showlocals` is used
def assert_matches_type(
    type_: Any,
    value: object,
    *,
    path: list[str],
    allow_none: bool = False,
) -> None:
    """
    Recursively asserts that a value matches a specified type annotation at runtime.
    
    Supports primitive types, collections, unions, literals, datetime types, and Pydantic BaseModel subclasses. Raises an AssertionError if the value does not conform to the provided type, including nested and complex type structures.
    
    Parameters:
        type_ (Any): The type annotation to check against.
        value (object): The value to validate.
        path (list[str]): The path to the current value within the data structure, used for error context.
        allow_none (bool): If True, allows the value to be None regardless of the type annotation.
    """
    if is_type_alias_type(type_):
        type_ = type_.__value__

    # unwrap `Annotated[T, ...]` -> `T`
    if is_annotated_type(type_):
        type_ = extract_type_arg(type_, 0)

    if allow_none and value is None:
        return

    if type_ is None or type_ is NoneType:
        assert value is None
        return

    origin = get_origin(type_) or type_

    if is_list_type(type_):
        return _assert_list_type(type_, value)

    if origin == str:
        assert isinstance(value, str)
    elif origin == int:
        assert isinstance(value, int)
    elif origin == bool:
        assert isinstance(value, bool)
    elif origin == float:
        assert isinstance(value, float)
    elif origin == bytes:
        assert isinstance(value, bytes)
    elif origin == datetime:
        assert isinstance(value, datetime)
    elif origin == date:
        assert isinstance(value, date)
    elif origin == object:
        # nothing to do here, the expected type is unknown
        pass
    elif origin == Literal:
        assert value in get_args(type_)
    elif origin == dict:
        assert is_dict(value)

        args = get_args(type_)
        key_type = args[0]
        items_type = args[1]

        for key, item in value.items():
            assert_matches_type(key_type, key, path=[*path, "<dict key>"])
            assert_matches_type(items_type, item, path=[*path, "<dict item>"])
    elif is_union_type(type_):
        variants = get_args(type_)

        try:
            none_index = variants.index(type(None))
        except ValueError:
            pass
        else:
            # special case Optional[T] for better error messages
            if len(variants) == 2:
                if value is None:
                    # valid
                    return

                return assert_matches_type(type_=variants[not none_index], value=value, path=path)

        for i, variant in enumerate(variants):
            try:
                assert_matches_type(variant, value, path=[*path, f"variant {i}"])
                return
            except AssertionError:
                traceback.print_exc()
                continue

        raise AssertionError("Did not match any variants")
    elif issubclass(origin, BaseModel):
        assert isinstance(value, type_)
        assert assert_matches_model(type_, cast(Any, value), path=path)
    elif inspect.isclass(origin) and origin.__name__ == "HttpxBinaryResponseContent":
        assert value.__class__.__name__ == "HttpxBinaryResponseContent"
    else:
        assert None, f"Unhandled field type: {type_}"


def _assert_list_type(type_: type[object], value: object) -> None:
    """
    Assert that all elements in a list match the specified inner type.
    
    Raises an AssertionError if the value is not a list or if any element does not match the expected type.
    """
    assert is_list(value)

    inner_type = get_args(type_)[0]
    for entry in value:
        assert_type(inner_type, entry)  # type: ignore


@contextlib.contextmanager
def update_env(**new_env: str | Omit) -> Iterator[None]:
    """
    Temporarily updates environment variables within a context, restoring the original environment afterward.
    
    Parameters:
        **new_env: Environment variable names and their new values. If a value is an instance of Omit, the variable is removed for the duration of the context.
    
    Yields:
        None: Control is yielded to the context block with the updated environment.
    """
    old = os.environ.copy()

    try:
        for name, value in new_env.items():
            if isinstance(value, Omit):
                os.environ.pop(name, None)
            else:
                os.environ[name] = value

        yield None
    finally:
        os.environ.clear()
        os.environ.update(old)
