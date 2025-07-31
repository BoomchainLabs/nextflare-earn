from __future__ import annotations

import os
import inspect
import logging
import datetime
import functools
from types import TracebackType
from typing import (
    TYPE_CHECKING,
    Any,
    Union,
    Generic,
    TypeVar,
    Callable,
    Iterator,
    AsyncIterator,
    cast,
    overload,
)
from typing_extensions import Awaitable, ParamSpec, override, get_origin

import anyio
import httpx
import pydantic

from ._types import NoneType
from ._utils import is_given, extract_type_arg, is_annotated_type, is_type_alias_type, extract_type_var_from_base
from ._models import BaseModel, is_basemodel
from ._constants import RAW_RESPONSE_HEADER, OVERRIDE_CAST_TO_HEADER
from ._streaming import Stream, AsyncStream, is_stream_class_type, extract_stream_chunk_type
from ._exceptions import EarnAppError, APIResponseValidationError

if TYPE_CHECKING:
    from ._models import FinalRequestOptions
    from ._base_client import BaseClient


P = ParamSpec("P")
R = TypeVar("R")
_T = TypeVar("_T")
_APIResponseT = TypeVar("_APIResponseT", bound="APIResponse[Any]")
_AsyncAPIResponseT = TypeVar("_AsyncAPIResponseT", bound="AsyncAPIResponse[Any]")

log: logging.Logger = logging.getLogger(__name__)


class BaseAPIResponse(Generic[R]):
    _cast_to: type[R]
    _client: BaseClient[Any, Any]
    _parsed_by_type: dict[type[Any], Any]
    _is_sse_stream: bool
    _stream_cls: type[Stream[Any]] | type[AsyncStream[Any]] | None
    _options: FinalRequestOptions

    http_response: httpx.Response

    retries_taken: int
    """The number of retries made. If no retries happened this will be `0`"""

    def __init__(
        self,
        *,
        raw: httpx.Response,
        cast_to: type[R],
        client: BaseClient[Any, Any],
        stream: bool,
        stream_cls: type[Stream[Any]] | type[AsyncStream[Any]] | None,
        options: FinalRequestOptions,
        retries_taken: int = 0,
    ) -> None:
        """
        Initialize a BaseAPIResponse instance with the given HTTP response, client, parsing type, and streaming configuration.
        
        Parameters:
            raw (httpx.Response): The underlying HTTP response object.
            cast_to (type): The target type for parsing the response content.
            stream (bool): Whether the response should be handled as a stream (e.g., SSE).
            stream_cls (type | None): The stream class to use for streaming responses, if applicable.
            options (FinalRequestOptions): The finalized request options used for this response.
            retries_taken (int): The number of retry attempts made for this request.
        """
        self._cast_to = cast_to
        self._client = client
        self._parsed_by_type = {}
        self._is_sse_stream = stream
        self._stream_cls = stream_cls
        self._options = options
        self.http_response = raw
        self.retries_taken = retries_taken

    @property
    def headers(self) -> httpx.Headers:
        """
        Return the HTTP headers from the underlying response.
        """
        return self.http_response.headers

    @property
    def http_request(self) -> httpx.Request:
        """
        Return the `httpx.Request` object associated with this response.
        """
        return self.http_response.request

    @property
    def status_code(self) -> int:
        """
        Return the HTTP status code of the response.
        """
        return self.http_response.status_code

    @property
    def url(self) -> httpx.URL:
        """
        Returns the URL of the HTTP request associated with this response.
        
        Returns:
            httpx.URL: The URL that was requested.
        """
        return self.http_response.url

    @property
    def method(self) -> str:
        """
        Return the HTTP method used for the request (e.g., 'GET', 'POST').
        """
        return self.http_request.method

    @property
    def http_version(self) -> str:
        """
        Return the HTTP protocol version used in the response.
        """
        return self.http_response.http_version

    @property
    def elapsed(self) -> datetime.timedelta:
        """
        Returns the duration of the complete HTTP request and response cycle.
        
        Returns:
            datetime.timedelta: The elapsed time between sending the request and receiving the response.
        """
        return self.http_response.elapsed

    @property
    def is_closed(self) -> bool:
        """
        Indicates whether the response body has been closed.
        
        Returns:
            bool: True if the response body is closed; False if there is unread response data remaining.
        """
        return self.http_response.is_closed

    @override
    def __repr__(self) -> str:
        """
        Return a string representation of the response object, including its class name, HTTP status code, reason phrase, and parsed type.
        """
        return (
            f"<{self.__class__.__name__} [{self.status_code} {self.http_response.reason_phrase}] type={self._cast_to}>"
        )

    def _parse(self, *, to: type[_T] | None = None) -> R | _T:
        """
        Parses the HTTP response content into the specified Python type.
        
        If a target type is provided via `to`, the response is parsed and converted to that type; otherwise, the default cast type is used. Supports parsing to primitive types, Pydantic models subclassing the custom `BaseModel`, lists, dictionaries, and custom stream types. Handles server-sent event (SSE) streaming, type aliases, and annotated types. Raises errors for unsupported types, invalid content types when strict validation is enabled, or misconfigured streaming classes.
        
        Parameters:
            to (type, optional): The type to parse the response into. If not provided, uses the default cast type.
        
        Returns:
            The parsed response content as the specified type, or as the default type if `to` is not given.
        
        Raises:
            TypeError: If an invalid stream or model type is provided.
            ValueError: If a subclass of `httpx.Response` is passed to `cast_to`.
            RuntimeError: If an unsupported type is requested.
            APIResponseValidationError: If strict validation is enabled and the response content type is not JSON.
            MissingStreamClassError: If streaming is requested but no stream class is configured.
        """
        cast_to = to if to is not None else self._cast_to

        # unwrap `TypeAlias('Name', T)` -> `T`
        if is_type_alias_type(cast_to):
            cast_to = cast_to.__value__  # type: ignore[unreachable]

        # unwrap `Annotated[T, ...]` -> `T`
        if cast_to and is_annotated_type(cast_to):
            cast_to = extract_type_arg(cast_to, 0)

        origin = get_origin(cast_to) or cast_to

        if self._is_sse_stream:
            if to:
                if not is_stream_class_type(to):
                    raise TypeError(f"Expected custom parse type to be a subclass of {Stream} or {AsyncStream}")

                return cast(
                    _T,
                    to(
                        cast_to=extract_stream_chunk_type(
                            to,
                            failure_message="Expected custom stream type to be passed with a type argument, e.g. Stream[ChunkType]",
                        ),
                        response=self.http_response,
                        client=cast(Any, self._client),
                    ),
                )

            if self._stream_cls:
                return cast(
                    R,
                    self._stream_cls(
                        cast_to=extract_stream_chunk_type(self._stream_cls),
                        response=self.http_response,
                        client=cast(Any, self._client),
                    ),
                )

            stream_cls = cast("type[Stream[Any]] | type[AsyncStream[Any]] | None", self._client._default_stream_cls)
            if stream_cls is None:
                raise MissingStreamClassError()

            return cast(
                R,
                stream_cls(
                    cast_to=cast_to,
                    response=self.http_response,
                    client=cast(Any, self._client),
                ),
            )

        if cast_to is NoneType:
            return cast(R, None)

        response = self.http_response
        if cast_to == str:
            return cast(R, response.text)

        if cast_to == bytes:
            return cast(R, response.content)

        if cast_to == int:
            return cast(R, int(response.text))

        if cast_to == float:
            return cast(R, float(response.text))

        if cast_to == bool:
            return cast(R, response.text.lower() == "true")

        if origin == APIResponse:
            raise RuntimeError("Unexpected state - cast_to is `APIResponse`")

        if inspect.isclass(origin) and issubclass(origin, httpx.Response):
            # Because of the invariance of our ResponseT TypeVar, users can subclass httpx.Response
            # and pass that class to our request functions. We cannot change the variance to be either
            # covariant or contravariant as that makes our usage of ResponseT illegal. We could construct
            # the response class ourselves but that is something that should be supported directly in httpx
            # as it would be easy to incorrectly construct the Response object due to the multitude of arguments.
            if cast_to != httpx.Response:
                raise ValueError(f"Subclasses of httpx.Response cannot be passed to `cast_to`")
            return cast(R, response)

        if (
            inspect.isclass(
                origin  # pyright: ignore[reportUnknownArgumentType]
            )
            and not issubclass(origin, BaseModel)
            and issubclass(origin, pydantic.BaseModel)
        ):
            raise TypeError("Pydantic models must subclass our base model type, e.g. `from earn_app import BaseModel`")

        if (
            cast_to is not object
            and not origin is list
            and not origin is dict
            and not origin is Union
            and not issubclass(origin, BaseModel)
        ):
            raise RuntimeError(
                f"Unsupported type, expected {cast_to} to be a subclass of {BaseModel}, {dict}, {list}, {Union}, {NoneType}, {str} or {httpx.Response}."
            )

        # split is required to handle cases where additional information is included
        # in the response, e.g. application/json; charset=utf-8
        content_type, *_ = response.headers.get("content-type", "*").split(";")
        if not content_type.endswith("json"):
            if is_basemodel(cast_to):
                try:
                    data = response.json()
                except Exception as exc:
                    log.debug("Could not read JSON from response data due to %s - %s", type(exc), exc)
                else:
                    return self._client._process_response_data(
                        data=data,
                        cast_to=cast_to,  # type: ignore
                        response=response,
                    )

            if self._client._strict_response_validation:
                raise APIResponseValidationError(
                    response=response,
                    message=f"Expected Content-Type response header to be `application/json` but received `{content_type}` instead.",
                    body=response.text,
                )

            # If the API responds with content that isn't JSON then we just return
            # the (decoded) text without performing any parsing so that you can still
            # handle the response however you need to.
            return response.text  # type: ignore

        data = response.json()

        return self._client._process_response_data(
            data=data,
            cast_to=cast_to,  # type: ignore
            response=response,
        )


class APIResponse(BaseAPIResponse[R]):
    @overload
    def parse(self, *, to: type[_T]) -> _T: """
Parse the response content into the specified type.

Parameters:
    to (type): The target type to parse the response content into.

Returns:
    The parsed response content as an instance of the specified type.
"""
...

    @overload
    def parse(self) -> R: """
Parses and returns the response content as the expected type.

Returns:
	The parsed response content as the type specified by the response's generic parameter.
"""
...

    def parse(self, *, to: type[_T] | None = None) -> R | _T:
        """
        Parse and return the response data as a rich Python object of the specified type.
        
        Parameters:
            to (type, optional): The type to parse the response data into. If not provided, uses the default type associated with the response.
        
        Returns:
            The parsed response data as an instance of the specified type, which may be a Pydantic model, dict, list, primitive type, or httpx.Response.
        
        Raises:
            APIResponseValidationError: If strict validation is enabled and the response content type is not compatible with the requested type.
            MissingStreamClassError: If streaming is requested but no stream class is configured.
        
        You can use this method to convert the raw response into a custom model or standard Python type for further processing.
        """
        cache_key = to if to is not None else self._cast_to
        cached = self._parsed_by_type.get(cache_key)
        if cached is not None:
            return cached  # type: ignore[no-any-return]

        if not self._is_sse_stream:
            self.read()

        parsed = self._parse(to=to)
        if is_given(self._options.post_parser):
            parsed = self._options.post_parser(parsed)

        self._parsed_by_type[cache_key] = parsed
        return parsed

    def read(self) -> bytes:
        """
        Reads and returns the entire binary content of the HTTP response.
        
        Returns:
            bytes: The full response body as bytes.
        
        Raises:
            StreamAlreadyConsumed: If the response content has already been consumed or streamed.
        """
        try:
            return self.http_response.read()
        except httpx.StreamConsumed as exc:
            # The default error raised by httpx isn't very
            # helpful in our case so we re-raise it with
            # a different error message.
            raise StreamAlreadyConsumed() from exc

    def text(self) -> str:
        """
        Return the response content decoded as a string.
        
        Returns:
            str: The response body as a decoded string.
        """
        self.read()
        return self.http_response.text

    def json(self) -> object:
        """
        Return the response content decoded as a JSON object.
        
        Returns:
            The parsed JSON content of the response.
        """
        self.read()
        return self.http_response.json()

    def close(self) -> None:
        """
        Closes the response and releases the underlying HTTP connection.
        
        This method should be called to free network resources if the response body is not fully consumed.
        """
        self.http_response.close()

    def iter_bytes(self, chunk_size: int | None = None) -> Iterator[bytes]:
        """
        Yields chunks of decoded response content as bytes.
        
        Automatically handles gzip, deflate, and brotli encoded responses.
        
        Parameters:
            chunk_size (int, optional): The number of bytes per chunk. If None, uses the default chunk size.
        
        Returns:
            Iterator[bytes]: An iterator over chunks of response bytes.
        """
        for chunk in self.http_response.iter_bytes(chunk_size):
            yield chunk

    def iter_text(self, chunk_size: int | None = None) -> Iterator[str]:
        """
        Yield decoded text chunks from the HTTP response content, automatically handling compression and character encoding.
        
        Parameters:
            chunk_size (int, optional): Number of bytes per chunk. If None, uses the default chunk size.
        
        Yields:
            str: Decoded text chunks from the response body.
        """
        for chunk in self.http_response.iter_text(chunk_size):
            yield chunk

    def iter_lines(self) -> Iterator[str]:
        """
        Iterates over the response content, yielding one line of text at a time.
        
        Returns:
            An iterator over lines of the response body as strings.
        """
        for chunk in self.http_response.iter_lines():
            yield chunk


class AsyncAPIResponse(BaseAPIResponse[R]):
    @overload
    async def parse(self, *, to: type[_T]) -> _T: """
Asynchronously parses the HTTP response content into the specified type.

Parameters:
    to (type[_T]): The target type to parse the response content into.

Returns:
    _T: The parsed response content as an instance of the specified type.
"""
...

    @overload
    async def parse(self) -> R: """
Asynchronously parses the HTTP response content into the expected Python type.

Returns:
	The parsed response content as the type specified by the response's generic parameter.
"""
...

    async def parse(self, *, to: type[_T] | None = None) -> R | _T:
        """
        Asynchronously parses the response data into a specified Python type.
        
        Parameters:
            to (type[_T], optional): The type to parse the response data into. If not provided, uses the default type associated with the response.
        
        Returns:
            R | _T: The parsed response data as the specified type or the default type.
        
        The method supports parsing into Pydantic models (`BaseModel`), dictionaries, lists, unions, strings, or the raw `httpx.Response` object. Parsed results are cached for subsequent calls.
        """
        cache_key = to if to is not None else self._cast_to
        cached = self._parsed_by_type.get(cache_key)
        if cached is not None:
            return cached  # type: ignore[no-any-return]

        if not self._is_sse_stream:
            await self.read()

        parsed = self._parse(to=to)
        if is_given(self._options.post_parser):
            parsed = self._options.post_parser(parsed)

        self._parsed_by_type[cache_key] = parsed
        return parsed

    async def read(self) -> bytes:
        """
        Asynchronously reads and returns the entire binary content of the HTTP response.
        
        Returns:
            bytes: The full response body as bytes.
        
        Raises:
            StreamAlreadyConsumed: If the response content has already been consumed.
        """
        try:
            return await self.http_response.aread()
        except httpx.StreamConsumed as exc:
            # the default error raised by httpx isn't very
            # helpful in our case so we re-raise it with
            # a different error message
            raise StreamAlreadyConsumed() from exc

    async def text(self) -> str:
        """
        Asynchronously reads and returns the response content as a decoded string.
        """
        await self.read()
        return self.http_response.text

    async def json(self) -> object:
        """
        Asynchronously reads and decodes the response content as JSON.
        
        Returns:
            The parsed JSON object from the response content.
        """
        await self.read()
        return self.http_response.json()

    async def close(self) -> None:
        """
        Closes the response and releases the underlying network connection.
        
        This method should be called to ensure resources are freed if the response is not fully consumed.
        """
        await self.http_response.aclose()

    async def iter_bytes(self, chunk_size: int | None = None) -> AsyncIterator[bytes]:
        """
        Asynchronously yields chunks of decoded response content as bytes.
        
        Parameters:
            chunk_size (int, optional): The number of bytes per chunk. If None, a default size is used.
        
        Yields:
            bytes: Chunks of the response body, automatically handling gzip, deflate, and brotli encodings.
        """
        async for chunk in self.http_response.aiter_bytes(chunk_size):
            yield chunk

    async def iter_text(self, chunk_size: int | None = None) -> AsyncIterator[str]:
        """
        Asynchronously iterates over the response content as decoded text chunks.
        
        Parameters:
            chunk_size (int, optional): The maximum number of bytes to read per chunk. If None, uses the default chunk size.
        
        Yields:
            str: Decoded text chunks from the response content.
        """
        async for chunk in self.http_response.aiter_text(chunk_size):
            yield chunk

    async def iter_lines(self) -> AsyncIterator[str]:
        """
        Asynchronously iterates over the response content, yielding one line of text at a time.
        
        Yields:
            str: The next line from the response content.
        """
        async for chunk in self.http_response.aiter_lines():
            yield chunk


class BinaryAPIResponse(APIResponse[bytes]):
    """Subclass of APIResponse providing helpers for dealing with binary data.

    Note: If you want to stream the response data instead of eagerly reading it
    all at once then you should use `.with_streaming_response` when making
    the API request, e.g. `.with_streaming_response.get_binary_response()`
    """

    def write_to_file(
        self,
        file: str | os.PathLike[str],
    ) -> None:
        """
        Write the entire binary response content to a file.
        
        Parameters:
            file (str | os.PathLike[str]): The target file path or path-like object where the response content will be written.
        
        Note:
            To stream large responses directly to a file without loading all data into memory, use a streaming response method instead.
        """
        with open(file, mode="wb") as f:
            for data in self.iter_bytes():
                f.write(data)


class AsyncBinaryAPIResponse(AsyncAPIResponse[bytes]):
    """Subclass of APIResponse providing helpers for dealing with binary data.

    Note: If you want to stream the response data instead of eagerly reading it
    all at once then you should use `.with_streaming_response` when making
    the API request, e.g. `.with_streaming_response.get_binary_response()`
    """

    async def write_to_file(
        self,
        file: str | os.PathLike[str],
    ) -> None:
        """
        Asynchronously writes the entire binary response content to a file.
        
        Parameters:
            file (str | os.PathLike[str]): The target file path where the response content will be written. Accepts a string or any path-like object.
        
        Note:
            To stream large responses directly to a file without loading all data into memory, use a streaming response method instead.
        """
        path = anyio.Path(file)
        async with await path.open(mode="wb") as f:
            async for data in self.iter_bytes():
                await f.write(data)


class StreamedBinaryAPIResponse(APIResponse[bytes]):
    def stream_to_file(
        self,
        file: str | os.PathLike[str],
        *,
        chunk_size: int | None = None,
    ) -> None:
        """
        Stream the binary response content to a file in chunks.
        
        Parameters:
            file (str | os.PathLike[str]): The target file path to write the streamed content.
            chunk_size (int | None): Optional size of each chunk in bytes. If not specified, a default chunk size is used.
        """
        with open(file, mode="wb") as f:
            for data in self.iter_bytes(chunk_size):
                f.write(data)


class AsyncStreamedBinaryAPIResponse(AsyncAPIResponse[bytes]):
    async def stream_to_file(
        self,
        file: str | os.PathLike[str],
        *,
        chunk_size: int | None = None,
    ) -> None:
        """
        Asynchronously streams the response content to a file in binary mode.
        
        Parameters:
            file (str | os.PathLike[str]): The target file path or path-like object to write the streamed content.
            chunk_size (int | None): Optional size of each chunk to write; defaults to implementation-defined size if not specified.
        """
        path = anyio.Path(file)
        async with await path.open(mode="wb") as f:
            async for data in self.iter_bytes(chunk_size):
                await f.write(data)


class MissingStreamClassError(TypeError):
    def __init__(self) -> None:
        """
        Initialize the exception for missing stream class configuration when streaming is requested.
        """
        super().__init__(
            "The `stream` argument was set to `True` but the `stream_cls` argument was not given. See `earn_app._streaming` for reference",
        )


class StreamAlreadyConsumed(EarnAppError):
    """
    Attempted to read or stream content, but the content has already
    been streamed.

    This can happen if you use a method like `.iter_lines()` and then attempt
    to read th entire response body afterwards, e.g.

    ```py
    response = await client.post(...)
    async for line in response.iter_lines():
        ...  # do something with `line`

    content = await response.read()
    # ^ error
    ```

    If you want this behaviour you'll need to either manually accumulate the response
    content or call `await response.read()` before iterating over the stream.
    """

    def __init__(self) -> None:
        """
        Initialize the exception for attempts to read or stream response content that has already been consumed.
        
        Raises an error with a message explaining that the response content cannot be accessed again after it has been streamed or read.
        """
        message = (
            "Attempted to read or stream some content, but the content has "
            "already been streamed. "
            "This could be due to attempting to stream the response "
            "content more than once."
            "\n\n"
            "You can fix this by manually accumulating the response content while streaming "
            "or by calling `.read()` before starting to stream."
        )
        super().__init__(message)


class ResponseContextManager(Generic[_APIResponseT]):
    """Context manager for ensuring that a request is not made
    until it is entered and that the response will always be closed
    when the context manager exits
    """

    def __init__(self, request_func: Callable[[], _APIResponseT]) -> None:
        """
        Initialize the context manager with a function that returns an API response instance.
        
        Parameters:
            request_func: A callable that, when invoked, returns an API response object to be managed within the context.
        """
        self._request_func = request_func
        self.__response: _APIResponseT | None = None

    def __enter__(self) -> _APIResponseT:
        """
        Enter the context manager, executing the wrapped request function and returning the API response object.
        
        Returns:
            The API response object produced by the wrapped request function.
        """
        self.__response = self._request_func()
        return self.__response

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """
        Closes the underlying response when exiting the context manager.
        
        Ensures that the response is properly closed and resources are released upon exiting the context, regardless of whether an exception occurred.
        """
        if self.__response is not None:
            self.__response.close()


class AsyncResponseContextManager(Generic[_AsyncAPIResponseT]):
    """Context manager for ensuring that a request is not made
    until it is entered and that the response will always be closed
    when the context manager exits
    """

    def __init__(self, api_request: Awaitable[_AsyncAPIResponseT]) -> None:
        """
        Initialize the asynchronous response context manager with a pending API request.
        
        Parameters:
        	api_request: An awaitable that yields an asynchronous API response when awaited.
        """
        self._api_request = api_request
        self.__response: _AsyncAPIResponseT | None = None

    async def __aenter__(self) -> _AsyncAPIResponseT:
        """
        Enter the asynchronous context manager, executing the API request and returning the response object.
        
        Returns:
            The awaited asynchronous API response instance.
        """
        self.__response = await self._api_request
        return self.__response

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """
        Asynchronously exits the context manager, ensuring the response is closed and resources are released.
        """
        if self.__response is not None:
            await self.__response.close()


def to_streamed_response_wrapper(func: Callable[P, R]) -> Callable[P, ResponseContextManager[APIResponse[R]]]:
    """
    Wraps a synchronous API method to return a context-managed streaming API response.
    
    Returns:
        A callable that, when invoked, yields a `ResponseContextManager` for an `APIResponse` with streaming enabled.
    """

    @functools.wraps(func)
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> ResponseContextManager[APIResponse[R]]:
        """
        Wraps a synchronous API client method to return a ResponseContextManager that yields a streaming APIResponse.
        
        The wrapped function injects headers to enable streaming mode and delays request execution until entering the context manager.
        """
        extra_headers: dict[str, str] = {**(cast(Any, kwargs.get("extra_headers")) or {})}
        extra_headers[RAW_RESPONSE_HEADER] = "stream"

        kwargs["extra_headers"] = extra_headers

        make_request = functools.partial(func, *args, **kwargs)

        return ResponseContextManager(cast(Callable[[], APIResponse[R]], make_request))

    return wrapped


def async_to_streamed_response_wrapper(
    func: Callable[P, Awaitable[R]],
) -> Callable[P, AsyncResponseContextManager[AsyncAPIResponse[R]]]:
    """
    Wraps an asynchronous API method to return an async context manager yielding a streamed raw response.
    
    The wrapped function injects headers to enable streaming and returns an `AsyncResponseContextManager` that yields an `AsyncAPIResponse` object for direct access to the raw HTTP response.
    """

    @functools.wraps(func)
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> AsyncResponseContextManager[AsyncAPIResponse[R]]:
        """
        Wraps an asynchronous API client method to return an async context manager yielding a streamed async API response.
        
        The wrapped function injects a special header to enable streaming mode and returns an `AsyncResponseContextManager` that manages the lifecycle of the `AsyncAPIResponse`. This allows safe and efficient handling of streamed HTTP responses in asynchronous workflows.
        """
        extra_headers: dict[str, str] = {**(cast(Any, kwargs.get("extra_headers")) or {})}
        extra_headers[RAW_RESPONSE_HEADER] = "stream"

        kwargs["extra_headers"] = extra_headers

        make_request = func(*args, **kwargs)

        return AsyncResponseContextManager(cast(Awaitable[AsyncAPIResponse[R]], make_request))

    return wrapped


def to_custom_streamed_response_wrapper(
    func: Callable[P, object],
    response_cls: type[_APIResponseT],
) -> Callable[P, ResponseContextManager[_APIResponseT]]:
    """
    Wraps a synchronous API client method to return a context-managed custom streaming response class.
    
    The returned function injects headers to enable streaming and ensures the specified concrete response class is used. The response is provided within a `ResponseContextManager` for safe resource handling.
    """

    @functools.wraps(func)
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> ResponseContextManager[_APIResponseT]:
        """
        Wraps a synchronous API client method to return a context-managed custom streaming response.
        
        The wrapped function injects headers to enable streaming and specifies a custom response class, returning a `ResponseContextManager` that ensures proper resource management for the streamed response.
        """
        extra_headers: dict[str, Any] = {**(cast(Any, kwargs.get("extra_headers")) or {})}
        extra_headers[RAW_RESPONSE_HEADER] = "stream"
        extra_headers[OVERRIDE_CAST_TO_HEADER] = response_cls

        kwargs["extra_headers"] = extra_headers

        make_request = functools.partial(func, *args, **kwargs)

        return ResponseContextManager(cast(Callable[[], _APIResponseT], make_request))

    return wrapped


def async_to_custom_streamed_response_wrapper(
    func: Callable[P, Awaitable[object]],
    response_cls: type[_AsyncAPIResponseT],
) -> Callable[P, AsyncResponseContextManager[_AsyncAPIResponseT]]:
    """
    Wraps an asynchronous API method to return an async context manager yielding a custom streamed response class.
    
    The provided `response_cls` must be a concrete subclass of `AsyncAPIResponse`. The wrapper injects headers to enable streaming and ensures the response is managed within an asynchronous context manager.
    """

    @functools.wraps(func)
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> AsyncResponseContextManager[_AsyncAPIResponseT]:
        """
        Wraps an asynchronous API client method to return an async context manager yielding a custom streamed response class.
        
        The wrapped function injects headers to enable streaming and specifies the custom response class for parsing. The returned context manager ensures proper resource management of the streamed response.
        """
        extra_headers: dict[str, Any] = {**(cast(Any, kwargs.get("extra_headers")) or {})}
        extra_headers[RAW_RESPONSE_HEADER] = "stream"
        extra_headers[OVERRIDE_CAST_TO_HEADER] = response_cls

        kwargs["extra_headers"] = extra_headers

        make_request = func(*args, **kwargs)

        return AsyncResponseContextManager(cast(Awaitable[_AsyncAPIResponseT], make_request))

    return wrapped


def to_raw_response_wrapper(func: Callable[P, R]) -> Callable[P, APIResponse[R]]:
    """
    Wraps an API method to return the raw `APIResponse` object, injecting headers to enable raw response handling.
    
    Returns:
    	A callable that, when invoked, executes the original API method and returns an `APIResponse` instance with raw response mode enabled.
    """

    @functools.wraps(func)
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> APIResponse[R]:
        """
        Wraps an API client method to return a raw APIResponse, injecting a header to request the raw response object.
        
        Returns:
            APIResponse[R]: The raw API response object with the requested type.
        """
        extra_headers: dict[str, str] = {**(cast(Any, kwargs.get("extra_headers")) or {})}
        extra_headers[RAW_RESPONSE_HEADER] = "raw"

        kwargs["extra_headers"] = extra_headers

        return cast(APIResponse[R], func(*args, **kwargs))

    return wrapped


def async_to_raw_response_wrapper(func: Callable[P, Awaitable[R]]) -> Callable[P, Awaitable[AsyncAPIResponse[R]]]:
    """
    Wraps an asynchronous API method to return the raw `AsyncAPIResponse` object, injecting headers to enable raw response handling.
    
    Returns:
        A callable that, when invoked, returns an awaitable yielding an `AsyncAPIResponse` containing the raw HTTP response.
    """

    @functools.wraps(func)
    async def wrapped(*args: P.args, **kwargs: P.kwargs) -> AsyncAPIResponse[R]:
        """
        Wraps an asynchronous API client method to return an AsyncAPIResponse with raw response handling enabled.
        
        Adds a special header to the request to indicate that the raw HTTP response should be returned, and passes through all arguments to the original function.
        
        Returns:
            AsyncAPIResponse[R]: The asynchronous API response object containing the raw HTTP response.
        """
        extra_headers: dict[str, str] = {**(cast(Any, kwargs.get("extra_headers")) or {})}
        extra_headers[RAW_RESPONSE_HEADER] = "raw"

        kwargs["extra_headers"] = extra_headers

        return cast(AsyncAPIResponse[R], await func(*args, **kwargs))

    return wrapped


def to_custom_raw_response_wrapper(
    func: Callable[P, object],
    response_cls: type[_APIResponseT],
) -> Callable[P, _APIResponseT]:
    """
    Wraps an API method to return a specified concrete APIResponse subclass, injecting headers to enable raw response handling.
    
    Parameters:
        func: The API method to wrap.
        response_cls: The concrete APIResponse subclass to return.
    
    Returns:
        A wrapped function that returns an instance of the specified response class with raw response handling enabled.
    """

    @functools.wraps(func)
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> _APIResponseT:
        """
        Wraps a synchronous API client method to return a custom raw response class instance.
        
        Adds headers to request raw response handling and overrides the response cast type with the specified response class.
        """
        extra_headers: dict[str, Any] = {**(cast(Any, kwargs.get("extra_headers")) or {})}
        extra_headers[RAW_RESPONSE_HEADER] = "raw"
        extra_headers[OVERRIDE_CAST_TO_HEADER] = response_cls

        kwargs["extra_headers"] = extra_headers

        return cast(_APIResponseT, func(*args, **kwargs))

    return wrapped


def async_to_custom_raw_response_wrapper(
    func: Callable[P, Awaitable[object]],
    response_cls: type[_AsyncAPIResponseT],
) -> Callable[P, Awaitable[_AsyncAPIResponseT]]:
    """
    Wraps an asynchronous API method to return a specified custom async response class directly.
    
    The provided `response_cls` must be a concrete subclass of `AsyncAPIResponse`. This wrapper injects headers to request the raw response and override the default response type, enabling the API method to yield an instance of the given response class.
    """

    @functools.wraps(func)
    def wrapped(*args: P.args, **kwargs: P.kwargs) -> Awaitable[_AsyncAPIResponseT]:
        """
        Wraps an asynchronous API client method to return a custom raw response class.
        
        This decorator injects headers to request the raw HTTP response and specifies the custom response class to use for parsing. The wrapped function returns an awaitable that yields an instance of the specified asynchronous response class.
        """
        extra_headers: dict[str, Any] = {**(cast(Any, kwargs.get("extra_headers")) or {})}
        extra_headers[RAW_RESPONSE_HEADER] = "raw"
        extra_headers[OVERRIDE_CAST_TO_HEADER] = response_cls

        kwargs["extra_headers"] = extra_headers

        return cast(Awaitable[_AsyncAPIResponseT], func(*args, **kwargs))

    return wrapped


def extract_response_type(typ: type[BaseAPIResponse[Any]]) -> type:
    """
    Extracts the generic type argument from a BaseAPIResponse subclass.
    
    Given a response type such as APIResponse[T] or a concrete subclass, returns the type used as the generic parameter (e.g., bytes, dict, or a custom model).
    
    Parameters:
    	typ (type[BaseAPIResponse[Any]]): The response class to inspect.
    
    Returns:
    	type: The extracted generic type argument.
    """
    return extract_type_var_from_base(
        typ,
        generic_bases=cast("tuple[type, ...]", (BaseAPIResponse, APIResponse, AsyncAPIResponse)),
        index=0,
    )
