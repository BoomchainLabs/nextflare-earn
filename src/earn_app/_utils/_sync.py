from __future__ import annotations

import sys
import asyncio
import functools
import contextvars
from typing import Any, TypeVar, Callable, Awaitable
from typing_extensions import ParamSpec

import anyio
import sniffio
import anyio.to_thread

T_Retval = TypeVar("T_Retval")
T_ParamSpec = ParamSpec("T_ParamSpec")


if sys.version_info >= (3, 9):
    _asyncio_to_thread = asyncio.to_thread
else:
    # backport of https://docs.python.org/3/library/asyncio-task.html#asyncio.to_thread
    # for Python 3.8 support
    async def _asyncio_to_thread(
        func: Callable[T_ParamSpec, T_Retval], /, *args: T_ParamSpec.args, **kwargs: T_ParamSpec.kwargs
    ) -> Any:
        """
        Run a synchronous function asynchronously in a separate thread, propagating context variables.
        
        Parameters:
            func: The synchronous function to execute in a thread.
            *args: Positional arguments to pass to the function.
            **kwargs: Keyword arguments to pass to the function.
        
        Returns:
            The result of the function call, awaited as a coroutine.
        
        The current context variables are preserved and accessible within the thread.
        """
        loop = asyncio.events.get_running_loop()
        ctx = contextvars.copy_context()
        func_call = functools.partial(ctx.run, func, *args, **kwargs)
        return await loop.run_in_executor(None, func_call)


async def to_thread(
    func: Callable[T_ParamSpec, T_Retval], /, *args: T_ParamSpec.args, **kwargs: T_ParamSpec.kwargs
) -> T_Retval:
    """
    Run a blocking function in a separate thread and await its result, compatible with multiple async libraries.
    
    Parameters:
        func: The synchronous callable to execute in a thread.
        *args: Positional arguments to pass to the callable.
        **kwargs: Keyword arguments to pass to the callable.
    
    Returns:
        The result returned by the blocking function, awaited asynchronously.
    """
    if sniffio.current_async_library() == "asyncio":
        return await _asyncio_to_thread(func, *args, **kwargs)

    return await anyio.to_thread.run_sync(
        functools.partial(func, *args, **kwargs),
    )


# inspired by `asyncer`, https://github.com/tiangolo/asyncer
def asyncify(function: Callable[T_ParamSpec, T_Retval]) -> Callable[T_ParamSpec, Awaitable[T_Retval]]:
    """
    Convert a blocking function into an asynchronous function that runs in a thread.
    
    The returned async function accepts the same arguments as the original and executes it in a thread, allowing integration of blocking code into async workflows.
    
    Parameters:
        function (Callable): The blocking function to be wrapped.
    
    Returns:
        Callable: An async function that runs the original function in a thread and returns its result.
    """

    async def wrapper(*args: T_ParamSpec.args, **kwargs: T_ParamSpec.kwargs) -> T_Retval:
        """
        Asynchronous wrapper that runs the original blocking function in a separate thread.
        
        Accepts the same arguments as the original function and returns its result as an awaitable.
        """
        return await to_thread(function, *args, **kwargs)

    return wrapper
