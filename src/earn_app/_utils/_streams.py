from typing import Any
from typing_extensions import Iterator, AsyncIterator


def consume_sync_iterator(iterator: Iterator[Any]) -> None:
    """
    Exhausts a synchronous iterator by iterating through all its elements without processing them.
    
    Parameters:
        iterator (Iterator[Any]): The iterator to be fully consumed.
    """
    for _ in iterator:
        ...


async def consume_async_iterator(iterator: AsyncIterator[Any]) -> None:
    """
    Asynchronously exhausts an asynchronous iterator, discarding all yielded values.
    
    This function iterates through all elements of the provided asynchronous iterator without performing any operations on them.
    """
    async for _ in iterator:
        ...
