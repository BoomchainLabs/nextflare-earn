from __future__ import annotations

import io
import os
import pathlib
from typing import overload
from typing_extensions import TypeGuard

import anyio

from ._types import (
    FileTypes,
    FileContent,
    RequestFiles,
    HttpxFileTypes,
    Base64FileInput,
    HttpxFileContent,
    HttpxRequestFiles,
)
from ._utils import is_tuple_t, is_mapping_t, is_sequence_t


def is_base64_file_input(obj: object) -> TypeGuard[Base64FileInput]:
    """
    Determine if the object is a base64 file input, specifically an IO stream or a path-like object.
    
    Returns:
        TypeGuard[Base64FileInput]: True if the object is an instance of io.IOBase or os.PathLike, indicating it can be treated as a base64 file input.
    """
    return isinstance(obj, io.IOBase) or isinstance(obj, os.PathLike)


def is_file_content(obj: object) -> TypeGuard[FileContent]:
    """
    Determine whether the given object is valid file content for HTTPX file uploads.
    
    Returns:
        TypeGuard[FileContent]: True if the object is bytes, a tuple, an IO stream, or a path-like object; otherwise, False.
    """
    return (
        isinstance(obj, bytes) or isinstance(obj, tuple) or isinstance(obj, io.IOBase) or isinstance(obj, os.PathLike)
    )


def assert_is_file_content(obj: object, *, key: str | None = None) -> None:
    """
    Raise a RuntimeError if the object is not valid file content.
    
    Parameters:
        key (str | None): Optional identifier to include in the error message for context.
    """
    if not is_file_content(obj):
        prefix = f"Expected entry at `{key}`" if key is not None else f"Expected file input `{obj!r}`"
        raise RuntimeError(
            f"{prefix} to be bytes, an io.IOBase instance, PathLike or a tuple but received {type(obj)} instead."
        ) from None


@overload
def to_httpx_files(files: None) -> None: """
Return None when no file input is provided.
"""
...


@overload
def to_httpx_files(files: RequestFiles) -> HttpxRequestFiles: """
Convert file input mappings or sequences into HTTPX-compatible request files.

Parameters:
	files: A mapping or sequence representing files to be uploaded, where each value or tuple element can be a path, bytes, IO stream, or a tuple describing file content.

Returns:
	An HTTPX-compatible mapping or sequence of file tuples suitable for use with HTTPX request file uploads.

Raises:
	TypeError: If the input is neither a mapping nor a sequence.
"""
...


def to_httpx_files(files: RequestFiles | None) -> HttpxRequestFiles | None:
    """
    Convert file input mappings or sequences into HTTPX-compatible request files.
    
    Parameters:
    	files: A mapping or sequence of file inputs to be transformed.
    
    Returns:
    	An HTTPX-compatible mapping or sequence of file tuples, or None if input is None.
    
    Raises:
    	TypeError: If the input is neither a mapping nor a sequence.
    """
    if files is None:
        return None

    if is_mapping_t(files):
        files = {key: _transform_file(file) for key, file in files.items()}
    elif is_sequence_t(files):
        files = [(key, _transform_file(file)) for key, file in files]
    else:
        raise TypeError(f"Unexpected file type input {type(files)}, expected mapping or sequence")

    return files


def _transform_file(file: FileTypes) -> HttpxFileTypes:
    """
    Convert a file input into an HTTPX-compatible file type for synchronous requests.
    
    If the input is a path-like object, reads its bytes and returns a tuple of filename and content. If the input is a tuple, recursively transforms its content. Raises TypeError for unsupported input types.
    
    Returns:
        An HTTPX-compatible file type suitable for use in request file uploads.
    """
    if is_file_content(file):
        if isinstance(file, os.PathLike):
            path = pathlib.Path(file)
            return (path.name, path.read_bytes())

        return file

    if is_tuple_t(file):
        return (file[0], _read_file_content(file[1]), *file[2:])

    raise TypeError(f"Expected file types input to be a FileContent type or to be a tuple")


def _read_file_content(file: FileContent) -> HttpxFileContent:
    """
    Return the file content as bytes if given a path-like object; otherwise, return the input unchanged.
    """
    if isinstance(file, os.PathLike):
        return pathlib.Path(file).read_bytes()
    return file


@overload
async def async_to_httpx_files(files: None) -> None: """
Asynchronously returns None when no file input is provided.
"""
...


@overload
async def async_to_httpx_files(files: RequestFiles) -> HttpxRequestFiles: """
Asynchronously converts file inputs into HTTPX-compatible request files.

Supports both mappings and sequences of files, transforming each entry into the format expected by HTTPX for file uploads. Reads file content asynchronously when necessary.

Returns:
    HTTPX-compatible request files, or None if no files are provided.

Raises:
    TypeError: If the input is not a mapping or sequence of files.
"""
...


async def async_to_httpx_files(files: RequestFiles | None) -> HttpxRequestFiles | None:
    """
    Asynchronously converts file inputs into HTTPX-compatible request files.
    
    If the input is a mapping, each file value is transformed asynchronously; if a sequence, each tuple's file element is transformed. Returns None if input is None.
    
    Returns:
        A mapping or sequence of HTTPX-compatible file tuples, or None if no files are provided.
    
    Raises:
        TypeError: If the input is not a mapping or sequence.
    """
    if files is None:
        return None

    if is_mapping_t(files):
        files = {key: await _async_transform_file(file) for key, file in files.items()}
    elif is_sequence_t(files):
        files = [(key, await _async_transform_file(file)) for key, file in files]
    else:
        raise TypeError("Unexpected file type input {type(files)}, expected mapping or sequence")

    return files


async def _async_transform_file(file: FileTypes) -> HttpxFileTypes:
    """
    Asynchronously transforms a file input into an HTTPX-compatible file type.
    
    If the input is a path-like object, reads its bytes asynchronously and returns a tuple of the filename and bytes. If the input is a tuple, recursively transforms its content. Raises a TypeError if the input is not valid file content or a tuple.
    """
    if is_file_content(file):
        if isinstance(file, os.PathLike):
            path = anyio.Path(file)
            return (path.name, await path.read_bytes())

        return file

    if is_tuple_t(file):
        return (file[0], await _async_read_file_content(file[1]), *file[2:])

    raise TypeError(f"Expected file types input to be a FileContent type or to be a tuple")


async def _async_read_file_content(file: FileContent) -> HttpxFileContent:
    """
    Asynchronously reads bytes from a path-like file content, or returns the input if it is already in a compatible format.
    
    If the input is a path-like object, reads and returns its bytes asynchronously. Otherwise, returns the input unchanged.
    """
    if isinstance(file, os.PathLike):
        return await anyio.Path(file).read_bytes()

    return file
