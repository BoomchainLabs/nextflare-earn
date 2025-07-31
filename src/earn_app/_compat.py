from __future__ import annotations

from typing import TYPE_CHECKING, Any, Union, Generic, TypeVar, Callable, cast, overload
from datetime import date, datetime
from typing_extensions import Self, Literal

import pydantic
from pydantic.fields import FieldInfo

from ._types import IncEx, StrBytesIntFloat

_T = TypeVar("_T")
_ModelT = TypeVar("_ModelT", bound=pydantic.BaseModel)

# --------------- Pydantic v2 compatibility ---------------

# Pyright incorrectly reports some of our functions as overriding a method when they don't
# pyright: reportIncompatibleMethodOverride=false

PYDANTIC_V2 = pydantic.VERSION.startswith("2.")

# v1 re-exports
if TYPE_CHECKING:

    def parse_date(value: date | StrBytesIntFloat) -> date:  # noqa: ARG001
        """
        Parse a value into a `date` object using Pydantic's date parsing logic.
        
        Parameters:
            value (date | str | bytes | int | float): The value to parse as a date.
        
        Returns:
            date: The parsed date object.
        """
        ...

    def parse_datetime(value: Union[datetime, StrBytesIntFloat]) -> datetime:  # noqa: ARG001
        """
        Parse a value into a `datetime` object using Pydantic's parsing logic.
        
        Parameters:
            value: A `datetime` object or a value that can be parsed into a `datetime` (such as a string, bytes, int, or float).
        
        Returns:
            A `datetime` object representing the parsed value.
        """
        ...

    def get_args(t: type[Any]) -> tuple[Any, ...]:  # noqa: ARG001
        """
        Return the type arguments of a generic type annotation.
        
        Parameters:
            t: The generic type or annotated type to inspect.
        
        Returns:
            A tuple containing the type arguments of the provided type, or an empty tuple if none are present.
        """
        ...

    def is_union(tp: type[Any] | None) -> bool:  # noqa: ARG001
        """
        Return True if the given type annotation represents a union type.
        
        Parameters:
            tp (type | None): The type annotation to check.
        
        Returns:
            bool: True if the type is a union, otherwise False.
        """
        ...

    def get_origin(t: type[Any]) -> type[Any] | None:  # noqa: ARG001
        """
        Return the unsubscripted base type of a generic or annotated type.
        
        Parameters:
            t (type[Any]): The type to inspect.
        
        Returns:
            type[Any] | None: The origin type if available, otherwise None.
        """
        ...

    def is_literal_type(type_: type[Any]) -> bool:  # noqa: ARG001
        """
        Return True if the given type is a typing.Literal type.
        
        Parameters:
            type_ (type): The type to check.
        
        Returns:
            bool: True if the type is a Literal, otherwise False.
        """
        ...

    def is_typeddict(type_: type[Any]) -> bool:  # noqa: ARG001
        """
        Return True if the given type is a TypedDict, otherwise False.
        
        Parameters:
            type_ (type[Any]): The type to check.
        
        Returns:
            bool: True if the type is a TypedDict, False otherwise.
        """
        ...

else:
    if PYDANTIC_V2:
        from pydantic.v1.typing import (
            get_args as get_args,
            is_union as is_union,
            get_origin as get_origin,
            is_typeddict as is_typeddict,
            is_literal_type as is_literal_type,
        )
        from pydantic.v1.datetime_parse import parse_date as parse_date, parse_datetime as parse_datetime
    else:
        from pydantic.typing import (
            get_args as get_args,
            is_union as is_union,
            get_origin as get_origin,
            is_typeddict as is_typeddict,
            is_literal_type as is_literal_type,
        )
        from pydantic.datetime_parse import parse_date as parse_date, parse_datetime as parse_datetime


# refactored config
if TYPE_CHECKING:
    from pydantic import ConfigDict as ConfigDict
else:
    if PYDANTIC_V2:
        from pydantic import ConfigDict
    else:
        # TODO: provide an error message here?
        ConfigDict = None


# renamed methods / properties
def parse_obj(model: type[_ModelT], value: object) -> _ModelT:
    """
    Parse an object into a Pydantic model instance, supporting both Pydantic v1 and v2.
    
    Parameters:
        model: The Pydantic model class to instantiate.
        value: The object to parse into the model.
    
    Returns:
        An instance of the specified Pydantic model populated with data from the input object.
    """
    if PYDANTIC_V2:
        return model.model_validate(value)
    else:
        return cast(_ModelT, model.parse_obj(value))  # pyright: ignore[reportDeprecated, reportUnnecessaryCast]


def field_is_required(field: FieldInfo) -> bool:
    """
    Return whether a Pydantic field is required, abstracting over Pydantic v1 and v2 differences.
    
    Parameters:
        field (FieldInfo): The Pydantic field to check.
    
    Returns:
        bool: True if the field is required, False otherwise.
    """
    if PYDANTIC_V2:
        return field.is_required()
    return field.required  # type: ignore


def field_get_default(field: FieldInfo) -> Any:
    """
    Return the default value for a Pydantic field, or None if the field is undefined in Pydantic v2.
    
    Parameters:
        field (FieldInfo): The Pydantic field to inspect.
    
    Returns:
        Any: The default value of the field, or None if no default is set (in Pydantic v2).
    """
    value = field.get_default()
    if PYDANTIC_V2:
        from pydantic_core import PydanticUndefined

        if value == PydanticUndefined:
            return None
        return value
    return value


def field_outer_type(field: FieldInfo) -> Any:
    """
    Return the declared type annotation of a Pydantic model field, abstracting differences between Pydantic v1 and v2.
    """
    if PYDANTIC_V2:
        return field.annotation
    return field.outer_type_  # type: ignore


def get_model_config(model: type[pydantic.BaseModel]) -> Any:
    """
    Return the configuration object for a Pydantic model class, abstracting differences between Pydantic v1 and v2.
    """
    if PYDANTIC_V2:
        return model.model_config
    return model.__config__  # type: ignore


def get_model_fields(model: type[pydantic.BaseModel]) -> dict[str, FieldInfo]:
    """
    Return the fields dictionary of a Pydantic model class, abstracting differences between Pydantic v1 and v2.
    
    Parameters:
        model (type[pydantic.BaseModel]): The Pydantic model class.
    
    Returns:
        dict[str, FieldInfo]: A mapping of field names to field information objects.
    """
    if PYDANTIC_V2:
        return model.model_fields
    return model.__fields__  # type: ignore


def model_copy(model: _ModelT, *, deep: bool = False) -> _ModelT:
    """
    Return a copy of a Pydantic model instance, optionally performing a deep copy.
    
    Parameters:
        deep (bool): If True, performs a deep copy of the model and its fields. Defaults to False.
    
    Returns:
        A new instance of the model, copied from the original.
    """
    if PYDANTIC_V2:
        return model.model_copy(deep=deep)
    return model.copy(deep=deep)  # type: ignore


def model_json(model: pydantic.BaseModel, *, indent: int | None = None) -> str:
    """
    Serialize a Pydantic model instance to a JSON string.
    
    Parameters:
        indent (int | None): Number of spaces for indentation in the output JSON string, or None for compact output.
    
    Returns:
        str: The JSON representation of the model.
    """
    if PYDANTIC_V2:
        return model.model_dump_json(indent=indent)
    return model.json(indent=indent)  # type: ignore


def model_dump(
    model: pydantic.BaseModel,
    *,
    exclude: IncEx | None = None,
    exclude_unset: bool = False,
    exclude_defaults: bool = False,
    warnings: bool = True,
    mode: Literal["json", "python"] = "python",
) -> dict[str, Any]:
    """
    Return a dictionary representation of a Pydantic model, abstracting differences between Pydantic v1 and v2.
    
    Parameters:
        exclude: Fields to exclude from the output.
        exclude_unset: If True, exclude fields that were not set.
        exclude_defaults: If True, exclude fields with default values.
        warnings: If True and supported, emit warnings for serialization issues.
        mode: Output mode, either "python" or "json".
    
    Returns:
        A dictionary containing the model's data, with exclusions and formatting applied as specified.
    """
    if PYDANTIC_V2 or hasattr(model, "model_dump"):
        return model.model_dump(
            mode=mode,
            exclude=exclude,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            # warnings are not supported in Pydantic v1
            warnings=warnings if PYDANTIC_V2 else True,
        )
    return cast(
        "dict[str, Any]",
        model.dict(  # pyright: ignore[reportDeprecated, reportUnnecessaryCast]
            exclude=exclude,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
        ),
    )


def model_parse(model: type[_ModelT], data: Any) -> _ModelT:
    """
    Parse input data into a Pydantic model instance, supporting both Pydantic v1 and v2.
    
    Parameters:
        model: The Pydantic model class to instantiate.
        data: The input data to parse into the model.
    
    Returns:
        An instance of the specified Pydantic model populated with the parsed data.
    """
    if PYDANTIC_V2:
        return model.model_validate(data)
    return model.parse_obj(data)  # pyright: ignore[reportDeprecated]


# generic models
if TYPE_CHECKING:

    class GenericModel(pydantic.BaseModel): ...

else:
    if PYDANTIC_V2:
        # there no longer needs to be a distinction in v2 but
        # we still have to create our own subclass to avoid
        # inconsistent MRO ordering errors
        class GenericModel(pydantic.BaseModel): ...

    else:
        import pydantic.generics

        class GenericModel(pydantic.generics.GenericModel, pydantic.BaseModel): ...


# cached properties
if TYPE_CHECKING:
    cached_property = property

    # we define a separate type (copied from typeshed)
    # that represents that `cached_property` is `set`able
    # at runtime, which differs from `@property`.
    #
    # this is a separate type as editors likely special case
    # `@property` and we don't want to cause issues just to have
    # more helpful internal types.

    class typed_cached_property(Generic[_T]):
        func: Callable[[Any], _T]
        attrname: str | None

        def __init__(self, func: Callable[[Any], _T]) -> None: """
Initialize the typed cached property with the provided function.

Parameters:
    func (Callable[[Any], _T]): The function whose result will be cached as a property.
"""
...

        @overload
        def __get__(self, instance: None, owner: type[Any] | None = None) -> Self: """
Return the cached property descriptor itself when accessed from the class, enabling introspection and correct descriptor protocol behavior.
"""
...

        @overload
        def __get__(self, instance: object, owner: type[Any] | None = None) -> _T: """
Retrieve the cached value from the instance, computing and storing it if not already cached.

Returns:
    The cached property value.
"""
...

        def __get__(self, instance: object, owner: type[Any] | None = None) -> _T | Self:
            """
            Raise NotImplementedError when attempting to access the property.
            
            Intended as a placeholder for subclasses to implement property retrieval logic.
            """
            raise NotImplementedError()

        def __set_name__(self, owner: type[Any], name: str) -> None: """
Set the name of the cached property when assigned to a class attribute.

This method is called automatically by Python during class creation.
"""
...

        # __set__ is not defined at runtime, but @cached_property is designed to be settable
        def __set__(self, instance: object, value: _T) -> None: """
Set the cached property value on the given instance.

This assigns the provided value directly to the instance's attribute corresponding to the cached property.
"""
...
else:
    from functools import cached_property as cached_property

    typed_cached_property = cached_property
