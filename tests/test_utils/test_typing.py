from __future__ import annotations

from typing import Generic, TypeVar, cast

from earn_app._utils import extract_type_var_from_base

_T = TypeVar("_T")
_T2 = TypeVar("_T2")
_T3 = TypeVar("_T3")


class BaseGeneric(Generic[_T]): ...


class SubclassGeneric(BaseGeneric[_T]): ...


class BaseGenericMultipleTypeArgs(Generic[_T, _T2, _T3]): ...


class SubclassGenericMultipleTypeArgs(BaseGenericMultipleTypeArgs[_T, _T2, _T3]): ...


class SubclassDifferentOrderGenericMultipleTypeArgs(BaseGenericMultipleTypeArgs[_T2, _T, _T3]): ...


def test_extract_type_var() -> None:
    assert (
        extract_type_var_from_base(
            BaseGeneric[int],
            index=0,
            generic_bases=cast("tuple[type, ...]", (BaseGeneric,)),
        )
        == int
    )


def test_extract_type_var_generic_subclass() -> None:
    assert (
        extract_type_var_from_base(
            SubclassGeneric[int],
            index=0,
            generic_bases=cast("tuple[type, ...]", (BaseGeneric,)),
        )
        == int
    )


def test_extract_type_var_multiple() -> None:
    """
    Test extraction of each type argument from a generic class with multiple type variables.
    
    Verifies that `extract_type_var_from_base` correctly retrieves the first, second, and third type arguments from an instantiation of `BaseGenericMultipleTypeArgs` with concrete types.
    """
    typ = BaseGenericMultipleTypeArgs[int, str, None]

    generic_bases = cast("tuple[type, ...]", (BaseGenericMultipleTypeArgs,))
    assert extract_type_var_from_base(typ, index=0, generic_bases=generic_bases) == int
    assert extract_type_var_from_base(typ, index=1, generic_bases=generic_bases) == str
    assert extract_type_var_from_base(typ, index=2, generic_bases=generic_bases) == type(None)


def test_extract_type_var_generic_subclass_multiple() -> None:
    """
    Test extracting each type argument from a subclass of a generic base class with multiple type variables.
    
    Verifies that `extract_type_var_from_base` correctly retrieves the concrete types for all type arguments from `SubclassGenericMultipleTypeArgs` when instantiated with specific types.
    """
    typ = SubclassGenericMultipleTypeArgs[int, str, None]

    generic_bases = cast("tuple[type, ...]", (BaseGenericMultipleTypeArgs,))
    assert extract_type_var_from_base(typ, index=0, generic_bases=generic_bases) == int
    assert extract_type_var_from_base(typ, index=1, generic_bases=generic_bases) == str
    assert extract_type_var_from_base(typ, index=2, generic_bases=generic_bases) == type(None)


def test_extract_type_var_generic_subclass_different_ordering_multiple() -> None:
    """
    Test extraction of type arguments from a subclass with reordered type variables.
    
    Verifies that `extract_type_var_from_base` correctly identifies the concrete types for each type variable index when the subclass reorders the type variables of its generic base class.
    """
    typ = SubclassDifferentOrderGenericMultipleTypeArgs[int, str, None]

    generic_bases = cast("tuple[type, ...]", (BaseGenericMultipleTypeArgs,))
    assert extract_type_var_from_base(typ, index=0, generic_bases=generic_bases) == int
    assert extract_type_var_from_base(typ, index=1, generic_bases=generic_bases) == str
    assert extract_type_var_from_base(typ, index=2, generic_bases=generic_bases) == type(None)
