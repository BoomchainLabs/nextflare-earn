from __future__ import annotations

from typing import Iterator, AsyncIterator

import httpx
import pytest

from earn_app import EarnApp, AsyncEarnApp
from earn_app._streaming import Stream, AsyncStream, ServerSentEvent


@pytest.mark.asyncio
@pytest.mark.parametrize("sync", [True, False], ids=["sync", "async"])
async def test_basic(sync: bool, client: EarnApp, async_client: AsyncEarnApp) -> None:
    """
    Test parsing of a basic Server-Sent Event with an event type and JSON data in both sync and async modes.
    
    Verifies that the event type and JSON-decoded data are correctly extracted from the SSE stream, and that the iterator is exhausted after the event.
    """
    def body() -> Iterator[bytes]:
        yield b"event: completion\n"
        yield b'data: {"foo":true}\n'
        yield b"\n"

    iterator = make_event_iterator(content=body(), sync=sync, client=client, async_client=async_client)

    sse = await iter_next(iterator)
    assert sse.event == "completion"
    assert sse.json() == {"foo": True}

    await assert_empty_iter(iterator)


@pytest.mark.asyncio
@pytest.mark.parametrize("sync", [True, False], ids=["sync", "async"])
async def test_data_missing_event(sync: bool, client: EarnApp, async_client: AsyncEarnApp) -> None:
    """
    Test SSE parsing when an event contains data but no event type.
    
    Verifies that the event's `event` field is `None` and the JSON data is correctly parsed.
    """
    def body() -> Iterator[bytes]:
        yield b'data: {"foo":true}\n'
        yield b"\n"

    iterator = make_event_iterator(content=body(), sync=sync, client=client, async_client=async_client)

    sse = await iter_next(iterator)
    assert sse.event is None
    assert sse.json() == {"foo": True}

    await assert_empty_iter(iterator)


@pytest.mark.asyncio
@pytest.mark.parametrize("sync", [True, False], ids=["sync", "async"])
async def test_event_missing_data(sync: bool, client: EarnApp, async_client: AsyncEarnApp) -> None:
    """
    Test that an SSE event with an event type but no data is parsed correctly.
    
    Verifies that the event name is set and the data field is an empty string when the SSE message contains only an event type.
    """
    def body() -> Iterator[bytes]:
        yield b"event: ping\n"
        yield b"\n"

    iterator = make_event_iterator(content=body(), sync=sync, client=client, async_client=async_client)

    sse = await iter_next(iterator)
    assert sse.event == "ping"
    assert sse.data == ""

    await assert_empty_iter(iterator)


@pytest.mark.asyncio
@pytest.mark.parametrize("sync", [True, False], ids=["sync", "async"])
async def test_multiple_events(sync: bool, client: EarnApp, async_client: AsyncEarnApp) -> None:
    """
    Test parsing of multiple SSE events without data fields in both sync and async modes.
    
    Verifies that two consecutive events ("ping" and "completion") are correctly parsed with empty data, and that the iterator is exhausted afterward.
    """
    def body() -> Iterator[bytes]:
        yield b"event: ping\n"
        yield b"\n"
        yield b"event: completion\n"
        yield b"\n"

    iterator = make_event_iterator(content=body(), sync=sync, client=client, async_client=async_client)

    sse = await iter_next(iterator)
    assert sse.event == "ping"
    assert sse.data == ""

    sse = await iter_next(iterator)
    assert sse.event == "completion"
    assert sse.data == ""

    await assert_empty_iter(iterator)


@pytest.mark.asyncio
@pytest.mark.parametrize("sync", [True, False], ids=["sync", "async"])
async def test_multiple_events_with_data(sync: bool, client: EarnApp, async_client: AsyncEarnApp) -> None:
    """
    Test parsing of multiple SSE events with associated JSON data in both sync and async modes.
    
    Verifies that each event is correctly parsed with its event type and JSON-decoded data, and that the iterator is exhausted after all events are consumed.
    """
    def body() -> Iterator[bytes]:
        yield b"event: ping\n"
        yield b'data: {"foo":true}\n'
        yield b"\n"
        yield b"event: completion\n"
        yield b'data: {"bar":false}\n'
        yield b"\n"

    iterator = make_event_iterator(content=body(), sync=sync, client=client, async_client=async_client)

    sse = await iter_next(iterator)
    assert sse.event == "ping"
    assert sse.json() == {"foo": True}

    sse = await iter_next(iterator)
    assert sse.event == "completion"
    assert sse.json() == {"bar": False}

    await assert_empty_iter(iterator)


@pytest.mark.asyncio
@pytest.mark.parametrize("sync", [True, False], ids=["sync", "async"])
async def test_multiple_data_lines_with_empty_line(sync: bool, client: EarnApp, async_client: AsyncEarnApp) -> None:
    """
    Test parsing of an SSE event with multiple data lines, including empty lines, ensuring correct data concatenation and JSON decoding.
    
    Verifies that empty and blank data lines are handled properly and that the resulting data string and JSON object match expectations.
    """
    def body() -> Iterator[bytes]:
        yield b"event: ping\n"
        yield b"data: {\n"
        yield b'data: "foo":\n'
        yield b"data: \n"
        yield b"data:\n"
        yield b"data: true}\n"
        yield b"\n\n"

    iterator = make_event_iterator(content=body(), sync=sync, client=client, async_client=async_client)

    sse = await iter_next(iterator)
    assert sse.event == "ping"
    assert sse.json() == {"foo": True}
    assert sse.data == '{\n"foo":\n\n\ntrue}'

    await assert_empty_iter(iterator)


@pytest.mark.asyncio
@pytest.mark.parametrize("sync", [True, False], ids=["sync", "async"])
async def test_data_json_escaped_double_new_line(sync: bool, client: EarnApp, async_client: AsyncEarnApp) -> None:
    """
    Test parsing of SSE events with JSON data containing escaped double newline characters.
    
    Verifies that the event parser correctly interprets JSON-encoded data fields with escaped newlines, ensuring the resulting data matches the expected structure after decoding.
    """
    def body() -> Iterator[bytes]:
        yield b"event: ping\n"
        yield b'data: {"foo": "my long\\n\\ncontent"}'
        yield b"\n\n"

    iterator = make_event_iterator(content=body(), sync=sync, client=client, async_client=async_client)

    sse = await iter_next(iterator)
    assert sse.event == "ping"
    assert sse.json() == {"foo": "my long\n\ncontent"}

    await assert_empty_iter(iterator)


@pytest.mark.asyncio
@pytest.mark.parametrize("sync", [True, False], ids=["sync", "async"])
async def test_multiple_data_lines(sync: bool, client: EarnApp, async_client: AsyncEarnApp) -> None:
    """
    Test parsing of an SSE event with multiple data lines forming a JSON object.
    
    Verifies that multi-line data fields are concatenated and correctly parsed as JSON in both synchronous and asynchronous streaming modes.
    """
    def body() -> Iterator[bytes]:
        yield b"event: ping\n"
        yield b"data: {\n"
        yield b'data: "foo":\n'
        yield b"data: true}\n"
        yield b"\n\n"

    iterator = make_event_iterator(content=body(), sync=sync, client=client, async_client=async_client)

    sse = await iter_next(iterator)
    assert sse.event == "ping"
    assert sse.json() == {"foo": True}

    await assert_empty_iter(iterator)


@pytest.mark.parametrize("sync", [True, False], ids=["sync", "async"])
async def test_special_new_line_character(
    sync: bool,
    client: EarnApp,
    async_client: AsyncEarnApp,
) -> None:
    """
    Test SSE parsing of events containing special Unicode newline characters in data fields.
    
    Verifies that Server-Sent Events with JSON data containing special newline characters (such as U+2028 LINE SEPARATOR) are correctly parsed and decoded in both synchronous and asynchronous streaming modes.
    """
    def body() -> Iterator[bytes]:
        yield b'data: {"content":" culpa"}\n'
        yield b"\n"
        yield b'data: {"content":" \xe2\x80\xa8"}\n'
        yield b"\n"
        yield b'data: {"content":"foo"}\n'
        yield b"\n"

    iterator = make_event_iterator(content=body(), sync=sync, client=client, async_client=async_client)

    sse = await iter_next(iterator)
    assert sse.event is None
    assert sse.json() == {"content": " culpa"}

    sse = await iter_next(iterator)
    assert sse.event is None
    assert sse.json() == {"content": "  "}

    sse = await iter_next(iterator)
    assert sse.event is None
    assert sse.json() == {"content": "foo"}

    await assert_empty_iter(iterator)


@pytest.mark.parametrize("sync", [True, False], ids=["sync", "async"])
async def test_multi_byte_character_multiple_chunks(
    sync: bool,
    client: EarnApp,
    async_client: AsyncEarnApp,
) -> None:
    """
    Test SSE parsing of multi-byte UTF-8 characters split across multiple byte chunks.
    
    Verifies that the event iterator correctly reconstructs and decodes multi-byte characters in JSON data when the bytes are fragmented across several chunks.
    """
    def body() -> Iterator[bytes]:
        yield b'data: {"content":"'
        # bytes taken from the string 'известни' and arbitrarily split
        # so that some multi-byte characters span multiple chunks
        yield b"\xd0"
        yield b"\xb8\xd0\xb7\xd0"
        yield b"\xb2\xd0\xb5\xd1\x81\xd1\x82\xd0\xbd\xd0\xb8"
        yield b'"}\n'
        yield b"\n"

    iterator = make_event_iterator(content=body(), sync=sync, client=client, async_client=async_client)

    sse = await iter_next(iterator)
    assert sse.event is None
    assert sse.json() == {"content": "известни"}


async def to_aiter(iter: Iterator[bytes]) -> AsyncIterator[bytes]:
    """
    Convert a synchronous iterator of byte chunks into an asynchronous iterator.
    
    Yields:
        bytes: Each chunk from the original iterator, asynchronously.
    """
    for chunk in iter:
        yield chunk


async def iter_next(iter: Iterator[ServerSentEvent] | AsyncIterator[ServerSentEvent]) -> ServerSentEvent:
    """
    Retrieve the next Server-Sent Event from either a synchronous or asynchronous iterator.
    
    Parameters:
    	iter: An iterator or asynchronous iterator yielding ServerSentEvent objects.
    
    Returns:
    	The next ServerSentEvent from the iterator.
    """
    if isinstance(iter, AsyncIterator):
        return await iter.__anext__()

    return next(iter)


async def assert_empty_iter(iter: Iterator[ServerSentEvent] | AsyncIterator[ServerSentEvent]) -> None:
    """
    Assert that the given iterator is exhausted by verifying it raises StopAsyncIteration or RuntimeError when advanced.
    """
    with pytest.raises((StopAsyncIteration, RuntimeError)):
        await iter_next(iter)


def make_event_iterator(
    content: Iterator[bytes],
    *,
    sync: bool,
    client: EarnApp,
    async_client: AsyncEarnApp,
) -> Iterator[ServerSentEvent] | AsyncIterator[ServerSentEvent]:
    """
    Create an iterator over parsed Server-Sent Events (SSE) from a stream of byte chunks.
    
    Depending on the `sync` flag, returns either a synchronous or asynchronous iterator that yields `ServerSentEvent` objects parsed from the provided byte content.
    """
    if sync:
        return Stream(cast_to=object, client=client, response=httpx.Response(200, content=content))._iter_events()

    return AsyncStream(
        cast_to=object, client=async_client, response=httpx.Response(200, content=to_aiter(content))
    )._iter_events()
