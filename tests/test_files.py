from pathlib import Path

import anyio
import pytest
from dirty_equals import IsDict, IsList, IsBytes, IsTuple

from earn_app._files import to_httpx_files, async_to_httpx_files

readme_path = Path(__file__).parent.parent.joinpath("README.md")


def test_pathlib_includes_file_name() -> None:
    """
    Test that `to_httpx_files` correctly converts a dictionary with a `Path` object value into an HTTPX-compatible file tuple including the filename and file content as bytes.
    """
    result = to_httpx_files({"file": readme_path})
    print(result)
    assert result == IsDict({"file": IsTuple("README.md", IsBytes())})


def test_tuple_input() -> None:
    """
    Test that `to_httpx_files` correctly processes a list of tuples with Path objects, returning a list of tuples containing the field name, filename, and file content as bytes.
    """
    result = to_httpx_files([("file", readme_path)])
    print(result)
    assert result == IsList(IsTuple("file", IsTuple("README.md", IsBytes())))


@pytest.mark.asyncio
async def test_async_pathlib_includes_file_name() -> None:
    """
    Asynchronously tests that async_to_httpx_files correctly converts a dictionary with a Path value into an HTTPX-compatible file tuple including the filename and file content as bytes.
    """
    result = await async_to_httpx_files({"file": readme_path})
    print(result)
    assert result == IsDict({"file": IsTuple("README.md", IsBytes())})


@pytest.mark.asyncio
async def test_async_supports_anyio_path() -> None:
    """
    Test that async_to_httpx_files correctly processes an anyio.Path object as input.
    
    Verifies that the function returns a dictionary mapping the key to a tuple containing the filename and file content as bytes.
    """
    result = await async_to_httpx_files({"file": anyio.Path(readme_path)})
    print(result)
    assert result == IsDict({"file": IsTuple("README.md", IsBytes())})


@pytest.mark.asyncio
async def test_async_tuple_input() -> None:
    """
    Asynchronously tests that `async_to_httpx_files` correctly converts a list of tuples containing a file key and a `Path` object into the expected HTTPX-compatible file tuple structure.
    """
    result = await async_to_httpx_files([("file", readme_path)])
    print(result)
    assert result == IsList(IsTuple("file", IsTuple("README.md", IsBytes())))


def test_string_not_allowed() -> None:
    """
    Test that passing a string as a file input to `to_httpx_files` raises a TypeError with the expected error message.
    """
    with pytest.raises(TypeError, match="Expected file types input to be a FileContent type or to be a tuple"):
        to_httpx_files(
            {
                "file": "foo",  # type: ignore
            }
        )
