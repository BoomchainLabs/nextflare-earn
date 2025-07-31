from __future__ import annotations

import sys
import typing
import typing_extensions
from typing import Any, TypeVar, Iterable, cast
from collections import abc as _c_abc
from typing_extensions import (
    TypeIs,
    Required,
    Annotated,
    get_args,
    get_origin,
)

from ._utils import lru_cache
from .._types import InheritsGeneric
from .._compat import is_union as _is_union


def is_annotated_type(typ: type) -> bool:
    """
    Return True if the given type is an Annotated type.
    
    Parameters:
        typ (type): The type to check.
    
    Returns:
        bool: True if typ is an Annotated type, otherwise False.
    """
    return get_origin(typ) == Annotated


def is_list_type(typ: type) -> bool:
    """
    Return True if the given type is a list or a typing.List type.
    """
    return (get_origin(typ) or typ) == list


def is_iterable_type(typ: type) -> bool:
    """
    Return True if the given type is an instance of typing.Iterable or collections.abc.Iterable.
    """
    origin = get_origin(typ) or typ
    return origin == Iterable or origin == _c_abc.Iterable


def is_union_type(typ: type) -> bool:
    """
    Return True if the given type is a union type.
    
    A union type is one created using typing.Union, the | operator (Python 3.10+), or typing_extensions.UnionType.
    """
    return _is_union(get_origin(typ))


def is_required_type(typ: type) -> bool:
    """
    Return True if the given type is a typing.Required type.
    """
    return get_origin(typ) == Required


def is_typevar(typ: type) -> bool:
    # type ignore is required because type checkers
    # think this expression will always return False
    """
    Return True if the given object is a TypeVar instance.
    
    Parameters:
    	typ (type): The object to check.
    
    Returns:
    	bool: True if typ is a TypeVar, otherwise False.
    """
    return type(typ) == TypeVar  # type: ignore


_TYPE_ALIAS_TYPES: tuple[type[typing_extensions.TypeAliasType], ...] = (typing_extensions.TypeAliasType,)
if sys.version_info >= (3, 12):
    _TYPE_ALIAS_TYPES = (*_TYPE_ALIAS_TYPES, typing.TypeAliasType)


def is_type_alias_type(tp: Any, /) -> TypeIs[typing_extensions.TypeAliasType]:
    """
    Return True if the given object is a recognized TypeAliasType instance.
    
    This includes both typing_extensions.TypeAliasType and, if available, typing.TypeAliasType from Python 3.12+.
    """
    return isinstance(tp, _TYPE_ALIAS_TYPES)


# Extracts T from Annotated[T, ...] or from Required[Annotated[T, ...]]
@lru_cache(maxsize=8096)
def strip_annotated_type(typ: type) -> type:
    """
    Recursively removes `Annotated` and `Required` wrappers from a type, returning the underlying base type.
    
    Parameters:
        typ (type): The type to process, potentially wrapped with `Annotated` or `Required`.
    
    Returns:
        type: The innermost base type with all `Annotated` and `Required` layers removed.
    """
    if is_required_type(typ) or is_annotated_type(typ):
        return strip_annotated_type(cast(type, get_args(typ)[0]))

    return typ


def extract_type_arg(typ: type, index: int) -> type:
    """
    Extracts the type argument at the specified index from a generic type.
    
    Parameters:
        typ (type): A generic type from which to extract the type argument.
        index (int): The position of the type argument to extract.
    
    Returns:
        type: The type argument at the given index.
    
    Raises:
        RuntimeError: If the type does not have a type argument at the specified index.
    """
    args = get_args(typ)
    try:
        return cast(type, args[index])
    except IndexError as err:
        raise RuntimeError(f"Expected type {typ} to have a type argument at index {index} but it did not") from err


def extract_type_var_from_base(
    typ: type,
    *,
    generic_bases: tuple[type, ...],
    index: int,
    failure_message: str | None = None,
) -> type:
    """
    Extracts the concrete type argument at the specified index from a generic base class in a given type or subclass.
    
    Given a type or subclass that inherits from one of the provided generic base classes, this function resolves and returns the type argument at the specified index. Handles direct generic types, concrete subclasses, and generic subclasses with unresolved type variables.
    
    Parameters:
        typ (type): The type or subclass to inspect.
        generic_bases (tuple[type, ...]): Tuple of generic base classes to match against.
        index (int): The index of the type argument to extract.
        failure_message (str | None): Optional custom error message if resolution fails.
    
    Returns:
        type: The resolved type argument at the specified index.
    
    Raises:
        RuntimeError: If the generic base class or type argument cannot be resolved.
    """
    cls = cast(object, get_origin(typ) or typ)
    if cls in generic_bases:  # pyright: ignore[reportUnnecessaryContains]
        # we're given the class directly
        return extract_type_arg(typ, index)

    # if a subclass is given
    # ---
    # this is needed as __orig_bases__ is not present in the typeshed stubs
    # because it is intended to be for internal use only, however there does
    # not seem to be a way to resolve generic TypeVars for inherited subclasses
    # without using it.
    if isinstance(cls, InheritsGeneric):
        target_base_class: Any | None = None
        for base in cls.__orig_bases__:
            if base.__origin__ in generic_bases:
                target_base_class = base
                break

        if target_base_class is None:
            raise RuntimeError(
                "Could not find the generic base class;\n"
                "This should never happen;\n"
                f"Does {cls} inherit from one of {generic_bases} ?"
            )

        extracted = extract_type_arg(target_base_class, index)
        if is_typevar(extracted):
            # If the extracted type argument is itself a type variable
            # then that means the subclass itself is generic, so we have
            # to resolve the type argument from the class itself, not
            # the base class.
            #
            # Note: if there is more than 1 type argument, the subclass could
            # change the ordering of the type arguments, this is not currently
            # supported.
            return extract_type_arg(typ, index)

        return extracted

    raise RuntimeError(failure_message or f"Could not resolve inner type variable at index {index} for {typ}")
