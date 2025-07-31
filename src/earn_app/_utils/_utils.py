from __future__ import annotations

import os
import re
import inspect
import functools
from typing import (
    Any,
    Tuple,
    Mapping,
    TypeVar,
    Callable,
    Iterable,
    Sequence,
    cast,
    overload,
)
from pathlib import Path
from datetime import date, datetime
from typing_extensions import TypeGuard

import sniffio

from .._types import NotGiven, FileTypes, NotGivenOr, HeadersLike
from .._compat import parse_date as parse_date, parse_datetime as parse_datetime

_T = TypeVar("_T")
_TupleT = TypeVar("_TupleT", bound=Tuple[object, ...])
_MappingT = TypeVar("_MappingT", bound=Mapping[str, object])
_SequenceT = TypeVar("_SequenceT", bound=Sequence[object])
CallableT = TypeVar("CallableT", bound=Callable[..., Any])


def flatten(t: Iterable[Iterable[_T]]) -> list[_T]:
    """
    Flatten a nested iterable of iterables into a single list.
    
    Parameters:
        t (Iterable[Iterable[_T]]): An iterable containing other iterables.
    
    Returns:
        list[_T]: A flat list containing all items from the nested iterables, in order.
    """
    return [item for sublist in t for item in sublist]


def extract_files(
    # TODO: this needs to take Dict but variance issues.....
    # create protocol type ?
    query: Mapping[str, object],
    *,
    paths: Sequence[Sequence[str]],
) -> list[tuple[str, FileTypes]]:
    """
    Recursively extracts file-like objects from a nested mapping along specified paths.
    
    Each path is a sequence of keys (with "<array>" indicating traversal of all items in a list) describing where to find files within the nested structure. Extracted files are returned as a list of tuples containing a flattened key and the file object. The input mapping is mutated by removing the extracted file entries.
    
    Parameters:
        query (Mapping[str, object]): The nested mapping to extract files from.
        paths (Sequence[Sequence[str]]): Paths specifying where to look for files.
    
    Returns:
        list[tuple[str, FileTypes]]: A list of (flattened key, file object) tuples for each extracted file.
    """
    files: list[tuple[str, FileTypes]] = []
    for path in paths:
        files.extend(_extract_items(query, path, index=0, flattened_key=None))
    return files


def _extract_items(
    obj: object,
    path: Sequence[str],
    *,
    index: int,
    flattened_key: str | None,
) -> list[tuple[str, FileTypes]]:
    """
    Recursively traverses an object along a specified path to extract file-like items, returning a list of (flattened key, file content) tuples.
    
    This function supports traversal through nested dictionaries and lists, handling special "<array>" path segments for arrays. If the path is exhausted, it validates and collects file content at the current location. Keys are flattened to represent the traversal path. If a path segment is missing or the object type does not match the expected structure, an empty list is returned.
    try:
        key = path[index]
    except IndexError:
        if isinstance(obj, NotGiven):
            # no value was provided - we can safely ignore
            return []

        # cyclical import
        from .._files import assert_is_file_content

        # We have exhausted the path, return the entry we found.
        assert flattened_key is not None

        if is_list(obj):
            files: list[tuple[str, FileTypes]] = []
            for entry in obj:
                assert_is_file_content(entry, key=flattened_key + "[]" if flattened_key else "")
                files.append((flattened_key + "[]", cast(FileTypes, entry)))
            return files

        assert_is_file_content(obj, key=flattened_key)
        return [(flattened_key, cast(FileTypes, obj))]

    index += 1
    if is_dict(obj):
        try:
            # We are at the last entry in the path so we must remove the field
            if (len(path)) == index:
                item = obj.pop(key)
            else:
                item = obj[key]
        except KeyError:
            # Key was not present in the dictionary, this is not indicative of an error
            # as the given path may not point to a required field. We also do not want
            # to enforce required fields as the API may differ from the spec in some cases.
            return []
        if flattened_key is None:
            flattened_key = key
        else:
            flattened_key += f"[{key}]"
        return _extract_items(
            item,
            path,
            index=index,
            flattened_key=flattened_key,
        )
    elif is_list(obj):
        if key != "<array>":
            return []

        return flatten(
            [
                _extract_items(
                    item,
                    path,
                    index=index,
                    flattened_key=flattened_key + "[]" if flattened_key is not None else "[]",
                )
                for item in obj
            ]
        )

    # Something unexpected was passed, just ignore it.
    return []


def is_given(obj: NotGivenOr[_T]) -> TypeGuard[_T]:
    """
    Return True if the object is not an instance of NotGiven, narrowing its type.
    
    This type guard is used to distinguish values that are not the NotGiven sentinel.
    """
    return not isinstance(obj, NotGiven)


# Type safe methods for narrowing types with TypeVars.
# The default narrowing for isinstance(obj, dict) is dict[unknown, unknown],
# however this cause Pyright to rightfully report errors. As we know we don't
# care about the contained types we can safely use `object` in it's place.
#
# There are two separate functions defined, `is_*` and `is_*_t` for different use cases.
# `is_*` is for when you're dealing with an unknown input
# `is_*_t` is for when you're narrowing a known union type to a specific subset


def is_tuple(obj: object) -> TypeGuard[tuple[object, ...]]:
    """
    Return True if the object is a tuple, for type narrowing purposes.
    
    Returns:
        TypeGuard[tuple[object, ...]]: True if the object is a tuple, otherwise False.
    """
    return isinstance(obj, tuple)


def is_tuple_t(obj: _TupleT | object) -> TypeGuard[_TupleT]:
    """
    Type guard that narrows an object to a specific tuple type.
    
    Returns:
        True if the object is an instance of tuple, allowing type narrowing to _TupleT.
    """
    return isinstance(obj, tuple)


def is_sequence(obj: object) -> TypeGuard[Sequence[object]]:
    """
    Determine whether the given object is a sequence (excluding strings and bytes).
    
    Returns:
        True if the object is an instance of collections.abc.Sequence; otherwise, False.
    """
    return isinstance(obj, Sequence)


def is_sequence_t(obj: _SequenceT | object) -> TypeGuard[_SequenceT]:
    """
    Type guard that checks if the object is an instance of `Sequence`, narrowing to the specific sequence type `_SequenceT`.
    
    Returns:
        True if `obj` is a `Sequence`, otherwise False.
    """
    return isinstance(obj, Sequence)


def is_mapping(obj: object) -> TypeGuard[Mapping[str, object]]:
    """
    Determine if the given object is a mapping with string keys.
    
    Returns:
        TypeGuard[Mapping[str, object]]: True if the object is a mapping (e.g., dict) with string keys, otherwise False.
    """
    return isinstance(obj, Mapping)


def is_mapping_t(obj: _MappingT | object) -> TypeGuard[_MappingT]:
    """
    Type guard that checks if the object is an instance of Mapping, narrowing to the specific mapping type.
    
    Returns:
        True if the object is a Mapping, otherwise False.
    """
    return isinstance(obj, Mapping)


def is_dict(obj: object) -> TypeGuard[dict[object, object]]:
    """
    Check if the given object is a dictionary.
    
    Returns:
        TypeGuard[dict[object, object]]: True if the object is a dictionary, otherwise False.
    """
    return isinstance(obj, dict)


def is_list(obj: object) -> TypeGuard[list[object]]:
    """
    Determine whether the given object is a list.
    
    Returns:
        TypeGuard[list[object]]: True if the object is a list, otherwise False.
    """
    return isinstance(obj, list)


def is_iterable(obj: object) -> TypeGuard[Iterable[object]]:
    """
    Return True if the object is an iterable, excluding strings and bytes.
    
    Parameters:
        obj (object): The object to check.
    
    Returns:
        TypeGuard[Iterable[object]]: True if the object is an iterable, otherwise False.
    """
    return isinstance(obj, Iterable)


def deepcopy_minimal(item: _T) -> _T:
    """
    Recursively creates a shallow copy of mappings and lists, leaving other objects unchanged.
    
    Only mappings (such as dict) and lists are copied recursively; all other types are returned as-is for performance optimization.
    """
    if is_mapping(item):
        return cast(_T, {k: deepcopy_minimal(v) for k, v in item.items()})
    if is_list(item):
        return cast(_T, [deepcopy_minimal(entry) for entry in item])
    return item


# copied from https://github.com/Rapptz/RoboDanny
def human_join(seq: Sequence[str], *, delim: str = ", ", final: str = "or") -> str:
    """
    Join a sequence of strings into a human-readable list with a final conjunction.
    
    Parameters:
        seq (Sequence[str]): The sequence of strings to join.
        delim (str, optional): Delimiter to use between elements except the last. Defaults to ", ".
        final (str, optional): Conjunction to use before the last element. Defaults to "or".
    
    Returns:
        str: A human-readable string combining the sequence elements.
    """
    size = len(seq)
    if size == 0:
        return ""

    if size == 1:
        return seq[0]

    if size == 2:
        return f"{seq[0]} {final} {seq[1]}"

    return delim.join(seq[:-1]) + f" {final} {seq[-1]}"


def quote(string: str) -> str:
    """
    Wraps the input string in single quotes without escaping any characters.
    
    Parameters:
        string (str): The string to be wrapped.
    
    Returns:
        str: The input string surrounded by single quotes.
    """
    return f"'{string}'"


def required_args(*variants: Sequence[str]) -> Callable[[CallableT], CallableT]:
    """
    Decorator that enforces that at least one specified set of required arguments is provided to the decorated function.
    
    This is useful for runtime validation of overloaded functions, ensuring that the function is called with arguments matching at least one of the provided variants. If none of the variants are satisfied, a `TypeError` is raised with a descriptive message.
    
    Parameters:
        *variants (Sequence[str]): Each variant is a sequence of argument names; at least one variant must be fully satisfied by the function call.
    
    Returns:
        Callable: A decorator that applies the argument validation to the target function.
    """

    def inner(func: CallableT) -> CallableT:
        """
        Decorator inner function that enforces required argument variants for the decorated function.
        
        Checks that at least one specified set of required arguments is present in the call, raising a TypeError with a descriptive message if not. Used internally by the `required_args` decorator.
        """
        params = inspect.signature(func).parameters
        positional = [
            name
            for name, param in params.items()
            if param.kind
            in {
                param.POSITIONAL_ONLY,
                param.POSITIONAL_OR_KEYWORD,
            }
        ]

        @functools.wraps(func)
        def wrapper(*args: object, **kwargs: object) -> object:
            """
            Validates that at least one required argument variant is present before calling the wrapped function.
            
            Raises:
                TypeError: If none of the specified argument variants are fully provided.
            """
            given_params: set[str] = set()
            for i, _ in enumerate(args):
                try:
                    given_params.add(positional[i])
                except IndexError:
                    raise TypeError(
                        f"{func.__name__}() takes {len(positional)} argument(s) but {len(args)} were given"
                    ) from None

            for key in kwargs.keys():
                given_params.add(key)

            for variant in variants:
                matches = all((param in given_params for param in variant))
                if matches:
                    break
            else:  # no break
                if len(variants) > 1:
                    variations = human_join(
                        ["(" + human_join([quote(arg) for arg in variant], final="and") + ")" for variant in variants]
                    )
                    msg = f"Missing required arguments; Expected either {variations} arguments to be given"
                else:
                    assert len(variants) > 0

                    # TODO: this error message is not deterministic
                    missing = list(set(variants[0]) - given_params)
                    if len(missing) > 1:
                        msg = f"Missing required arguments: {human_join([quote(arg) for arg in missing])}"
                    else:
                        msg = f"Missing required argument: {quote(missing[0])}"
                raise TypeError(msg)
            return func(*args, **kwargs)

        return wrapper  # type: ignore

    return inner


_K = TypeVar("_K")
_V = TypeVar("_V")


@overload
def strip_not_given(obj: None) -> None: """
Returns None when the input object is None.
"""
...


@overload
def strip_not_given(obj: Mapping[_K, _V | NotGiven]) -> dict[_K, _V]: """
Return a new dictionary with keys removed where the value is an instance of NotGiven.

Parameters:
	obj (Mapping[_K, _V | NotGiven]): Input mapping potentially containing NotGiven values.

Returns:
	dict[_K, _V]: Dictionary with all NotGiven values stripped from the top level.
"""
...


@overload
def strip_not_given(obj: object) -> object: """
Removes top-level keys from a mapping whose values are instances of NotGiven.

If the input is not a mapping or is None, returns the input unchanged.
"""
...


def strip_not_given(obj: object | None) -> object:
    """
    Removes top-level dictionary keys whose values are instances of `NotGiven`.
    
    If the input is not a mapping or is `None`, returns it unchanged.
    """
    if obj is None:
        return None

    if not is_mapping(obj):
        return obj

    return {key: value for key, value in obj.items() if not isinstance(value, NotGiven)}


def coerce_integer(val: str) -> int:
    """
    Convert a string to an integer using base 10.
    
    Parameters:
        val (str): The string representation of an integer.
    
    Returns:
        int: The integer value parsed from the string.
    """
    return int(val, base=10)


def coerce_float(val: str) -> float:
    """
    Convert a string to a floating-point number.
    
    Parameters:
        val (str): The string representation of a float.
    
    Returns:
        float: The converted floating-point number.
    """
    return float(val)


def coerce_boolean(val: str) -> bool:
    """
    Convert a string to a boolean value.
    
    Returns True if the input string is "true", "1", or "on"; otherwise, returns False.
    """
    return val == "true" or val == "1" or val == "on"


def maybe_coerce_integer(val: str | None) -> int | None:
    """
    Convert a string to an integer, returning None if the input is None.
    
    Parameters:
        val (str | None): The string to convert, or None.
    
    Returns:
        int | None: The converted integer, or None if input was None.
    """
    if val is None:
        return None
    return coerce_integer(val)


def maybe_coerce_float(val: str | None) -> float | None:
    """
    Convert a string to a float, returning None if the input is None.
    
    Parameters:
    	val (str | None): The string to convert, or None.
    
    Returns:
    	float | None: The converted float value, or None if input is None.
    """
    if val is None:
        return None
    return coerce_float(val)


def maybe_coerce_boolean(val: str | None) -> bool | None:
    """
    Convert a string to a boolean value, returning None if the input is None.
    
    Parameters:
    	val (str | None): The string to convert, or None.
    
    Returns:
    	bool | None: The converted boolean value, or None if input is None.
    """
    if val is None:
        return None
    return coerce_boolean(val)


def removeprefix(string: str, prefix: str) -> str:
    """
    Return a copy of the string with the specified prefix removed if present.
    
    If the string does not start with the prefix, the original string is returned unchanged.
    """
    if string.startswith(prefix):
        return string[len(prefix) :]
    return string


def removesuffix(string: str, suffix: str) -> str:
    """
    Return a copy of the string with the specified suffix removed, if present.
    
    If the string does not end with the given suffix, the original string is returned unchanged.
    """
    if string.endswith(suffix):
        return string[: -len(suffix)]
    return string


def file_from_path(path: str) -> FileTypes:
    """
    Reads a file from the specified path and returns a tuple containing the file name and its contents as bytes.
    
    Parameters:
        path (str): The path to the file.
    
    Returns:
        FileTypes: A tuple of (file name, file contents as bytes).
    """
    contents = Path(path).read_bytes()
    file_name = os.path.basename(path)
    return (file_name, contents)


def get_required_header(headers: HeadersLike, header: str) -> str:
    """
    Retrieve the value of a specified header from a headers mapping, performing case-insensitive and normalized lookups.
    
    Attempts to match the header name in a case-insensitive manner and with various normalizations (original, lowercase, uppercase, intercaps). Raises a ValueError if the header is not found.
    
    Parameters:
        header (str): The name of the header to retrieve.
    
    Returns:
        str: The value of the specified header.
    
    Raises:
        ValueError: If the header is not found in the mapping.
    """
    lower_header = header.lower()
    if is_mapping_t(headers):
        # mypy doesn't understand the type narrowing here
        for k, v in headers.items():  # type: ignore
            if k.lower() == lower_header and isinstance(v, str):
                return v

    # to deal with the case where the header looks like Stainless-Event-Id
    intercaps_header = re.sub(r"([^\w])(\w)", lambda pat: pat.group(1) + pat.group(2).upper(), header.capitalize())

    for normalized_header in [header, lower_header, header.upper(), intercaps_header]:
        value = headers.get(normalized_header)
        if value:
            return value

    raise ValueError(f"Could not find {header} header")


def get_async_library() -> str:
    """
    Detects and returns the name of the current async library in use.
    
    Returns:
        The name of the detected async library (e.g., "asyncio", "trio"), or "false" if detection fails.
    """
    try:
        return sniffio.current_async_library()
    except Exception:
        return "false"


def lru_cache(*, maxsize: int | None = 128) -> Callable[[CallableT], CallableT]:
    """
    A typed wrapper around functools.lru_cache that preserves the original function's type signature.
    
    Parameters:
        maxsize (int | None): The maximum size of the cache. Defaults to 128.
    
    Returns:
        Callable: A decorator that applies LRU caching while retaining the wrapped function's type annotations.
    """
    wrapper = functools.lru_cache(  # noqa: TID251
        maxsize=maxsize,
    )
    return cast(Any, wrapper)  # type: ignore[no-any-return]


def json_safe(data: object) -> object:
    """
    Recursively converts mappings and sequences into JSON-serializable structures, converting dates and datetimes to ISO format strings.
    
    Parameters:
        data (object): The input object to be converted.
    
    Returns:
        object: A JSON-safe version of the input, with mappings and sequences processed recursively and date/datetime objects converted to ISO strings.
    """
    if is_mapping(data):
        return {json_safe(key): json_safe(value) for key, value in data.items()}

    if is_iterable(data) and not isinstance(data, (str, bytes, bytearray)):
        return [json_safe(item) for item in data]

    if isinstance(data, (datetime, date)):
        return data.isoformat()

    return data
