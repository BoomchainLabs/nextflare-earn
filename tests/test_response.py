import json
from typing import Any, List, Union, cast
from typing_extensions import Annotated

import httpx
import pytest
import pydantic

from earn_app import EarnApp, BaseModel, AsyncEarnApp
from earn_app._response import (
    APIResponse,
    BaseAPIResponse,
    AsyncAPIResponse,
    BinaryAPIResponse,
    AsyncBinaryAPIResponse,
    extract_response_type,
)
from earn_app._streaming import Stream
from earn_app._base_client import FinalRequestOptions


class ConcreteBaseAPIResponse(APIResponse[bytes]): ...


class ConcreteAPIResponse(APIResponse[List[str]]): ...


class ConcreteAsyncAPIResponse(APIResponse[httpx.Response]): ...


def test_extract_response_type_direct_classes() -> None:
    """
    Test that `extract_response_type` correctly extracts the generic type argument from direct generic response classes.
    """
    assert extract_response_type(BaseAPIResponse[str]) == str
    assert extract_response_type(APIResponse[str]) == str
    assert extract_response_type(AsyncAPIResponse[str]) == str


def test_extract_response_type_direct_class_missing_type_arg() -> None:
    """
    Test that extract_response_type raises a RuntimeError when called on a generic response class without a type argument.
    """
    with pytest.raises(
        RuntimeError,
        match="Expected type <class 'earn_app._response.AsyncAPIResponse'> to have a type argument at index 0 but it did not",
    ):
        extract_response_type(AsyncAPIResponse)


def test_extract_response_type_concrete_subclasses() -> None:
    """
    Test that `extract_response_type` correctly infers the response type from concrete subclasses of API response classes.
    """
    assert extract_response_type(ConcreteBaseAPIResponse) == bytes
    assert extract_response_type(ConcreteAPIResponse) == List[str]
    assert extract_response_type(ConcreteAsyncAPIResponse) == httpx.Response


def test_extract_response_type_binary_response() -> None:
    """
    Test that `extract_response_type` returns `bytes` for both binary response classes.
    """
    assert extract_response_type(BinaryAPIResponse) == bytes
    assert extract_response_type(AsyncBinaryAPIResponse) == bytes


class PydanticModel(pydantic.BaseModel): ...


def test_response_parse_mismatched_basemodel(client: EarnApp) -> None:
    """
    Test that parsing a response into a Pydantic model not subclassing the package's BaseModel raises a TypeError.
    """
    response = APIResponse(
        raw=httpx.Response(200, content=b"foo"),
        client=client,
        stream=False,
        stream_cls=None,
        cast_to=str,
        options=FinalRequestOptions.construct(method="get", url="/foo"),
    )

    with pytest.raises(
        TypeError,
        match="Pydantic models must subclass our base model type, e.g. `from earn_app import BaseModel`",
    ):
        response.parse(to=PydanticModel)


@pytest.mark.asyncio
async def test_async_response_parse_mismatched_basemodel(async_client: AsyncEarnApp) -> None:
    """
    Test that parsing an async API response into a Pydantic model not derived from the package's BaseModel raises a TypeError.
    """
    response = AsyncAPIResponse(
        raw=httpx.Response(200, content=b"foo"),
        client=async_client,
        stream=False,
        stream_cls=None,
        cast_to=str,
        options=FinalRequestOptions.construct(method="get", url="/foo"),
    )

    with pytest.raises(
        TypeError,
        match="Pydantic models must subclass our base model type, e.g. `from earn_app import BaseModel`",
    ):
        await response.parse(to=PydanticModel)


def test_response_parse_custom_stream(client: EarnApp) -> None:
    """
    Tests that parsing a streaming API response into a `Stream[int]` sets the stream's cast type to `int`.
    """
    response = APIResponse(
        raw=httpx.Response(200, content=b"foo"),
        client=client,
        stream=True,
        stream_cls=None,
        cast_to=str,
        options=FinalRequestOptions.construct(method="get", url="/foo"),
    )

    stream = response.parse(to=Stream[int])
    assert stream._cast_to == int


@pytest.mark.asyncio
async def test_async_response_parse_custom_stream(async_client: AsyncEarnApp) -> None:
    """
    Asynchronously parses a streaming API response into a Stream of integers and verifies the cast type is set to int.
    """
    response = AsyncAPIResponse(
        raw=httpx.Response(200, content=b"foo"),
        client=async_client,
        stream=True,
        stream_cls=None,
        cast_to=str,
        options=FinalRequestOptions.construct(method="get", url="/foo"),
    )

    stream = await response.parse(to=Stream[int])
    assert stream._cast_to == int


class CustomModel(BaseModel):
    foo: str
    bar: int


def test_response_parse_custom_model(client: EarnApp) -> None:
    """
    Tests parsing a JSON API response into a custom Pydantic model subclass.
    
    Asserts that the parsed object has the expected field values.
    """
    response = APIResponse(
        raw=httpx.Response(200, content=json.dumps({"foo": "hello!", "bar": 2})),
        client=client,
        stream=False,
        stream_cls=None,
        cast_to=str,
        options=FinalRequestOptions.construct(method="get", url="/foo"),
    )

    obj = response.parse(to=CustomModel)
    assert obj.foo == "hello!"
    assert obj.bar == 2


@pytest.mark.asyncio
async def test_async_response_parse_custom_model(async_client: AsyncEarnApp) -> None:
    """
    Asynchronously tests parsing a JSON response into a custom Pydantic model using an AsyncAPIResponse.
    
    Verifies that the parsed object is an instance of CustomModel with correctly populated fields.
    """
    response = AsyncAPIResponse(
        raw=httpx.Response(200, content=json.dumps({"foo": "hello!", "bar": 2})),
        client=async_client,
        stream=False,
        stream_cls=None,
        cast_to=str,
        options=FinalRequestOptions.construct(method="get", url="/foo"),
    )

    obj = await response.parse(to=CustomModel)
    assert obj.foo == "hello!"
    assert obj.bar == 2


def test_response_parse_annotated_type(client: EarnApp) -> None:
    """
    Tests that an APIResponse can parse JSON content into a Pydantic model wrapped in an Annotated type, correctly populating the model's fields.
    """
    response = APIResponse(
        raw=httpx.Response(200, content=json.dumps({"foo": "hello!", "bar": 2})),
        client=client,
        stream=False,
        stream_cls=None,
        cast_to=str,
        options=FinalRequestOptions.construct(method="get", url="/foo"),
    )

    obj = response.parse(
        to=cast("type[CustomModel]", Annotated[CustomModel, "random metadata"]),
    )
    assert obj.foo == "hello!"
    assert obj.bar == 2


async def test_async_response_parse_annotated_type(async_client: AsyncEarnApp) -> None:
    """
    Asynchronously parses a response into an Annotated type wrapping a custom model and verifies correct field values.
    """
    response = AsyncAPIResponse(
        raw=httpx.Response(200, content=json.dumps({"foo": "hello!", "bar": 2})),
        client=async_client,
        stream=False,
        stream_cls=None,
        cast_to=str,
        options=FinalRequestOptions.construct(method="get", url="/foo"),
    )

    obj = await response.parse(
        to=cast("type[CustomModel]", Annotated[CustomModel, "random metadata"]),
    )
    assert obj.foo == "hello!"
    assert obj.bar == 2


@pytest.mark.parametrize(
    "content, expected",
    [
        ("false", False),
        ("true", True),
        ("False", False),
        ("True", True),
        ("TrUe", True),
        ("FalSe", False),
    ],
)
def test_response_parse_bool(client: EarnApp, content: str, expected: bool) -> None:
    """
    Test that APIResponse correctly parses string content into a boolean value.
    
    Asserts that various string representations of boolean values are accurately converted to Python bool when parsed.
    """
    response = APIResponse(
        raw=httpx.Response(200, content=content),
        client=client,
        stream=False,
        stream_cls=None,
        cast_to=str,
        options=FinalRequestOptions.construct(method="get", url="/foo"),
    )

    result = response.parse(to=bool)
    assert result is expected


@pytest.mark.parametrize(
    "content, expected",
    [
        ("false", False),
        ("true", True),
        ("False", False),
        ("True", True),
        ("TrUe", True),
        ("FalSe", False),
    ],
)
async def test_async_response_parse_bool(client: AsyncEarnApp, content: str, expected: bool) -> None:
    """
    Asynchronously parses a string HTTP response into a boolean value and asserts the result matches the expected value.
    
    Parameters:
        content (str): The string content to be parsed as a boolean.
        expected (bool): The expected boolean result after parsing.
    """
    response = AsyncAPIResponse(
        raw=httpx.Response(200, content=content),
        client=client,
        stream=False,
        stream_cls=None,
        cast_to=str,
        options=FinalRequestOptions.construct(method="get", url="/foo"),
    )

    result = await response.parse(to=bool)
    assert result is expected


class OtherModel(BaseModel):
    a: str


@pytest.mark.parametrize("client", [False], indirect=True)  # loose validation
def test_response_parse_expect_model_union_non_json_content(client: EarnApp) -> None:
    """
    Test that parsing a non-JSON response with a union of models returns the raw string content.
    
    Verifies that when the response content type is not JSON and the expected type is a union of models, the parser returns the raw string instead of attempting model deserialization.
    """
    response = APIResponse(
        raw=httpx.Response(200, content=b"foo", headers={"Content-Type": "application/text"}),
        client=client,
        stream=False,
        stream_cls=None,
        cast_to=str,
        options=FinalRequestOptions.construct(method="get", url="/foo"),
    )

    obj = response.parse(to=cast(Any, Union[CustomModel, OtherModel]))
    assert isinstance(obj, str)
    assert obj == "foo"


@pytest.mark.asyncio
@pytest.mark.parametrize("async_client", [False], indirect=True)  # loose validation
async def test_async_response_parse_expect_model_union_non_json_content(async_client: AsyncEarnApp) -> None:
    """
    Asynchronously tests that parsing a non-JSON response with a union of models returns the raw string content.
    
    Verifies that when the response content type is not JSON and the expected type is a union of models, the parser returns the raw string instead of attempting model deserialization.
    """
    response = AsyncAPIResponse(
        raw=httpx.Response(200, content=b"foo", headers={"Content-Type": "application/text"}),
        client=async_client,
        stream=False,
        stream_cls=None,
        cast_to=str,
        options=FinalRequestOptions.construct(method="get", url="/foo"),
    )

    obj = await response.parse(to=cast(Any, Union[CustomModel, OtherModel]))
    assert isinstance(obj, str)
    assert obj == "foo"
