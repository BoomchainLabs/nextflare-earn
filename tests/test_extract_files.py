from __future__ import annotations

from typing import Sequence

import pytest

from earn_app._types import FileTypes
from earn_app._utils import extract_files


def test_removes_files_from_input() -> None:
    """
    Test that `extract_files` correctly extracts and removes file-like objects from nested dictionaries at specified key paths.
    
    Verifies that:
    - No files are extracted and input remains unchanged when no paths are provided.
    - Files at given paths are extracted as (key path, bytes) tuples and removed from the input.
    - Non-file data is preserved in the input after extraction.
    """
    query = {"foo": "bar"}
    assert extract_files(query, paths=[]) == []
    assert query == {"foo": "bar"}

    query2 = {"foo": b"Bar", "hello": "world"}
    assert extract_files(query2, paths=[["foo"]]) == [("foo", b"Bar")]
    assert query2 == {"hello": "world"}

    query3 = {"foo": {"foo": {"bar": b"Bar"}}, "hello": "world"}
    assert extract_files(query3, paths=[["foo", "foo", "bar"]]) == [("foo[foo][bar]", b"Bar")]
    assert query3 == {"foo": {"foo": {}}, "hello": "world"}

    query4 = {"foo": {"bar": b"Bar", "baz": "foo"}, "hello": "world"}
    assert extract_files(query4, paths=[["foo", "bar"]]) == [("foo[bar]", b"Bar")]
    assert query4 == {"hello": "world", "foo": {"baz": "foo"}}


def test_multiple_files() -> None:
    """
    Tests that extract_files correctly extracts multiple files from a list of dictionaries at the specified path and removes the file entries from the original input.
    """
    query = {"documents": [{"file": b"My first file"}, {"file": b"My second file"}]}
    assert extract_files(query, paths=[["documents", "<array>", "file"]]) == [
        ("documents[][file]", b"My first file"),
        ("documents[][file]", b"My second file"),
    ]
    assert query == {"documents": [{}, {}]}


@pytest.mark.parametrize(
    "query,paths,expected",
    [
        [
            {"foo": {"bar": "baz"}},
            [["foo", "<array>", "bar"]],
            [],
        ],
        [
            {"foo": ["bar", "baz"]},
            [["foo", "bar"]],
            [],
        ],
        [
            {"foo": {"bar": "baz"}},
            [["foo", "foo"]],
            [],
        ],
    ],
    ids=["dict expecting array", "array expecting dict", "unknown keys"],
)
def test_ignores_incorrect_paths(
    query: dict[str, object],
    paths: Sequence[Sequence[str]],
    expected: list[tuple[str, FileTypes]],
) -> None:
    """
    Test that extract_files returns an empty list and leaves the input unchanged when paths do not match the input structure.
    
    Parameters:
        query (dict): The input dictionary to search for files.
        paths (Sequence[Sequence[str]]): Key paths that do not correspond to any files in the input.
        expected (list): The expected empty list of extracted files.
    """
    assert extract_files(query, paths=paths) == expected
