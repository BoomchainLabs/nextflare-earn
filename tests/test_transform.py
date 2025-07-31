from __future__ import annotations

import io
import pathlib
from typing import Any, Dict, List, Union, TypeVar, Iterable, Optional, cast
from datetime import date, datetime
from typing_extensions import Required, Annotated, TypedDict

import pytest

from earn_app._types import NOT_GIVEN, Base64FileInput
from earn_app._utils import (
    PropertyInfo,
    transform as _transform,
    parse_datetime,
    async_transform as _async_transform,
)
from earn_app._compat import PYDANTIC_V2
from earn_app._models import BaseModel

_T = TypeVar("_T")

SAMPLE_FILE_PATH = pathlib.Path(__file__).parent.joinpath("sample_file.txt")


async def transform(
    data: _T,
    expected_type: object,
    use_async: bool,
) -> _T:
    """
    Transforms input data to match the specified type, using either asynchronous or synchronous processing.
    
    Parameters:
        data: The input data to be transformed.
        expected_type: The target type or schema to which the data should conform.
        use_async: If True, performs the transformation asynchronously; otherwise, uses synchronous processing.
    
    Returns:
        The transformed data, structured according to the expected type.
    """
    if use_async:
        return await _async_transform(data, expected_type=expected_type)

    return _transform(data, expected_type=expected_type)


parametrize = pytest.mark.parametrize("use_async", [False, True], ids=["sync", "async"])


class Foo1(TypedDict):
    foo_bar: Annotated[str, PropertyInfo(alias="fooBar")]


@parametrize
@pytest.mark.asyncio
async def test_top_level_alias(use_async: bool) -> None:
    """
    Tests that a top-level TypedDict field is correctly transformed using its alias.
    
    Verifies that the key `foo_bar` is mapped to its alias `fooBar` during transformation.
    """
    assert await transform({"foo_bar": "hello"}, expected_type=Foo1, use_async=use_async) == {"fooBar": "hello"}


class Foo2(TypedDict):
    bar: Bar2


class Bar2(TypedDict):
    this_thing: Annotated[int, PropertyInfo(alias="this__thing")]
    baz: Annotated[Baz2, PropertyInfo(alias="Baz")]


class Baz2(TypedDict):
    my_baz: Annotated[str, PropertyInfo(alias="myBaz")]


@parametrize
@pytest.mark.asyncio
async def test_recursive_typeddict(use_async: bool) -> None:
    """
    Test that nested TypedDicts with aliased keys are recursively transformed as expected.
    
    Verifies that the transformation utility correctly applies key aliasing at multiple levels of nesting within TypedDict structures.
    """
    assert await transform({"bar": {"this_thing": 1}}, Foo2, use_async) == {"bar": {"this__thing": 1}}
    assert await transform({"bar": {"baz": {"my_baz": "foo"}}}, Foo2, use_async) == {"bar": {"Baz": {"myBaz": "foo"}}}


class Foo3(TypedDict):
    things: List[Bar3]


class Bar3(TypedDict):
    my_field: Annotated[str, PropertyInfo(alias="myField")]


@parametrize
@pytest.mark.asyncio
async def test_list_of_typeddict(use_async: bool) -> None:
    """
    Tests that a list of TypedDicts is transformed with correct aliasing of field names.
    
    Parameters:
        use_async (bool): If True, runs the test using the asynchronous transformation; otherwise, uses the synchronous transformation.
    """
    result = await transform({"things": [{"my_field": "foo"}, {"my_field": "foo2"}]}, Foo3, use_async)
    assert result == {"things": [{"myField": "foo"}, {"myField": "foo2"}]}


class Foo4(TypedDict):
    foo: Union[Bar4, Baz4]


class Bar4(TypedDict):
    foo_bar: Annotated[str, PropertyInfo(alias="fooBar")]


class Baz4(TypedDict):
    foo_baz: Annotated[str, PropertyInfo(alias="fooBaz")]


@parametrize
@pytest.mark.asyncio
async def test_union_of_typeddict(use_async: bool) -> None:
    """
    Test that transformation correctly handles union fields of TypedDicts with aliased keys, including cases with overlapping keys.
    """
    assert await transform({"foo": {"foo_bar": "bar"}}, Foo4, use_async) == {"foo": {"fooBar": "bar"}}
    assert await transform({"foo": {"foo_baz": "baz"}}, Foo4, use_async) == {"foo": {"fooBaz": "baz"}}
    assert await transform({"foo": {"foo_baz": "baz", "foo_bar": "bar"}}, Foo4, use_async) == {
        "foo": {"fooBaz": "baz", "fooBar": "bar"}
    }


class Foo5(TypedDict):
    foo: Annotated[Union[Bar4, List[Baz4]], PropertyInfo(alias="FOO")]


class Bar5(TypedDict):
    foo_bar: Annotated[str, PropertyInfo(alias="fooBar")]


class Baz5(TypedDict):
    foo_baz: Annotated[str, PropertyInfo(alias="fooBaz")]


@parametrize
@pytest.mark.asyncio
async def test_union_of_list(use_async: bool) -> None:
    """
    Test transformation of union types involving a TypedDict or a list of TypedDicts with key aliasing.
    
    Verifies that both single TypedDict and list of TypedDict inputs are correctly transformed according to the expected type and key aliases.
    """
    assert await transform({"foo": {"foo_bar": "bar"}}, Foo5, use_async) == {"FOO": {"fooBar": "bar"}}
    assert await transform(
        {
            "foo": [
                {"foo_baz": "baz"},
                {"foo_baz": "baz"},
            ]
        },
        Foo5,
        use_async,
    ) == {"FOO": [{"fooBaz": "baz"}, {"fooBaz": "baz"}]}


class Foo6(TypedDict):
    bar: Annotated[str, PropertyInfo(alias="Bar")]


@parametrize
@pytest.mark.asyncio
async def test_includes_unknown_keys(use_async: bool) -> None:
    """
    Test that unknown keys in the input dictionary are preserved during transformation, alongside aliased fields.
    """
    assert await transform({"bar": "bar", "baz_": {"FOO": 1}}, Foo6, use_async) == {
        "Bar": "bar",
        "baz_": {"FOO": 1},
    }


class Foo7(TypedDict):
    bar: Annotated[List[Bar7], PropertyInfo(alias="bAr")]
    foo: Bar7


class Bar7(TypedDict):
    foo: str


@parametrize
@pytest.mark.asyncio
async def test_ignores_invalid_input(use_async: bool) -> None:
    """
    Tests that invalid input types for aliased fields are passed through without transformation, and non-aliased fields are preserved as-is.
    """
    assert await transform({"bar": "<foo>"}, Foo7, use_async) == {"bAr": "<foo>"}
    assert await transform({"foo": "<foo>"}, Foo7, use_async) == {"foo": "<foo>"}


class DatetimeDict(TypedDict, total=False):
    foo: Annotated[datetime, PropertyInfo(format="iso8601")]

    bar: Annotated[Optional[datetime], PropertyInfo(format="iso8601")]

    required: Required[Annotated[Optional[datetime], PropertyInfo(format="iso8601")]]

    list_: Required[Annotated[Optional[List[datetime]], PropertyInfo(format="iso8601")]]

    union: Annotated[Union[int, datetime], PropertyInfo(format="iso8601")]


class DateDict(TypedDict, total=False):
    foo: Annotated[date, PropertyInfo(format="iso8601")]


class DatetimeModel(BaseModel):
    foo: datetime


class DateModel(BaseModel):
    foo: Optional[date]


@parametrize
@pytest.mark.asyncio
async def test_iso8601_format(use_async: bool) -> None:
    """
    Test that datetime and date fields are correctly transformed to ISO8601-formatted strings or None in both TypedDicts and Pydantic models, handling both timezone-aware and naive datetimes.
    """
    dt = datetime.fromisoformat("2023-02-23T14:16:36.337692+00:00")
    tz = "Z" if PYDANTIC_V2 else "+00:00"
    assert await transform({"foo": dt}, DatetimeDict, use_async) == {"foo": "2023-02-23T14:16:36.337692+00:00"}  # type: ignore[comparison-overlap]
    assert await transform(DatetimeModel(foo=dt), Any, use_async) == {"foo": "2023-02-23T14:16:36.337692" + tz}  # type: ignore[comparison-overlap]

    dt = dt.replace(tzinfo=None)
    assert await transform({"foo": dt}, DatetimeDict, use_async) == {"foo": "2023-02-23T14:16:36.337692"}  # type: ignore[comparison-overlap]
    assert await transform(DatetimeModel(foo=dt), Any, use_async) == {"foo": "2023-02-23T14:16:36.337692"}  # type: ignore[comparison-overlap]

    assert await transform({"foo": None}, DateDict, use_async) == {"foo": None}  # type: ignore[comparison-overlap]
    assert await transform(DateModel(foo=None), Any, use_async) == {"foo": None}  # type: ignore
    assert await transform({"foo": date.fromisoformat("2023-02-23")}, DateDict, use_async) == {"foo": "2023-02-23"}  # type: ignore[comparison-overlap]
    assert await transform(DateModel(foo=date.fromisoformat("2023-02-23")), DateDict, use_async) == {
        "foo": "2023-02-23"
    }  # type: ignore[comparison-overlap]


@parametrize
@pytest.mark.asyncio
async def test_optional_iso8601_format(use_async: bool) -> None:
    """
    Test that optional datetime fields are correctly transformed to ISO8601 strings or None.
    """
    dt = datetime.fromisoformat("2023-02-23T14:16:36.337692+00:00")
    assert await transform({"bar": dt}, DatetimeDict, use_async) == {"bar": "2023-02-23T14:16:36.337692+00:00"}  # type: ignore[comparison-overlap]

    assert await transform({"bar": None}, DatetimeDict, use_async) == {"bar": None}


@parametrize
@pytest.mark.asyncio
async def test_required_iso8601_format(use_async: bool) -> None:
    """
    Test that required datetime fields are transformed to ISO8601 strings and None values are preserved.
    """
    dt = datetime.fromisoformat("2023-02-23T14:16:36.337692+00:00")
    assert await transform({"required": dt}, DatetimeDict, use_async) == {
        "required": "2023-02-23T14:16:36.337692+00:00"
    }  # type: ignore[comparison-overlap]

    assert await transform({"required": None}, DatetimeDict, use_async) == {"required": None}


@parametrize
@pytest.mark.asyncio
async def test_union_datetime(use_async: bool) -> None:
    """
    Test that union fields containing datetime or string values are correctly transformed, ensuring datetimes are formatted as ISO8601 strings and strings are left unchanged.
    """
    dt = datetime.fromisoformat("2023-02-23T14:16:36.337692+00:00")
    assert await transform({"union": dt}, DatetimeDict, use_async) == {  # type: ignore[comparison-overlap]
        "union": "2023-02-23T14:16:36.337692+00:00"
    }

    assert await transform({"union": "foo"}, DatetimeDict, use_async) == {"union": "foo"}


@parametrize
@pytest.mark.asyncio
async def test_nested_list_iso6801_format(use_async: bool) -> None:
    """
    Test that lists of datetime objects are transformed to ISO8601-formatted strings within TypedDicts.
    """
    dt1 = datetime.fromisoformat("2023-02-23T14:16:36.337692+00:00")
    dt2 = parse_datetime("2022-01-15T06:34:23Z")
    assert await transform({"list_": [dt1, dt2]}, DatetimeDict, use_async) == {  # type: ignore[comparison-overlap]
        "list_": ["2023-02-23T14:16:36.337692+00:00", "2022-01-15T06:34:23+00:00"]
    }


@parametrize
@pytest.mark.asyncio
async def test_datetime_custom_format(use_async: bool) -> None:
    """
    Tests that a datetime object is transformed to a string using a custom format template.
    
    Parameters:
        use_async (bool): If True, runs the transformation asynchronously; otherwise, synchronously.
    """
    dt = parse_datetime("2022-01-15T06:34:23Z")

    result = await transform(dt, Annotated[datetime, PropertyInfo(format="custom", format_template="%H")], use_async)
    assert result == "06"  # type: ignore[comparison-overlap]


class DateDictWithRequiredAlias(TypedDict, total=False):
    required_prop: Required[Annotated[date, PropertyInfo(format="iso8601", alias="prop")]]


@parametrize
@pytest.mark.asyncio
async def test_datetime_with_alias(use_async: bool) -> None:
    """
    Test that a required date field with an alias is correctly transformed to its aliased key and ISO8601 string format, or None if the value is None.
    """
    assert await transform({"required_prop": None}, DateDictWithRequiredAlias, use_async) == {"prop": None}  # type: ignore[comparison-overlap]
    assert await transform(
        {"required_prop": date.fromisoformat("2023-02-23")}, DateDictWithRequiredAlias, use_async
    ) == {"prop": "2023-02-23"}  # type: ignore[comparison-overlap]


class MyModel(BaseModel):
    foo: str


@parametrize
@pytest.mark.asyncio
async def test_pydantic_model_to_dictionary(use_async: bool) -> None:
    """
    Test that Pydantic models, including those constructed with `construct`, are transformed into dictionaries with their field values.
    """
    assert cast(Any, await transform(MyModel(foo="hi!"), Any, use_async)) == {"foo": "hi!"}
    assert cast(Any, await transform(MyModel.construct(foo="hi!"), Any, use_async)) == {"foo": "hi!"}


@parametrize
@pytest.mark.asyncio
async def test_pydantic_empty_model(use_async: bool) -> None:
    """
    Test that transforming an empty Pydantic model returns an empty dictionary.
    """
    assert cast(Any, await transform(MyModel.construct(), Any, use_async)) == {}


@parametrize
@pytest.mark.asyncio
async def test_pydantic_unknown_field(use_async: bool) -> None:
    """
    Test that unknown fields in a Pydantic model are preserved during transformation.
    """
    assert cast(Any, await transform(MyModel.construct(my_untyped_field=True), Any, use_async)) == {
        "my_untyped_field": True
    }


@parametrize
@pytest.mark.asyncio
async def test_pydantic_mismatched_types(use_async: bool) -> None:
    """
    Test that transforming a Pydantic model with mismatched field types preserves the original values, emitting a warning in Pydantic v2.
    """
    model = MyModel.construct(foo=True)
    if PYDANTIC_V2:
        with pytest.warns(UserWarning):
            params = await transform(model, Any, use_async)
    else:
        params = await transform(model, Any, use_async)
    assert cast(Any, params) == {"foo": True}


@parametrize
@pytest.mark.asyncio
async def test_pydantic_mismatched_object_type(use_async: bool) -> None:
    """
    Test that a Pydantic model field containing another model instance is transformed into a nested dictionary structure.
    
    Verifies that when a Pydantic model has a field set to another model instance, the transformation produces a dictionary with nested dictionaries, and emits a warning in Pydantic v2.
    """
    model = MyModel.construct(foo=MyModel.construct(hello="world"))
    if PYDANTIC_V2:
        with pytest.warns(UserWarning):
            params = await transform(model, Any, use_async)
    else:
        params = await transform(model, Any, use_async)
    assert cast(Any, params) == {"foo": {"hello": "world"}}


class ModelNestedObjects(BaseModel):
    nested: MyModel


@parametrize
@pytest.mark.asyncio
async def test_pydantic_nested_objects(use_async: bool) -> None:
    """
    Test that nested Pydantic models are correctly transformed into dictionaries with nested structures preserved.
    """
    model = ModelNestedObjects.construct(nested={"foo": "stainless"})
    assert isinstance(model.nested, MyModel)
    assert cast(Any, await transform(model, Any, use_async)) == {"nested": {"foo": "stainless"}}


class ModelWithDefaultField(BaseModel):
    foo: str
    with_none_default: Union[str, None] = None
    with_str_default: str = "foo"


@parametrize
@pytest.mark.asyncio
async def test_pydantic_default_field(use_async: bool) -> None:
    # should be excluded when defaults are used
    """
    Tests that fields with default values in a Pydantic model are excluded from transformation output unless explicitly set, and are included when explicitly provided with default or non-default values.
    """
    model = ModelWithDefaultField.construct()
    assert model.with_none_default is None
    assert model.with_str_default == "foo"
    assert cast(Any, await transform(model, Any, use_async)) == {}

    # should be included when the default value is explicitly given
    model = ModelWithDefaultField.construct(with_none_default=None, with_str_default="foo")
    assert model.with_none_default is None
    assert model.with_str_default == "foo"
    assert cast(Any, await transform(model, Any, use_async)) == {"with_none_default": None, "with_str_default": "foo"}

    # should be included when a non-default value is explicitly given
    model = ModelWithDefaultField.construct(with_none_default="bar", with_str_default="baz")
    assert model.with_none_default == "bar"
    assert model.with_str_default == "baz"
    assert cast(Any, await transform(model, Any, use_async)) == {"with_none_default": "bar", "with_str_default": "baz"}


class TypedDictIterableUnion(TypedDict):
    foo: Annotated[Union[Bar8, Iterable[Baz8]], PropertyInfo(alias="FOO")]


class Bar8(TypedDict):
    foo_bar: Annotated[str, PropertyInfo(alias="fooBar")]


class Baz8(TypedDict):
    foo_baz: Annotated[str, PropertyInfo(alias="fooBaz")]


@parametrize
@pytest.mark.asyncio
async def test_iterable_of_dictionaries(use_async: bool) -> None:
    """
    Test that iterables of TypedDicts are transformed correctly, including lists, tuples, and generators, with proper key aliasing.
    """
    assert await transform({"foo": [{"foo_baz": "bar"}]}, TypedDictIterableUnion, use_async) == {
        "FOO": [{"fooBaz": "bar"}]
    }
    assert cast(Any, await transform({"foo": ({"foo_baz": "bar"},)}, TypedDictIterableUnion, use_async)) == {
        "FOO": [{"fooBaz": "bar"}]
    }

    def my_iter() -> Iterable[Baz8]:
        """
        Yield two Baz8 TypedDict instances with 'foo_baz' values 'hello' and 'world'.
        
        Returns:
            An iterable of Baz8 dictionaries with preset 'foo_baz' values.
        """
        yield {"foo_baz": "hello"}
        yield {"foo_baz": "world"}

    assert await transform({"foo": my_iter()}, TypedDictIterableUnion, use_async) == {
        "FOO": [{"fooBaz": "hello"}, {"fooBaz": "world"}]
    }


@parametrize
@pytest.mark.asyncio
async def test_dictionary_items(use_async: bool) -> None:
    """
    Tests that dictionary values, when TypedDicts with aliased fields, are transformed so that the aliases are applied to the nested items.
    """
    class DictItems(TypedDict):
        foo_baz: Annotated[str, PropertyInfo(alias="fooBaz")]

    assert await transform({"foo": {"foo_baz": "bar"}}, Dict[str, DictItems], use_async) == {"foo": {"fooBaz": "bar"}}


class TypedDictIterableUnionStr(TypedDict):
    foo: Annotated[Union[str, Iterable[Baz8]], PropertyInfo(alias="FOO")]


@parametrize
@pytest.mark.asyncio
async def test_iterable_union_str(use_async: bool) -> None:
    """
    Test transformation of union types involving strings and iterables of TypedDicts with aliasing.
    
    Verifies that string values are preserved and iterables of TypedDicts are transformed with correct key aliasing when using both synchronous and asynchronous transformation modes.
    """
    assert await transform({"foo": "bar"}, TypedDictIterableUnionStr, use_async) == {"FOO": "bar"}
    assert cast(Any, await transform(iter([{"foo_baz": "bar"}]), Union[str, Iterable[Baz8]], use_async)) == [
        {"fooBaz": "bar"}
    ]


class TypedDictBase64Input(TypedDict):
    foo: Annotated[Union[str, Base64FileInput], PropertyInfo(format="base64")]


@parametrize
@pytest.mark.asyncio
async def test_base64_file_input(use_async: bool) -> None:
    # strings are left as-is
    """
    Tests that the transform function correctly handles base64-encoded file input fields, leaving strings unchanged and converting pathlib.Path and file-like objects to base64 strings.
    """
    assert await transform({"foo": "bar"}, TypedDictBase64Input, use_async) == {"foo": "bar"}

    # pathlib.Path is automatically converted to base64
    assert await transform({"foo": SAMPLE_FILE_PATH}, TypedDictBase64Input, use_async) == {
        "foo": "SGVsbG8sIHdvcmxkIQo="
    }  # type: ignore[comparison-overlap]

    # io instances are automatically converted to base64
    assert await transform({"foo": io.StringIO("Hello, world!")}, TypedDictBase64Input, use_async) == {
        "foo": "SGVsbG8sIHdvcmxkIQ=="
    }  # type: ignore[comparison-overlap]
    assert await transform({"foo": io.BytesIO(b"Hello, world!")}, TypedDictBase64Input, use_async) == {
        "foo": "SGVsbG8sIHdvcmxkIQ=="
    }  # type: ignore[comparison-overlap]


@parametrize
@pytest.mark.asyncio
async def test_transform_skipping(use_async: bool) -> None:
    # lists of ints are left as-is
    """
    Test that lists of integers are returned unchanged, while iterables of integers are converted to lists during transformation.
    """
    data = [1, 2, 3]
    assert await transform(data, List[int], use_async) is data

    # iterables of ints are converted to a list
    data = iter([1, 2, 3])
    assert await transform(data, Iterable[int], use_async) == [1, 2, 3]


@parametrize
@pytest.mark.asyncio
async def test_strips_notgiven(use_async: bool) -> None:
    """
    Tests that fields with the sentinel value `NOT_GIVEN` are omitted from the transformed output, while valid fields are included.
    """
    assert await transform({"foo_bar": "bar"}, Foo1, use_async) == {"fooBar": "bar"}
    assert await transform({"foo_bar": NOT_GIVEN}, Foo1, use_async) == {}
