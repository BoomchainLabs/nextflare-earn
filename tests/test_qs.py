from typing import Any, cast
from functools import partial
from urllib.parse import unquote

import pytest

from earn_app._qs import Querystring, stringify


def test_empty() -> None:
    """
    Test that empty dictionaries and nested empty dictionaries serialize to an empty query string.
    """
    assert stringify({}) == ""
    assert stringify({"a": {}}) == ""
    assert stringify({"a": {"b": {"c": {}}}}) == ""


def test_basic() -> None:
    """
    Test that basic key-value pairs are serialized correctly by the stringify function.
    
    Verifies correct serialization of integers, strings, booleans, floats, and None values, ensuring that None values serialize to an empty string.
    """
    assert stringify({"a": 1}) == "a=1"
    assert stringify({"a": "b"}) == "a=b"
    assert stringify({"a": True}) == "a=true"
    assert stringify({"a": False}) == "a=false"
    assert stringify({"a": 1.23456}) == "a=1.23456"
    assert stringify({"a": None}) == ""


@pytest.mark.parametrize("method", ["class", "function"])
def test_nested_dotted(method: str) -> None:
    """
    Test that nested dictionaries are serialized using dot notation for keys when `nested_format="dots"` is specified.
    
    Parameters:
        method (str): Specifies whether to use the class-based or function-based serialization method.
    """
    if method == "class":
        serialise = Querystring(nested_format="dots").stringify
    else:
        serialise = partial(stringify, nested_format="dots")

    assert unquote(serialise({"a": {"b": "c"}})) == "a.b=c"
    assert unquote(serialise({"a": {"b": "c", "d": "e", "f": "g"}})) == "a.b=c&a.d=e&a.f=g"
    assert unquote(serialise({"a": {"b": {"c": {"d": "e"}}}})) == "a.b.c.d=e"
    assert unquote(serialise({"a": {"b": True}})) == "a.b=true"


def test_nested_brackets() -> None:
    """
    Test that nested dictionaries are serialized using bracket notation.
    
    Verifies that the `stringify` function produces correct bracketed query string keys for nested dictionaries, including multiple keys and boolean values.
    """
    assert unquote(stringify({"a": {"b": "c"}})) == "a[b]=c"
    assert unquote(stringify({"a": {"b": "c", "d": "e", "f": "g"}})) == "a[b]=c&a[d]=e&a[f]=g"
    assert unquote(stringify({"a": {"b": {"c": {"d": "e"}}}})) == "a[b][c][d]=e"
    assert unquote(stringify({"a": {"b": True}})) == "a[b]=true"


@pytest.mark.parametrize("method", ["class", "function"])
def test_array_comma(method: str) -> None:
    """
    Test that lists are serialized as comma-separated values in query strings when using the 'comma' array format.
    
    Parameters:
        method (str): Specifies whether to use the class-based or function-based serialization method.
    """
    if method == "class":
        serialise = Querystring(array_format="comma").stringify
    else:
        serialise = partial(stringify, array_format="comma")

    assert unquote(serialise({"in": ["foo", "bar"]})) == "in=foo,bar"
    assert unquote(serialise({"a": {"b": [True, False]}})) == "a[b]=true,false"
    assert unquote(serialise({"a": {"b": [True, False, None, True]}})) == "a[b]=true,false,true"


def test_array_repeat() -> None:
    """
    Test that lists are serialized as repeated key-value pairs in query strings, including nested lists and omission of None values.
    """
    assert unquote(stringify({"in": ["foo", "bar"]})) == "in=foo&in=bar"
    assert unquote(stringify({"a": {"b": [True, False]}})) == "a[b]=true&a[b]=false"
    assert unquote(stringify({"a": {"b": [True, False, None, True]}})) == "a[b]=true&a[b]=false&a[b]=true"
    assert unquote(stringify({"in": ["foo", {"b": {"c": ["d", "e"]}}]})) == "in=foo&in[b][c]=d&in[b][c]=e"


@pytest.mark.parametrize("method", ["class", "function"])
def test_array_brackets(method: str) -> None:
    """
    Test that lists are serialized as bracketed keys (e.g., `key[]=value`) when using the 'brackets' array format.
    
    Verifies correct serialization for top-level and nested lists, including omission of None values and proper boolean value formatting.
    """
    if method == "class":
        serialise = Querystring(array_format="brackets").stringify
    else:
        serialise = partial(stringify, array_format="brackets")

    assert unquote(serialise({"in": ["foo", "bar"]})) == "in[]=foo&in[]=bar"
    assert unquote(serialise({"a": {"b": [True, False]}})) == "a[b][]=true&a[b][]=false"
    assert unquote(serialise({"a": {"b": [True, False, None, True]}})) == "a[b][]=true&a[b][]=false&a[b][]=true"


def test_unknown_array_format() -> None:
    with pytest.raises(NotImplementedError, match="Unknown array_format value: foo, choose from comma, repeat"):
        stringify({"a": ["foo", "bar"]}, array_format=cast(Any, "foo"))
