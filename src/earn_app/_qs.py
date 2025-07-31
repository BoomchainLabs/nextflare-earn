from __future__ import annotations

from typing import Any, List, Tuple, Union, Mapping, TypeVar
from urllib.parse import parse_qs, urlencode
from typing_extensions import Literal, get_args

from ._types import NOT_GIVEN, NotGiven, NotGivenOr
from ._utils import flatten

_T = TypeVar("_T")


ArrayFormat = Literal["comma", "repeat", "indices", "brackets"]
NestedFormat = Literal["dots", "brackets"]

PrimitiveData = Union[str, int, float, bool, None]
# this should be Data = Union[PrimitiveData, "List[Data]", "Tuple[Data]", "Mapping[str, Data]"]
# https://github.com/microsoft/pyright/issues/3555
Data = Union[PrimitiveData, List[Any], Tuple[Any], "Mapping[str, Any]"]
Params = Mapping[str, Data]


class Querystring:
    array_format: ArrayFormat
    nested_format: NestedFormat

    def __init__(
        self,
        *,
        array_format: ArrayFormat = "repeat",
        nested_format: NestedFormat = "brackets",
    ) -> None:
        """
        Initialize a Querystring instance with specified array and nested object formatting options.
        
        Parameters:
            array_format (ArrayFormat, optional): Determines how arrays are serialized in query strings. Defaults to "repeat".
            nested_format (NestedFormat, optional): Determines how nested objects are serialized. Defaults to "brackets".
        """
        self.array_format = array_format
        self.nested_format = nested_format

    def parse(self, query: str) -> Mapping[str, object]:
        # Note: custom format syntax is not supported yet
        """
        Parse a URL query string into a mapping of keys to values.
        
        Parameters:
            query (str): The URL query string to parse.
        
        Returns:
            Mapping[str, object]: A mapping where each key is a parameter name and each value is a list of values associated with that key.
        """
        return parse_qs(query)

    def stringify(
        self,
        params: Params,
        *,
        array_format: NotGivenOr[ArrayFormat] = NOT_GIVEN,
        nested_format: NotGivenOr[NestedFormat] = NOT_GIVEN,
    ) -> str:
        """
        Serialize a mapping of parameters into a URL-encoded query string.
        
        Parameters:
            params (Params): Mapping of parameter names to values, supporting nested structures and arrays.
        
        Returns:
            str: The URL-encoded query string representing the parameters.
        """
        return urlencode(
            self.stringify_items(
                params,
                array_format=array_format,
                nested_format=nested_format,
            )
        )

    def stringify_items(
        self,
        params: Params,
        *,
        array_format: NotGivenOr[ArrayFormat] = NOT_GIVEN,
        nested_format: NotGivenOr[NestedFormat] = NOT_GIVEN,
    ) -> list[tuple[str, str]]:
        """
        Convert a mapping of parameters into a flat list of key-value string tuples for query string serialization.
        
        Parameters:
            params (Params): Mapping of parameter names to values, which may include nested structures or arrays.
        
        Returns:
            list[tuple[str, str]]: List of (key, value) pairs representing the serialized parameters according to the specified array and nested formatting options.
        """
        opts = Options(
            qs=self,
            array_format=array_format,
            nested_format=nested_format,
        )
        return flatten([self._stringify_item(key, value, opts) for key, value in params.items()])

    def _stringify_item(
        self,
        key: str,
        value: Data,
        opts: Options,
    ) -> list[tuple[str, str]]:
        """
        Recursively serializes a key-value pair into a list of query string key-value tuples according to the specified array and nested formatting options.
        
        Parameters:
            key (str): The current key to serialize.
            value (Data): The value associated with the key, which may be a primitive, list, tuple, or mapping.
            opts (Options): Formatting options for array and nested object serialization.
        
        Returns:
            list[tuple[str, str]]: A flat list of (key, value) string tuples suitable for URL encoding.
        
        Raises:
            NotImplementedError: If the array format is "indices" or an unknown array format is specified.
        """
        if isinstance(value, Mapping):
            items: list[tuple[str, str]] = []
            nested_format = opts.nested_format
            for subkey, subvalue in value.items():
                items.extend(
                    self._stringify_item(
                        # TODO: error if unknown format
                        f"{key}.{subkey}" if nested_format == "dots" else f"{key}[{subkey}]",
                        subvalue,
                        opts,
                    )
                )
            return items

        if isinstance(value, (list, tuple)):
            array_format = opts.array_format
            if array_format == "comma":
                return [
                    (
                        key,
                        ",".join(self._primitive_value_to_str(item) for item in value if item is not None),
                    ),
                ]
            elif array_format == "repeat":
                items = []
                for item in value:
                    items.extend(self._stringify_item(key, item, opts))
                return items
            elif array_format == "indices":
                raise NotImplementedError("The array indices format is not supported yet")
            elif array_format == "brackets":
                items = []
                key = key + "[]"
                for item in value:
                    items.extend(self._stringify_item(key, item, opts))
                return items
            else:
                raise NotImplementedError(
                    f"Unknown array_format value: {array_format}, choose from {', '.join(get_args(ArrayFormat))}"
                )

        serialised = self._primitive_value_to_str(value)
        if not serialised:
            return []
        return [(key, serialised)]

    def _primitive_value_to_str(self, value: PrimitiveData) -> str:
        # copied from httpx
        """
        Convert a primitive value to its string representation for query string serialization.
        
        Booleans are converted to "true" or "false", None to an empty string, and other types to their string form.
        
        Parameters:
            value (PrimitiveData): The primitive value to convert.
        
        Returns:
            str: The string representation suitable for use in a query string.
        """
        if value is True:
            return "true"
        elif value is False:
            return "false"
        elif value is None:
            return ""
        return str(value)


_qs = Querystring()
parse = _qs.parse
stringify = _qs.stringify
stringify_items = _qs.stringify_items


class Options:
    array_format: ArrayFormat
    nested_format: NestedFormat

    def __init__(
        self,
        qs: Querystring = _qs,
        *,
        array_format: NotGivenOr[ArrayFormat] = NOT_GIVEN,
        nested_format: NotGivenOr[NestedFormat] = NOT_GIVEN,
    ) -> None:
        """
        Initialize formatting options for query string serialization.
        
        If `array_format` or `nested_format` are not provided, defaults are taken from the given `Querystring` instance.
        """
        self.array_format = qs.array_format if isinstance(array_format, NotGiven) else array_format
        self.nested_format = qs.nested_format if isinstance(nested_format, NotGiven) else nested_format
