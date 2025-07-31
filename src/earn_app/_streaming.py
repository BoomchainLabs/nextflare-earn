# Note: initially copied from https://github.com/florimondmanca/httpx-sse/blob/master/src/httpx_sse/_decoders.py
from __future__ import annotations

import json
import inspect
from types import TracebackType
from typing import TYPE_CHECKING, Any, Generic, TypeVar, Iterator, AsyncIterator, cast
from typing_extensions import Self, Protocol, TypeGuard, override, get_origin, runtime_checkable

import httpx

from ._utils import extract_type_var_from_base

if TYPE_CHECKING:
    from ._client import EarnApp, AsyncEarnApp


_T = TypeVar("_T")


class Stream(Generic[_T]):
    """Provides the core interface to iterate over a synchronous stream response."""

    response: httpx.Response

    _decoder: SSEBytesDecoder

    def __init__(
        self,
        *,
        cast_to: type[_T],
        response: httpx.Response,
        client: EarnApp,
    ) -> None:
        """
        Initialize a synchronous SSE stream iterator for processing events from an HTTP response.
        
        Parameters:
            cast_to (type[_T]): The target type to which each SSE event's data will be converted.
            response (httpx.Response): The HTTP response object containing the SSE stream.
        """
        self.response = response
        self._cast_to = cast_to
        self._client = client
        self._decoder = client._make_sse_decoder()
        self._iterator = self.__stream__()

    def __next__(self) -> _T:
        """
        Return the next decoded and processed item from the SSE stream.
        
        Returns:
            The next item of type `_T` from the stream.
        
        Raises:
            StopIteration: If the stream is exhausted.
        """
        return self._iterator.__next__()

    def __iter__(self) -> Iterator[_T]:
        """
        Return an iterator over the decoded and processed items in the SSE stream.
        """
        for item in self._iterator:
            yield item

    def _iter_events(self) -> Iterator[ServerSentEvent]:
        """
        Yields decoded Server-Sent Event objects from the HTTP response byte stream.
        
        Returns:
            Iterator[ServerSentEvent]: An iterator over parsed SSE events from the response.
        """
        yield from self._decoder.iter_bytes(self.response.iter_bytes())

    def __stream__(self) -> Iterator[_T]:
        """
        Yields processed data items from the SSE stream, converting each event's JSON payload to the target type.
        
        Returns:
            Iterator[_T]: An iterator over processed data items of type `_T` from the SSE stream.
        """
        cast_to = cast(Any, self._cast_to)
        response = self.response
        process_data = self._client._process_response_data
        iterator = self._iter_events()

        for sse in iterator:
            yield process_data(data=sse.json(), cast_to=cast_to, response=response)

        # Ensure the entire stream is consumed
        for _sse in iterator:
            ...

    def __enter__(self) -> Self:
        """
        Enter the runtime context for the stream, returning the stream instance itself.
        """
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """
        Ensures the stream is properly closed when exiting a context manager block.
        """
        self.close()

    def close(self) -> None:
        """
        Closes the underlying HTTP response and releases the network connection.
        
        This method should be called to ensure resources are freed if the response body is not fully consumed.
        """
        self.response.close()


class AsyncStream(Generic[_T]):
    """Provides the core interface to iterate over an asynchronous stream response."""

    response: httpx.Response

    _decoder: SSEDecoder | SSEBytesDecoder

    def __init__(
        self,
        *,
        cast_to: type[_T],
        response: httpx.Response,
        client: AsyncEarnApp,
    ) -> None:
        """
        Initialize an asynchronous SSE stream iterator for processing events from an HTTP response.
        
        Parameters:
            cast_to (type[_T]): The target type to which each SSE event's data will be converted.
            response (httpx.Response): The HTTP response object containing the SSE stream.
        """
        self.response = response
        self._cast_to = cast_to
        self._client = client
        self._decoder = client._make_sse_decoder()
        self._iterator = self.__stream__()

    async def __anext__(self) -> _T:
        """
        Return the next item from the asynchronous SSE stream.
        
        Returns:
            The next decoded and processed data item from the stream.
        """
        return await self._iterator.__anext__()

    async def __aiter__(self) -> AsyncIterator[_T]:
        """
        Return an asynchronous iterator over the items in the stream.
        
        Yields:
            Items of type `_T` decoded and processed from the SSE stream.
        """
        async for item in self._iterator:
            yield item

    async def _iter_events(self) -> AsyncIterator[ServerSentEvent]:
        """
        Asynchronously iterates over Server-Sent Events (SSE) decoded from the HTTP response.
        
        Yields:
            ServerSentEvent: The next decoded SSE event from the response stream.
        """
        async for sse in self._decoder.aiter_bytes(self.response.aiter_bytes()):
            yield sse

    async def __stream__(self) -> AsyncIterator[_T]:
        """
        Asynchronously yields processed data items from a Server-Sent Events (SSE) stream.
        
        Yields:
            Items of type `_T` produced by processing each SSE event's JSON data.
        """
        cast_to = cast(Any, self._cast_to)
        response = self.response
        process_data = self._client._process_response_data
        iterator = self._iter_events()

        async for sse in iterator:
            yield process_data(data=sse.json(), cast_to=cast_to, response=response)

        # Ensure the entire stream is consumed
        async for _sse in iterator:
            ...

    async def __aenter__(self) -> Self:
        """
        Enter the asynchronous context manager for the stream, returning the stream instance.
        """
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """
        Exits the asynchronous context manager and closes the stream, releasing any associated resources.
        """
        await self.close()

    async def close(self) -> None:
        """
        Closes the underlying HTTP response and releases the connection.
        
        This method should be called to ensure resources are freed if the response body is not fully consumed.
        """
        await self.response.aclose()


class ServerSentEvent:
    def __init__(
        self,
        *,
        event: str | None = None,
        data: str | None = None,
        id: str | None = None,
        retry: int | None = None,
    ) -> None:
        """
        Initialize a ServerSentEvent instance with optional event type, data, ID, and retry interval.
        
        Parameters:
            event (str | None): The event type, if specified.
            data (str | None): The event data string. Defaults to an empty string if not provided.
            id (str | None): The event ID, if specified.
            retry (int | None): The reconnection time in milliseconds, if specified.
        """
        if data is None:
            data = ""

        self._id = id
        self._data = data
        self._event = event or None
        self._retry = retry

    @property
    def event(self) -> str | None:
        """
        Returns the event type of the Server-Sent Event, or None if not specified.
        """
        return self._event

    @property
    def id(self) -> str | None:
        """
        Return the event ID associated with this Server-Sent Event, or None if not set.
        """
        return self._id

    @property
    def retry(self) -> int | None:
        """
        Return the SSE event's retry interval in milliseconds, or None if not specified.
        """
        return self._retry

    @property
    def data(self) -> str:
        """
        Returns the data payload of the server-sent event as a string.
        """
        return self._data

    def json(self) -> Any:
        """
        Parse the event data as JSON and return the resulting object.
        
        Returns:
            The Python object resulting from decoding the event's data string as JSON.
        """
        return json.loads(self.data)

    @override
    def __repr__(self) -> str:
        """
        Return a string representation of the ServerSentEvent, including its event type, data, id, and retry interval.
        """
        return f"ServerSentEvent(event={self.event}, data={self.data}, id={self.id}, retry={self.retry})"


class SSEDecoder:
    _data: list[str]
    _event: str | None
    _retry: int | None
    _last_event_id: str | None

    def __init__(self) -> None:
        """
        Initialize the SSEDecoder with empty state for parsing Server-Sent Events.
        """
        self._event = None
        self._data = []
        self._last_event_id = None
        self._retry = None

    def iter_bytes(self, iterator: Iterator[bytes]) -> Iterator[ServerSentEvent]:
        """
        Iterates over a stream of raw byte chunks and yields parsed Server-Sent Event objects.
        
        Parameters:
            iterator (Iterator[bytes]): An iterator yielding raw byte chunks from an SSE stream.
        
        Returns:
            Iterator[ServerSentEvent]: An iterator over parsed ServerSentEvent instances extracted from the byte stream.
        """
        for chunk in self._iter_chunks(iterator):
            # Split before decoding so splitlines() only uses \r and \n
            for raw_line in chunk.splitlines():
                line = raw_line.decode("utf-8")
                sse = self.decode(line)
                if sse:
                    yield sse

    def _iter_chunks(self, iterator: Iterator[bytes]) -> Iterator[bytes]:
        """
        Yields complete Server-Sent Event (SSE) message chunks from an iterator of raw byte data.
        
        Each yielded chunk corresponds to a full SSE event, delimited by a double newline sequence.
        """
        data = b""
        for chunk in iterator:
            for line in chunk.splitlines(keepends=True):
                data += line
                if data.endswith((b"\r\r", b"\n\n", b"\r\n\r\n")):
                    yield data
                    data = b""
        if data:
            yield data

    async def aiter_bytes(self, iterator: AsyncIterator[bytes]) -> AsyncIterator[ServerSentEvent]:
        """
        Asynchronously iterates over a stream of raw byte chunks and yields parsed ServerSentEvent objects for each complete SSE event encountered.
        
        Parameters:
            iterator (AsyncIterator[bytes]): An asynchronous iterator yielding raw byte chunks from an SSE stream.
        
        Yields:
            ServerSentEvent: Parsed SSE events as they are decoded from the byte stream.
        """
        async for chunk in self._aiter_chunks(iterator):
            # Split before decoding so splitlines() only uses \r and \n
            for raw_line in chunk.splitlines():
                line = raw_line.decode("utf-8")
                sse = self.decode(line)
                if sse:
                    yield sse

    async def _aiter_chunks(self, iterator: AsyncIterator[bytes]) -> AsyncIterator[bytes]:
        """
        Asynchronously iterates over a stream of bytes and yields complete SSE message chunks.
        
        Each yielded chunk corresponds to a sequence of bytes ending with a double newline, representing a complete SSE event.
        """
        data = b""
        async for chunk in iterator:
            for line in chunk.splitlines(keepends=True):
                data += line
                if data.endswith((b"\r\r", b"\n\n", b"\r\n\r\n")):
                    yield data
                    data = b""
        if data:
            yield data

    def decode(self, line: str) -> ServerSentEvent | None:
        # See: https://html.spec.whatwg.org/multipage/server-sent-events.html#event-stream-interpretation  # noqa: E501

        """
        Parses a single line from an SSE stream and updates the decoder state, returning a complete ServerSentEvent if the line marks the end of an event.
        
        Parameters:
            line (str): A line from the SSE stream.
        
        Returns:
            ServerSentEvent | None: The completed ServerSentEvent if the line is empty and an event is ready; otherwise, None.
        """
        if not line:
            if not self._event and not self._data and not self._last_event_id and self._retry is None:
                return None

            sse = ServerSentEvent(
                event=self._event,
                data="\n".join(self._data),
                id=self._last_event_id,
                retry=self._retry,
            )

            # NOTE: as per the SSE spec, do not reset last_event_id.
            self._event = None
            self._data = []
            self._retry = None

            return sse

        if line.startswith(":"):
            return None

        fieldname, _, value = line.partition(":")

        if value.startswith(" "):
            value = value[1:]

        if fieldname == "event":
            self._event = value
        elif fieldname == "data":
            self._data.append(value)
        elif fieldname == "id":
            if "\0" in value:
                pass
            else:
                self._last_event_id = value
        elif fieldname == "retry":
            try:
                self._retry = int(value)
            except (TypeError, ValueError):
                pass
        else:
            pass  # Field is ignored.

        return None


@runtime_checkable
class SSEBytesDecoder(Protocol):
    def iter_bytes(self, iterator: Iterator[bytes]) -> Iterator[ServerSentEvent]:
        """
        Iterates over a stream of raw byte chunks and yields parsed Server-Sent Event objects.
        
        Parameters:
            iterator (Iterator[bytes]): An iterator yielding raw byte chunks from an SSE stream.
        
        Returns:
            Iterator[ServerSentEvent]: An iterator yielding ServerSentEvent instances parsed from the input bytes.
        """
        ...

    def aiter_bytes(self, iterator: AsyncIterator[bytes]) -> AsyncIterator[ServerSentEvent]:
        """
        Asynchronously iterates over a stream of raw binary data and yields each parsed Server-Sent Event.
        
        Parameters:
            iterator (AsyncIterator[bytes]): An asynchronous iterator yielding chunks of raw SSE data.
        
        Returns:
            AsyncIterator[ServerSentEvent]: An asynchronous iterator yielding ServerSentEvent instances as they are parsed from the input stream.
        """
        ...


def is_stream_class_type(typ: type) -> TypeGuard[type[Stream[object]] | type[AsyncStream[object]]]:
    """
    Determines if the given type is a subclass of Stream or AsyncStream.
    
    Returns:
    	TypeGuard[type[Stream[object]] | type[AsyncStream[object]]]: True if the type is a Stream or AsyncStream subclass, otherwise False.
    """
    origin = get_origin(typ) or typ
    return inspect.isclass(origin) and issubclass(origin, (Stream, AsyncStream))


def extract_stream_chunk_type(
    stream_cls: type,
    *,
    failure_message: str | None = None,
) -> type:
    """
    Extracts the generic type parameter from a Stream or AsyncStream subclass.
    
    If a concrete subclass is provided (e.g., `class MyStream(Stream[bytes])`), returns the specified type parameter (e.g., `bytes`). Supports both Stream and AsyncStream base classes.
    
    Parameters:
        stream_cls (type): The stream class to inspect.
        failure_message (str, optional): Custom error message if extraction fails.
    
    Returns:
        type: The extracted generic type parameter.
    """
    from ._base_client import Stream, AsyncStream

    return extract_type_var_from_base(
        stream_cls,
        index=0,
        generic_bases=cast("tuple[type, ...]", (Stream, AsyncStream)),
        failure_message=failure_message,
    )
