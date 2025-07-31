# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import gc
import os
import sys
import json
import time
import asyncio
import inspect
import subprocess
import tracemalloc
from typing import Any, Union, cast
from textwrap import dedent
from unittest import mock
from typing_extensions import Literal

import httpx
import pytest
from respx import MockRouter
from pydantic import ValidationError

from earn_app import EarnApp, AsyncEarnApp, APIResponseValidationError
from earn_app._types import Omit
from earn_app._models import BaseModel, FinalRequestOptions
from earn_app._exceptions import EarnAppError, APIStatusError, APITimeoutError, APIResponseValidationError
from earn_app._base_client import (
    DEFAULT_TIMEOUT,
    HTTPX_DEFAULT_TIMEOUT,
    BaseClient,
    DefaultHttpxClient,
    DefaultAsyncHttpxClient,
    make_request_options,
)

from .utils import update_env

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")
api_key = "My API Key"


def _get_params(client: BaseClient[Any, Any]) -> dict[str, str]:
    """
    Builds a GET request to the `/foo` endpoint using the provided client and returns its query parameters as a dictionary.
    
    Parameters:
    	client (BaseClient): The API client used to build the request.
    
    Returns:
    	Dict[str, str]: A dictionary of query parameter names and values from the constructed request.
    """
    request = client._build_request(FinalRequestOptions(method="get", url="/foo"))
    url = httpx.URL(request.url)
    return dict(url.params)


def _low_retry_timeout(*_args: Any, **_kwargs: Any) -> float:
    """
    Return a fixed low retry timeout value of 0.1 seconds.
    """
    return 0.1


def _get_open_connections(client: EarnApp | AsyncEarnApp) -> int:
    """
    Return the number of open HTTP connections in the client's underlying transport pool.
    
    Parameters:
    	client (EarnApp | AsyncEarnApp): The API client instance to inspect.
    
    Returns:
    	int: The count of open HTTP connections.
    """
    transport = client._client._transport
    assert isinstance(transport, httpx.HTTPTransport) or isinstance(transport, httpx.AsyncHTTPTransport)

    pool = transport._pool
    return len(pool._requests)


class TestEarnApp:
    client = EarnApp(base_url=base_url, api_key=api_key, _strict_response_validation=True)

    @pytest.mark.respx(base_url=base_url)
    def test_raw_response(self, respx_mock: MockRouter) -> None:
        """
        Tests that the client returns a raw httpx.Response object with correct status code and JSON content when requested.
        """
        respx_mock.post("/foo").mock(return_value=httpx.Response(200, json={"foo": "bar"}))

        response = self.client.post("/foo", cast_to=httpx.Response)
        assert response.status_code == 200
        assert isinstance(response, httpx.Response)
        assert response.json() == {"foo": "bar"}

    @pytest.mark.respx(base_url=base_url)
    def test_raw_response_for_binary(self, respx_mock: MockRouter) -> None:
        """
        Tests that a POST request returning binary content with a JSON payload is correctly parsed as JSON when using the raw httpx.Response type.
        """
        respx_mock.post("/foo").mock(
            return_value=httpx.Response(200, headers={"Content-Type": "application/binary"}, content='{"foo": "bar"}')
        )

        response = self.client.post("/foo", cast_to=httpx.Response)
        assert response.status_code == 200
        assert isinstance(response, httpx.Response)
        assert response.json() == {"foo": "bar"}

    def test_copy(self) -> None:
        """
        Tests that the client `.copy()` method creates a distinct instance and allows overriding the API key without affecting the original client.
        """
        copied = self.client.copy()
        assert id(copied) != id(self.client)

        copied = self.client.copy(api_key="another My API Key")
        assert copied.api_key == "another My API Key"
        assert self.client.api_key == "My API Key"

    def test_copy_default_options(self) -> None:
        # options that have a default are overridden correctly
        """
        Test that copying the client with overridden default options correctly updates the new instance without affecting the original.
        
        Verifies that options like `max_retries` and `timeout` are properly set on the copied client, and that the original client's options remain unchanged.
        """
        copied = self.client.copy(max_retries=7)
        assert copied.max_retries == 7
        assert self.client.max_retries == 2

        copied2 = copied.copy(max_retries=6)
        assert copied2.max_retries == 6
        assert copied.max_retries == 7

        # timeout
        assert isinstance(self.client.timeout, httpx.Timeout)
        copied = self.client.copy(timeout=None)
        assert copied.timeout is None
        assert isinstance(self.client.timeout, httpx.Timeout)

    def test_copy_default_headers(self) -> None:
        """
        Tests copying a client with default headers, verifying merging, overriding, and exclusivity of header options.
        
        Ensures that copying the client preserves or updates default headers as specified, and that mutually exclusive arguments raise an error.
        """
        client = EarnApp(
            base_url=base_url, api_key=api_key, _strict_response_validation=True, default_headers={"X-Foo": "bar"}
        )
        assert client.default_headers["X-Foo"] == "bar"

        # does not override the already given value when not specified
        copied = client.copy()
        assert copied.default_headers["X-Foo"] == "bar"

        # merges already given headers
        copied = client.copy(default_headers={"X-Bar": "stainless"})
        assert copied.default_headers["X-Foo"] == "bar"
        assert copied.default_headers["X-Bar"] == "stainless"

        # uses new values for any already given headers
        copied = client.copy(default_headers={"X-Foo": "stainless"})
        assert copied.default_headers["X-Foo"] == "stainless"

        # set_default_headers

        # completely overrides already set values
        copied = client.copy(set_default_headers={})
        assert copied.default_headers.get("X-Foo") is None

        copied = client.copy(set_default_headers={"X-Bar": "Robert"})
        assert copied.default_headers["X-Bar"] == "Robert"

        with pytest.raises(
            ValueError,
            match="`default_headers` and `set_default_headers` arguments are mutually exclusive",
        ):
            client.copy(set_default_headers={}, default_headers={"X-Foo": "Bar"})

    def test_copy_default_query(self) -> None:
        """
        Tests the behavior of copying an EarnApp client with respect to default query parameters.
        
        Verifies that copying preserves, merges, overrides, or replaces default query parameters according to the provided arguments, and that mutually exclusive arguments raise an error.
        """
        client = EarnApp(
            base_url=base_url, api_key=api_key, _strict_response_validation=True, default_query={"foo": "bar"}
        )
        assert _get_params(client)["foo"] == "bar"

        # does not override the already given value when not specified
        copied = client.copy()
        assert _get_params(copied)["foo"] == "bar"

        # merges already given params
        copied = client.copy(default_query={"bar": "stainless"})
        params = _get_params(copied)
        assert params["foo"] == "bar"
        assert params["bar"] == "stainless"

        # uses new values for any already given headers
        copied = client.copy(default_query={"foo": "stainless"})
        assert _get_params(copied)["foo"] == "stainless"

        # set_default_query

        # completely overrides already set values
        copied = client.copy(set_default_query={})
        assert _get_params(copied) == {}

        copied = client.copy(set_default_query={"bar": "Robert"})
        assert _get_params(copied)["bar"] == "Robert"

        with pytest.raises(
            ValueError,
            # TODO: update
            match="`default_query` and `set_default_query` arguments are mutually exclusive",
        ):
            client.copy(set_default_query={}, default_query={"foo": "Bar"})

    def test_copy_signature(self) -> None:
        # ensure the same parameters that can be passed to the client are defined in the `.copy()` method
        """
        Verifies that the `.copy()` method of the client defines all parameters present in the client constructor, except for explicitly excluded ones.
        """
        init_signature = inspect.signature(
            # mypy doesn't like that we access the `__init__` property.
            self.client.__init__,  # type: ignore[misc]
        )
        copy_signature = inspect.signature(self.client.copy)
        exclude_params = {"transport", "proxies", "_strict_response_validation"}

        for name in init_signature.parameters.keys():
            if name in exclude_params:
                continue

            copy_param = copy_signature.parameters.get(name)
            assert copy_param is not None, f"copy() signature is missing the {name} param"

    def test_copy_build_request(self) -> None:
        """
        Detects memory leaks when repeatedly building requests with a copied client instance.
        
        This test builds requests multiple times using a copied client, compares memory snapshots before and after, and asserts that no unexpected memory allocations persist, indicating the absence of memory leaks in the request-building process.
        """
        options = FinalRequestOptions(method="get", url="/foo")

        def build_request(options: FinalRequestOptions) -> None:
            """
            Builds an HTTP request using the provided options by delegating to a copied client instance.
            
            Parameters:
                options (FinalRequestOptions): The finalized options for building the HTTP request.
            """
            client = self.client.copy()
            client._build_request(options)

        # ensure that the machinery is warmed up before tracing starts.
        build_request(options)
        gc.collect()

        tracemalloc.start(1000)

        snapshot_before = tracemalloc.take_snapshot()

        ITERATIONS = 10
        for _ in range(ITERATIONS):
            build_request(options)

        gc.collect()
        snapshot_after = tracemalloc.take_snapshot()

        tracemalloc.stop()

        def add_leak(leaks: list[tracemalloc.StatisticDiff], diff: tracemalloc.StatisticDiff) -> None:
            """
            Appends a memory leak statistic to the leaks list if it meets specific criteria.
            
            Only statistics representing persistent memory allocations per iteration and not originating from known false-positive sources are considered.
            """
            if diff.count == 0:
                # Avoid false positives by considering only leaks (i.e. allocations that persist).
                return

            if diff.count % ITERATIONS != 0:
                # Avoid false positives by considering only leaks that appear per iteration.
                return

            for frame in diff.traceback:
                if any(
                    frame.filename.endswith(fragment)
                    for fragment in [
                        # to_raw_response_wrapper leaks through the @functools.wraps() decorator.
                        #
                        # removing the decorator fixes the leak for reasons we don't understand.
                        "earn_app/_legacy_response.py",
                        "earn_app/_response.py",
                        # pydantic.BaseModel.model_dump || pydantic.BaseModel.dict leak memory for some reason.
                        "earn_app/_compat.py",
                        # Standard library leaks we don't care about.
                        "/logging/__init__.py",
                    ]
                ):
                    return

            leaks.append(diff)

        leaks: list[tracemalloc.StatisticDiff] = []
        for diff in snapshot_after.compare_to(snapshot_before, "traceback"):
            add_leak(leaks, diff)
        if leaks:
            for leak in leaks:
                print("MEMORY LEAK:", leak)
                for frame in leak.traceback:
                    print(frame)
            raise AssertionError()

    def test_request_timeout(self) -> None:
        """
        Test that the request timeout is set correctly from both the client default and per-request options.
        """
        request = self.client._build_request(FinalRequestOptions(method="get", url="/foo"))
        timeout = httpx.Timeout(**request.extensions["timeout"])  # type: ignore
        assert timeout == DEFAULT_TIMEOUT

        request = self.client._build_request(
            FinalRequestOptions(method="get", url="/foo", timeout=httpx.Timeout(100.0))
        )
        timeout = httpx.Timeout(**request.extensions["timeout"])  # type: ignore
        assert timeout == httpx.Timeout(100.0)

    def test_client_timeout_option(self) -> None:
        """
        Tests that the client-level timeout option is correctly applied to built requests.
        """
        client = EarnApp(base_url=base_url, api_key=api_key, _strict_response_validation=True, timeout=httpx.Timeout(0))

        request = client._build_request(FinalRequestOptions(method="get", url="/foo"))
        timeout = httpx.Timeout(**request.extensions["timeout"])  # type: ignore
        assert timeout == httpx.Timeout(0)

    def test_http_client_timeout_option(self) -> None:
        # custom timeout given to the httpx client should be used
        """
        Test that the client's timeout behavior correctly respects custom, omitted, and default timeout settings when using a custom httpx.Client.
        """
        with httpx.Client(timeout=None) as http_client:
            client = EarnApp(
                base_url=base_url, api_key=api_key, _strict_response_validation=True, http_client=http_client
            )

            request = client._build_request(FinalRequestOptions(method="get", url="/foo"))
            timeout = httpx.Timeout(**request.extensions["timeout"])  # type: ignore
            assert timeout == httpx.Timeout(None)

        # no timeout given to the httpx client should not use the httpx default
        with httpx.Client() as http_client:
            client = EarnApp(
                base_url=base_url, api_key=api_key, _strict_response_validation=True, http_client=http_client
            )

            request = client._build_request(FinalRequestOptions(method="get", url="/foo"))
            timeout = httpx.Timeout(**request.extensions["timeout"])  # type: ignore
            assert timeout == DEFAULT_TIMEOUT

        # explicitly passing the default timeout currently results in it being ignored
        with httpx.Client(timeout=HTTPX_DEFAULT_TIMEOUT) as http_client:
            client = EarnApp(
                base_url=base_url, api_key=api_key, _strict_response_validation=True, http_client=http_client
            )

            request = client._build_request(FinalRequestOptions(method="get", url="/foo"))
            timeout = httpx.Timeout(**request.extensions["timeout"])  # type: ignore
            assert timeout == DEFAULT_TIMEOUT  # our default

    async def test_invalid_http_client(self) -> None:
        """
        Test that passing an async HTTP client to the synchronous EarnApp client raises a TypeError.
        """
        with pytest.raises(TypeError, match="Invalid `http_client` arg"):
            async with httpx.AsyncClient() as http_client:
                EarnApp(
                    base_url=base_url,
                    api_key=api_key,
                    _strict_response_validation=True,
                    http_client=cast(Any, http_client),
                )

    def test_default_headers_option(self) -> None:
        """
        Tests that default headers are correctly included in requests and can be overridden by client configuration.
        """
        client = EarnApp(
            base_url=base_url, api_key=api_key, _strict_response_validation=True, default_headers={"X-Foo": "bar"}
        )
        request = client._build_request(FinalRequestOptions(method="get", url="/foo"))
        assert request.headers.get("x-foo") == "bar"
        assert request.headers.get("x-stainless-lang") == "python"

        client2 = EarnApp(
            base_url=base_url,
            api_key=api_key,
            _strict_response_validation=True,
            default_headers={
                "X-Foo": "stainless",
                "X-Stainless-Lang": "my-overriding-header",
            },
        )
        request = client2._build_request(FinalRequestOptions(method="get", url="/foo"))
        assert request.headers.get("x-foo") == "stainless"
        assert request.headers.get("x-stainless-lang") == "my-overriding-header"

    def test_validate_headers(self) -> None:
        """
        Tests that the Authorization header is set when an API key is provided and that an error is raised if the API key is missing.
        """
        client = EarnApp(base_url=base_url, api_key=api_key, _strict_response_validation=True)
        request = client._build_request(FinalRequestOptions(method="get", url="/foo"))
        assert request.headers.get("Authorization") == f"Bearer {api_key}"

        with pytest.raises(EarnAppError):
            with update_env(**{"EARN_APP_API_KEY": Omit()}):
                client2 = EarnApp(base_url=base_url, api_key=None, _strict_response_validation=True)
            _ = client2

    def test_default_query_option(self) -> None:
        """
        Tests that the client's default query parameters are included in requests and can be overridden by per-request parameters.
        """
        client = EarnApp(
            base_url=base_url, api_key=api_key, _strict_response_validation=True, default_query={"query_param": "bar"}
        )
        request = client._build_request(FinalRequestOptions(method="get", url="/foo"))
        url = httpx.URL(request.url)
        assert dict(url.params) == {"query_param": "bar"}

        request = client._build_request(
            FinalRequestOptions(
                method="get",
                url="/foo",
                params={"foo": "baz", "query_param": "overridden"},
            )
        )
        url = httpx.URL(request.url)
        assert dict(url.params) == {"foo": "baz", "query_param": "overridden"}

    def test_request_extra_json(self) -> None:
        """
        Tests that extra JSON data provided in request options is merged with or overrides the main JSON payload when building a request.
        
        Verifies that:
        - Both `json_data` and `extra_json` are merged in the request body.
        - If only `extra_json` is provided, it becomes the request body.
        - When keys overlap, values from `extra_json` take precedence over those in `json_data`.
        """
        request = self.client._build_request(
            FinalRequestOptions(
                method="post",
                url="/foo",
                json_data={"foo": "bar"},
                extra_json={"baz": False},
            ),
        )
        data = json.loads(request.content.decode("utf-8"))
        assert data == {"foo": "bar", "baz": False}

        request = self.client._build_request(
            FinalRequestOptions(
                method="post",
                url="/foo",
                extra_json={"baz": False},
            ),
        )
        data = json.loads(request.content.decode("utf-8"))
        assert data == {"baz": False}

        # `extra_json` takes priority over `json_data` when keys clash
        request = self.client._build_request(
            FinalRequestOptions(
                method="post",
                url="/foo",
                json_data={"foo": "bar", "baz": True},
                extra_json={"baz": None},
            ),
        )
        data = json.loads(request.content.decode("utf-8"))
        assert data == {"foo": "bar", "baz": None}

    def test_request_extra_headers(self) -> None:
        """
        Tests that extra headers provided in a request are included and take precedence over default headers when keys overlap.
        """
        request = self.client._build_request(
            FinalRequestOptions(
                method="post",
                url="/foo",
                **make_request_options(extra_headers={"X-Foo": "Foo"}),
            ),
        )
        assert request.headers.get("X-Foo") == "Foo"

        # `extra_headers` takes priority over `default_headers` when keys clash
        request = self.client.with_options(default_headers={"X-Bar": "true"})._build_request(
            FinalRequestOptions(
                method="post",
                url="/foo",
                **make_request_options(
                    extra_headers={"X-Bar": "false"},
                ),
            ),
        )
        assert request.headers.get("X-Bar") == "false"

    def test_request_extra_query(self) -> None:
        """
        Tests that extra query parameters are correctly merged into the request, with `extra_query` taking precedence over `query` when keys overlap.
        """
        request = self.client._build_request(
            FinalRequestOptions(
                method="post",
                url="/foo",
                **make_request_options(
                    extra_query={"my_query_param": "Foo"},
                ),
            ),
        )
        params = dict(request.url.params)
        assert params == {"my_query_param": "Foo"}

        # if both `query` and `extra_query` are given, they are merged
        request = self.client._build_request(
            FinalRequestOptions(
                method="post",
                url="/foo",
                **make_request_options(
                    query={"bar": "1"},
                    extra_query={"foo": "2"},
                ),
            ),
        )
        params = dict(request.url.params)
        assert params == {"bar": "1", "foo": "2"}

        # `extra_query` takes priority over `query` when keys clash
        request = self.client._build_request(
            FinalRequestOptions(
                method="post",
                url="/foo",
                **make_request_options(
                    query={"foo": "1"},
                    extra_query={"foo": "2"},
                ),
            ),
        )
        params = dict(request.url.params)
        assert params == {"foo": "2"}

    def test_multipart_repeating_array(self, client: EarnApp) -> None:
        """
        Tests that building a multipart/form-data request with an array field and a file correctly formats the multipart body with repeated array keys.
        """
        request = client._build_request(
            FinalRequestOptions.construct(
                method="get",
                url="/foo",
                headers={"Content-Type": "multipart/form-data; boundary=6b7ba517decee4a450543ea6ae821c82"},
                json_data={"array": ["foo", "bar"]},
                files=[("foo.txt", b"hello world")],
            )
        )

        assert request.read().split(b"\r\n") == [
            b"--6b7ba517decee4a450543ea6ae821c82",
            b'Content-Disposition: form-data; name="array[]"',
            b"",
            b"foo",
            b"--6b7ba517decee4a450543ea6ae821c82",
            b'Content-Disposition: form-data; name="array[]"',
            b"",
            b"bar",
            b"--6b7ba517decee4a450543ea6ae821c82",
            b'Content-Disposition: form-data; name="foo.txt"; filename="upload"',
            b"Content-Type: application/octet-stream",
            b"",
            b"hello world",
            b"--6b7ba517decee4a450543ea6ae821c82--",
            b"",
        ]

    @pytest.mark.respx(base_url=base_url)
    def test_basic_union_response(self, respx_mock: MockRouter) -> None:
        """
        Tests that the client correctly parses a response into the appropriate model when casting to a union of Pydantic models.
        
        Asserts that when the response JSON matches the structure of one model in the union, the response is instantiated as that model.
        """
        class Model1(BaseModel):
            name: str

        class Model2(BaseModel):
            foo: str

        respx_mock.get("/foo").mock(return_value=httpx.Response(200, json={"foo": "bar"}))

        response = self.client.get("/foo", cast_to=cast(Any, Union[Model1, Model2]))
        assert isinstance(response, Model2)
        assert response.foo == "bar"

    @pytest.mark.respx(base_url=base_url)
    def test_union_response_different_types(self, respx_mock: MockRouter) -> None:
        """
        Tests that the client correctly casts responses to the appropriate model in a union of Pydantic models with overlapping field names but different types, based on the response JSON value type.
        """

        class Model1(BaseModel):
            foo: int

        class Model2(BaseModel):
            foo: str

        respx_mock.get("/foo").mock(return_value=httpx.Response(200, json={"foo": "bar"}))

        response = self.client.get("/foo", cast_to=cast(Any, Union[Model1, Model2]))
        assert isinstance(response, Model2)
        assert response.foo == "bar"

        respx_mock.get("/foo").mock(return_value=httpx.Response(200, json={"foo": 1}))

        response = self.client.get("/foo", cast_to=cast(Any, Union[Model1, Model2]))
        assert isinstance(response, Model1)
        assert response.foo == 1

    @pytest.mark.respx(base_url=base_url)
    def test_non_application_json_content_type_for_json_data(self, respx_mock: MockRouter) -> None:
        """
        Tests that a response with a non-JSON content type but containing JSON data is correctly parsed and cast to the specified model.
        """

        class Model(BaseModel):
            foo: int

        respx_mock.get("/foo").mock(
            return_value=httpx.Response(
                200,
                content=json.dumps({"foo": 2}),
                headers={"Content-Type": "application/text"},
            )
        )

        response = self.client.get("/foo", cast_to=Model)
        assert isinstance(response, Model)
        assert response.foo == 2

    def test_base_url_setter(self) -> None:
        """
        Test that setting the base_url property on the client normalizes it with a trailing slash.
        """
        client = EarnApp(base_url="https://example.com/from_init", api_key=api_key, _strict_response_validation=True)
        assert client.base_url == "https://example.com/from_init/"

        client.base_url = "https://example.com/from_setter"  # type: ignore[assignment]

        assert client.base_url == "https://example.com/from_setter/"

    def test_base_url_env(self) -> None:
        """
        Tests that the client correctly resolves the base URL from the environment variable, enforces explicit base_url=None when using the environment argument, and defaults to the correct URL for a given environment.
        """
        with update_env(EARN_APP_BASE_URL="http://localhost:5000/from/env"):
            client = EarnApp(api_key=api_key, _strict_response_validation=True)
            assert client.base_url == "http://localhost:5000/from/env/"

        # explicit environment arg requires explicitness
        with update_env(EARN_APP_BASE_URL="http://localhost:5000/from/env"):
            with pytest.raises(ValueError, match=r"you must pass base_url=None"):
                EarnApp(api_key=api_key, _strict_response_validation=True, environment="production")

            client = EarnApp(base_url=None, api_key=api_key, _strict_response_validation=True, environment="production")
            assert str(client.base_url).startswith("https://api.slerfhub.xyz/api")

    @pytest.mark.parametrize(
        "client",
        [
            EarnApp(base_url="http://localhost:5000/custom/path/", api_key=api_key, _strict_response_validation=True),
            EarnApp(
                base_url="http://localhost:5000/custom/path/",
                api_key=api_key,
                _strict_response_validation=True,
                http_client=httpx.Client(),
            ),
        ],
        ids=["standard", "custom http client"],
    )
    def test_base_url_trailing_slash(self, client: EarnApp) -> None:
        """
        Tests that the client correctly appends a relative path to a base URL ending with a trailing slash.
        """
        request = client._build_request(
            FinalRequestOptions(
                method="post",
                url="/foo",
                json_data={"foo": "bar"},
            ),
        )
        assert request.url == "http://localhost:5000/custom/path/foo"

    @pytest.mark.parametrize(
        "client",
        [
            EarnApp(base_url="http://localhost:5000/custom/path/", api_key=api_key, _strict_response_validation=True),
            EarnApp(
                base_url="http://localhost:5000/custom/path/",
                api_key=api_key,
                _strict_response_validation=True,
                http_client=httpx.Client(),
            ),
        ],
        ids=["standard", "custom http client"],
    )
    def test_base_url_no_trailing_slash(self, client: EarnApp) -> None:
        """
        Tests that the client correctly concatenates the base URL without a trailing slash to a relative request path.
        """
        request = client._build_request(
            FinalRequestOptions(
                method="post",
                url="/foo",
                json_data={"foo": "bar"},
            ),
        )
        assert request.url == "http://localhost:5000/custom/path/foo"

    @pytest.mark.parametrize(
        "client",
        [
            EarnApp(base_url="http://localhost:5000/custom/path/", api_key=api_key, _strict_response_validation=True),
            EarnApp(
                base_url="http://localhost:5000/custom/path/",
                api_key=api_key,
                _strict_response_validation=True,
                http_client=httpx.Client(),
            ),
        ],
        ids=["standard", "custom http client"],
    )
    def test_absolute_request_url(self, client: EarnApp) -> None:
        """
        Tests that an absolute URL provided in a request is used as-is, bypassing the client's base URL.
        """
        request = client._build_request(
            FinalRequestOptions(
                method="post",
                url="https://myapi.com/foo",
                json_data={"foo": "bar"},
            ),
        )
        assert request.url == "https://myapi.com/foo"

    def test_copied_client_does_not_close_http(self) -> None:
        """
        Verify that copying a client does not close the original client's underlying HTTP connection.
        
        Ensures that deleting a copied client instance does not affect the open state of the original client.
        """
        client = EarnApp(base_url=base_url, api_key=api_key, _strict_response_validation=True)
        assert not client.is_closed()

        copied = client.copy()
        assert copied is not client

        del copied

        assert not client.is_closed()

    def test_client_context_manager(self) -> None:
        """
        Tests that the client supports the context manager protocol, remaining open within the context and closing automatically upon exit.
        """
        client = EarnApp(base_url=base_url, api_key=api_key, _strict_response_validation=True)
        with client as c2:
            assert c2 is client
            assert not c2.is_closed()
            assert not client.is_closed()
        assert client.is_closed()

    @pytest.mark.respx(base_url=base_url)
    def test_client_response_validation_error(self, respx_mock: MockRouter) -> None:
        """
        Tests that an APIResponseValidationError is raised when the response JSON does not match the expected model schema, and that the underlying cause is a Pydantic ValidationError.
        """
        class Model(BaseModel):
            foo: str

        respx_mock.get("/foo").mock(return_value=httpx.Response(200, json={"foo": {"invalid": True}}))

        with pytest.raises(APIResponseValidationError) as exc:
            self.client.get("/foo", cast_to=Model)

        assert isinstance(exc.value.__cause__, ValidationError)

    def test_client_max_retries_validation(self) -> None:
        """
        Test that initializing the client with `max_retries=None` raises a TypeError.
        """
        with pytest.raises(TypeError, match=r"max_retries cannot be None"):
            EarnApp(base_url=base_url, api_key=api_key, _strict_response_validation=True, max_retries=cast(Any, None))

    @pytest.mark.respx(base_url=base_url)
    def test_received_text_for_expected_json(self, respx_mock: MockRouter) -> None:
        """
        Tests handling of text responses when JSON is expected, verifying strict and non-strict response validation modes.
        
        Raises:
            APIResponseValidationError: If strict response validation is enabled and the response is not valid JSON.
        
        Asserts that with strict validation, a non-JSON response raises an error, and with non-strict validation, the raw text is returned.
        """
        class Model(BaseModel):
            name: str

        respx_mock.get("/foo").mock(return_value=httpx.Response(200, text="my-custom-format"))

        strict_client = EarnApp(base_url=base_url, api_key=api_key, _strict_response_validation=True)

        with pytest.raises(APIResponseValidationError):
            strict_client.get("/foo", cast_to=Model)

        client = EarnApp(base_url=base_url, api_key=api_key, _strict_response_validation=False)

        response = client.get("/foo", cast_to=Model)
        assert isinstance(response, str)  # type: ignore[unreachable]

    @pytest.mark.parametrize(
        "remaining_retries,retry_after,timeout",
        [
            [3, "20", 20],
            [3, "0", 0.5],
            [3, "-10", 0.5],
            [3, "60", 60],
            [3, "61", 0.5],
            [3, "Fri, 29 Sep 2023 16:26:57 GMT", 20],
            [3, "Fri, 29 Sep 2023 16:26:37 GMT", 0.5],
            [3, "Fri, 29 Sep 2023 16:26:27 GMT", 0.5],
            [3, "Fri, 29 Sep 2023 16:27:37 GMT", 60],
            [3, "Fri, 29 Sep 2023 16:27:38 GMT", 0.5],
            [3, "99999999999999999999999999999999999", 0.5],
            [3, "Zun, 29 Sep 2023 16:26:27 GMT", 0.5],
            [3, "", 0.5],
            [2, "", 0.5 * 2.0],
            [1, "", 0.5 * 4.0],
            [-1100, "", 8],  # test large number potentially overflowing
        ],
    )
    @mock.patch("time.time", mock.MagicMock(return_value=1696004797))
    def test_parse_retry_after_header(self, remaining_retries: int, retry_after: str, timeout: float) -> None:
        """
        Tests that the client correctly parses the 'Retry-After' HTTP header and calculates the appropriate retry timeout.
        
        Parameters:
            remaining_retries (int): The number of retries left for the request.
            retry_after (str): The value of the 'Retry-After' header to be parsed.
            timeout (float): The expected timeout value to compare against the calculated result.
        """
        client = EarnApp(base_url=base_url, api_key=api_key, _strict_response_validation=True)

        headers = httpx.Headers({"retry-after": retry_after})
        options = FinalRequestOptions(method="get", url="/foo", max_retries=3)
        calculated = client._calculate_retry_timeout(remaining_retries, options, headers)
        assert calculated == pytest.approx(timeout, 0.5 * 0.875)  # pyright: ignore[reportUnknownMemberType]

    @mock.patch("earn_app._base_client.BaseClient._calculate_retry_timeout", _low_retry_timeout)
    @pytest.mark.respx(base_url=base_url)
    def test_retrying_timeout_errors_doesnt_leak(self, respx_mock: MockRouter, client: EarnApp) -> None:
        """
        Tests that repeated timeout errors during a POST request do not cause HTTP connection leaks.
        
        Asserts that an `APITimeoutError` is raised when all retries fail due to timeouts, and verifies that no open HTTP connections remain after the operation.
        """
        respx_mock.post("/users").mock(side_effect=httpx.TimeoutException("Test timeout error"))

        with pytest.raises(APITimeoutError):
            client.users.with_streaming_response.create(wallet_address="walletAddress").__enter__()

        assert _get_open_connections(self.client) == 0

    @mock.patch("earn_app._base_client.BaseClient._calculate_retry_timeout", _low_retry_timeout)
    @pytest.mark.respx(base_url=base_url)
    def test_retrying_status_errors_doesnt_leak(self, respx_mock: MockRouter, client: EarnApp) -> None:
        """
        Tests that repeated HTTP 500 status errors during a request do not cause HTTP connection leaks.
        
        Asserts that an `APIStatusError` is raised when the server returns a 500 status, and verifies that all HTTP connections are properly closed after the error.
        """
        respx_mock.post("/users").mock(return_value=httpx.Response(500))

        with pytest.raises(APIStatusError):
            client.users.with_streaming_response.create(wallet_address="walletAddress").__enter__()
        assert _get_open_connections(self.client) == 0

    @pytest.mark.parametrize("failures_before_success", [0, 2, 4])
    @mock.patch("earn_app._base_client.BaseClient._calculate_retry_timeout", _low_retry_timeout)
    @pytest.mark.respx(base_url=base_url)
    @pytest.mark.parametrize("failure_mode", ["status", "exception"])
    def test_retries_taken(
        self,
        client: EarnApp,
        failures_before_success: int,
        failure_mode: Literal["status", "exception"],
        respx_mock: MockRouter,
    ) -> None:
        """
        Tests that the client retries failed requests the expected number of times before succeeding, verifying retry count headers and response metadata.
        
        Parameters:
            failures_before_success (int): Number of failures to simulate before a successful response is returned.
            failure_mode (Literal["status", "exception"]): Determines whether failures are simulated as HTTP 500 responses or raised exceptions.
        """
        client = client.with_options(max_retries=4)

        nb_retries = 0

        def retry_handler(_request: httpx.Request) -> httpx.Response:
            """
            Simulates a retry scenario by returning a failure response or raising an exception for a specified number of attempts before returning a success response.
            
            Returns:
                httpx.Response: A 500 response for failed attempts or a 200 response after the specified number of failures.
            """
            nonlocal nb_retries
            if nb_retries < failures_before_success:
                nb_retries += 1
                if failure_mode == "exception":
                    raise RuntimeError("oops")
                return httpx.Response(500)
            return httpx.Response(200)

        respx_mock.post("/users").mock(side_effect=retry_handler)

        response = client.users.with_raw_response.create(wallet_address="walletAddress")

        assert response.retries_taken == failures_before_success
        assert int(response.http_request.headers.get("x-stainless-retry-count")) == failures_before_success

    @pytest.mark.parametrize("failures_before_success", [0, 2, 4])
    @mock.patch("earn_app._base_client.BaseClient._calculate_retry_timeout", _low_retry_timeout)
    @pytest.mark.respx(base_url=base_url)
    def test_omit_retry_count_header(
        self, client: EarnApp, failures_before_success: int, respx_mock: MockRouter
    ) -> None:
        """
        Tests that omitting the retry count header results in no `x-stainless-retry-count` header being sent in the request, even after retries.
        """
        client = client.with_options(max_retries=4)

        nb_retries = 0

        def retry_handler(_request: httpx.Request) -> httpx.Response:
            """
            Simulates a retry handler that returns a 500 response for a specified number of attempts before returning a 200 response.
            
            Parameters:
                _request (httpx.Request): The incoming HTTP request (unused).
            
            Returns:
                httpx.Response: An HTTP 500 response until the retry limit is reached, then an HTTP 200 response.
            """
            nonlocal nb_retries
            if nb_retries < failures_before_success:
                nb_retries += 1
                return httpx.Response(500)
            return httpx.Response(200)

        respx_mock.post("/users").mock(side_effect=retry_handler)

        response = client.users.with_raw_response.create(
            wallet_address="walletAddress", extra_headers={"x-stainless-retry-count": Omit()}
        )

        assert len(response.http_request.headers.get_list("x-stainless-retry-count")) == 0

    @pytest.mark.parametrize("failures_before_success", [0, 2, 4])
    @mock.patch("earn_app._base_client.BaseClient._calculate_retry_timeout", _low_retry_timeout)
    @pytest.mark.respx(base_url=base_url)
    def test_overwrite_retry_count_header(
        self, client: EarnApp, failures_before_success: int, respx_mock: MockRouter
    ) -> None:
        """
        Tests that explicitly setting the retry count header in extra headers overrides the default retry count value in the request.
        """
        client = client.with_options(max_retries=4)

        nb_retries = 0

        def retry_handler(_request: httpx.Request) -> httpx.Response:
            """
            Simulates a retry handler that returns a 500 response for a specified number of attempts before returning a 200 response.
            
            Parameters:
                _request (httpx.Request): The incoming HTTP request (unused).
            
            Returns:
                httpx.Response: An HTTP 500 response until the retry limit is reached, then an HTTP 200 response.
            """
            nonlocal nb_retries
            if nb_retries < failures_before_success:
                nb_retries += 1
                return httpx.Response(500)
            return httpx.Response(200)

        respx_mock.post("/users").mock(side_effect=retry_handler)

        response = client.users.with_raw_response.create(
            wallet_address="walletAddress", extra_headers={"x-stainless-retry-count": "42"}
        )

        assert response.http_request.headers.get("x-stainless-retry-count") == "42"

    def test_proxy_environment_variables(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Test that the proxy environment variables are set correctly
        """
        Tests that the default HTTP client correctly applies proxy settings from environment variables.
        
        Parameters:
        	monkeypatch: Pytest fixture used to set environment variables for the test.
        """
        monkeypatch.setenv("HTTPS_PROXY", "https://example.org")

        client = DefaultHttpxClient()

        mounts = tuple(client._mounts.items())
        assert len(mounts) == 1
        assert mounts[0][0].pattern == "https://"

    @pytest.mark.filterwarnings("ignore:.*deprecated.*:DeprecationWarning")
    def test_default_client_creation(self) -> None:
        # Ensure that the client can be initialized without any exceptions
        """
        Tests that the default HTTP client can be created with various configuration options without raising exceptions.
        """
        DefaultHttpxClient(
            verify=True,
            cert=None,
            trust_env=True,
            http1=True,
            http2=False,
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
        )

    @pytest.mark.respx(base_url=base_url)
    def test_follow_redirects(self, respx_mock: MockRouter) -> None:
        # Test that the default follow_redirects=True allows following redirects
        """
        Tests that the client follows HTTP redirects by default when making a POST request, resulting in a successful final response.
        """
        respx_mock.post("/redirect").mock(
            return_value=httpx.Response(302, headers={"Location": f"{base_url}/redirected"})
        )
        respx_mock.get("/redirected").mock(return_value=httpx.Response(200, json={"status": "ok"}))

        response = self.client.post("/redirect", body={"key": "value"}, cast_to=httpx.Response)
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    @pytest.mark.respx(base_url=base_url)
    def test_follow_redirects_disabled(self, respx_mock: MockRouter) -> None:
        # Test that follow_redirects=False prevents following redirects
        """
        Verify that setting `follow_redirects=False` on a request prevents automatic redirect following and raises an `APIStatusError` on receiving a redirect response.
        
        Asserts that the raised error contains the original 302 response and correct `Location` header.
        """
        respx_mock.post("/redirect").mock(
            return_value=httpx.Response(302, headers={"Location": f"{base_url}/redirected"})
        )

        with pytest.raises(APIStatusError) as exc_info:
            self.client.post(
                "/redirect", body={"key": "value"}, options={"follow_redirects": False}, cast_to=httpx.Response
            )

        assert exc_info.value.response.status_code == 302
        assert exc_info.value.response.headers["Location"] == f"{base_url}/redirected"


class TestAsyncEarnApp:
    client = AsyncEarnApp(base_url=base_url, api_key=api_key, _strict_response_validation=True)

    @pytest.mark.respx(base_url=base_url)
    @pytest.mark.asyncio
    async def test_raw_response(self, respx_mock: MockRouter) -> None:
        """
        Tests that the asynchronous client returns a raw httpx.Response object with correct status code and JSON content when requested.
        """
        respx_mock.post("/foo").mock(return_value=httpx.Response(200, json={"foo": "bar"}))

        response = await self.client.post("/foo", cast_to=httpx.Response)
        assert response.status_code == 200
        assert isinstance(response, httpx.Response)
        assert response.json() == {"foo": "bar"}

    @pytest.mark.respx(base_url=base_url)
    @pytest.mark.asyncio
    async def test_raw_response_for_binary(self, respx_mock: MockRouter) -> None:
        """
        Tests that a POST request returning binary content with a JSON payload is correctly parsed as JSON when using the async client.
        
        Parameters:
            respx_mock (MockRouter): The HTTP mock router used to intercept and mock requests.
        """
        respx_mock.post("/foo").mock(
            return_value=httpx.Response(200, headers={"Content-Type": "application/binary"}, content='{"foo": "bar"}')
        )

        response = await self.client.post("/foo", cast_to=httpx.Response)
        assert response.status_code == 200
        assert isinstance(response, httpx.Response)
        assert response.json() == {"foo": "bar"}

    def test_copy(self) -> None:
        """
        Tests that the client `.copy()` method creates a distinct instance and allows overriding the API key without affecting the original client.
        """
        copied = self.client.copy()
        assert id(copied) != id(self.client)

        copied = self.client.copy(api_key="another My API Key")
        assert copied.api_key == "another My API Key"
        assert self.client.api_key == "My API Key"

    def test_copy_default_options(self) -> None:
        # options that have a default are overridden correctly
        """
        Test that copying the client with overridden default options correctly updates the new instance without affecting the original.
        
        Verifies that options like `max_retries` and `timeout` are properly set on the copied client, and that the original client's options remain unchanged.
        """
        copied = self.client.copy(max_retries=7)
        assert copied.max_retries == 7
        assert self.client.max_retries == 2

        copied2 = copied.copy(max_retries=6)
        assert copied2.max_retries == 6
        assert copied.max_retries == 7

        # timeout
        assert isinstance(self.client.timeout, httpx.Timeout)
        copied = self.client.copy(timeout=None)
        assert copied.timeout is None
        assert isinstance(self.client.timeout, httpx.Timeout)

    def test_copy_default_headers(self) -> None:
        """
        Tests copying an AsyncEarnApp client with various default header configurations.
        
        Verifies that copying preserves, merges, overrides, or replaces default headers as expected, and that mutually exclusive arguments raise a ValueError.
        """
        client = AsyncEarnApp(
            base_url=base_url, api_key=api_key, _strict_response_validation=True, default_headers={"X-Foo": "bar"}
        )
        assert client.default_headers["X-Foo"] == "bar"

        # does not override the already given value when not specified
        copied = client.copy()
        assert copied.default_headers["X-Foo"] == "bar"

        # merges already given headers
        copied = client.copy(default_headers={"X-Bar": "stainless"})
        assert copied.default_headers["X-Foo"] == "bar"
        assert copied.default_headers["X-Bar"] == "stainless"

        # uses new values for any already given headers
        copied = client.copy(default_headers={"X-Foo": "stainless"})
        assert copied.default_headers["X-Foo"] == "stainless"

        # set_default_headers

        # completely overrides already set values
        copied = client.copy(set_default_headers={})
        assert copied.default_headers.get("X-Foo") is None

        copied = client.copy(set_default_headers={"X-Bar": "Robert"})
        assert copied.default_headers["X-Bar"] == "Robert"

        with pytest.raises(
            ValueError,
            match="`default_headers` and `set_default_headers` arguments are mutually exclusive",
        ):
            client.copy(set_default_headers={}, default_headers={"X-Foo": "Bar"})

    def test_copy_default_query(self) -> None:
        """
        Tests copying an AsyncEarnApp client with default query parameters, verifying merging, overriding, and exclusivity behavior for `default_query` and `set_default_query` options.
        """
        client = AsyncEarnApp(
            base_url=base_url, api_key=api_key, _strict_response_validation=True, default_query={"foo": "bar"}
        )
        assert _get_params(client)["foo"] == "bar"

        # does not override the already given value when not specified
        copied = client.copy()
        assert _get_params(copied)["foo"] == "bar"

        # merges already given params
        copied = client.copy(default_query={"bar": "stainless"})
        params = _get_params(copied)
        assert params["foo"] == "bar"
        assert params["bar"] == "stainless"

        # uses new values for any already given headers
        copied = client.copy(default_query={"foo": "stainless"})
        assert _get_params(copied)["foo"] == "stainless"

        # set_default_query

        # completely overrides already set values
        copied = client.copy(set_default_query={})
        assert _get_params(copied) == {}

        copied = client.copy(set_default_query={"bar": "Robert"})
        assert _get_params(copied)["bar"] == "Robert"

        with pytest.raises(
            ValueError,
            # TODO: update
            match="`default_query` and `set_default_query` arguments are mutually exclusive",
        ):
            client.copy(set_default_query={}, default_query={"foo": "Bar"})

    def test_copy_signature(self) -> None:
        # ensure the same parameters that can be passed to the client are defined in the `.copy()` method
        """
        Verifies that the `.copy()` method of the client defines all parameters present in the client constructor, except for explicitly excluded ones.
        """
        init_signature = inspect.signature(
            # mypy doesn't like that we access the `__init__` property.
            self.client.__init__,  # type: ignore[misc]
        )
        copy_signature = inspect.signature(self.client.copy)
        exclude_params = {"transport", "proxies", "_strict_response_validation"}

        for name in init_signature.parameters.keys():
            if name in exclude_params:
                continue

            copy_param = copy_signature.parameters.get(name)
            assert copy_param is not None, f"copy() signature is missing the {name} param"

    def test_copy_build_request(self) -> None:
        """
        Detects memory leaks when repeatedly building requests with a copied client instance.
        
        This test builds requests multiple times using a copied client, compares memory snapshots before and after, and asserts that no unexpected memory allocations persist, indicating the absence of memory leaks in the request-building process.
        """
        options = FinalRequestOptions(method="get", url="/foo")

        def build_request(options: FinalRequestOptions) -> None:
            """
            Builds an HTTP request using the provided options by delegating to a copied client instance.
            
            Parameters:
                options (FinalRequestOptions): The finalized options for building the HTTP request.
            """
            client = self.client.copy()
            client._build_request(options)

        # ensure that the machinery is warmed up before tracing starts.
        build_request(options)
        gc.collect()

        tracemalloc.start(1000)

        snapshot_before = tracemalloc.take_snapshot()

        ITERATIONS = 10
        for _ in range(ITERATIONS):
            build_request(options)

        gc.collect()
        snapshot_after = tracemalloc.take_snapshot()

        tracemalloc.stop()

        def add_leak(leaks: list[tracemalloc.StatisticDiff], diff: tracemalloc.StatisticDiff) -> None:
            """
            Appends a memory leak statistic to the leaks list if it meets specific criteria.
            
            Only statistics representing persistent memory allocations per iteration and not originating from known false-positive sources are considered.
            """
            if diff.count == 0:
                # Avoid false positives by considering only leaks (i.e. allocations that persist).
                return

            if diff.count % ITERATIONS != 0:
                # Avoid false positives by considering only leaks that appear per iteration.
                return

            for frame in diff.traceback:
                if any(
                    frame.filename.endswith(fragment)
                    for fragment in [
                        # to_raw_response_wrapper leaks through the @functools.wraps() decorator.
                        #
                        # removing the decorator fixes the leak for reasons we don't understand.
                        "earn_app/_legacy_response.py",
                        "earn_app/_response.py",
                        # pydantic.BaseModel.model_dump || pydantic.BaseModel.dict leak memory for some reason.
                        "earn_app/_compat.py",
                        # Standard library leaks we don't care about.
                        "/logging/__init__.py",
                    ]
                ):
                    return

            leaks.append(diff)

        leaks: list[tracemalloc.StatisticDiff] = []
        for diff in snapshot_after.compare_to(snapshot_before, "traceback"):
            add_leak(leaks, diff)
        if leaks:
            for leak in leaks:
                print("MEMORY LEAK:", leak)
                for frame in leak.traceback:
                    print(frame)
            raise AssertionError()

    async def test_request_timeout(self) -> None:
        """
        Tests that the request timeout is set correctly from both the client default and per-request options for the asynchronous client.
        """
        request = self.client._build_request(FinalRequestOptions(method="get", url="/foo"))
        timeout = httpx.Timeout(**request.extensions["timeout"])  # type: ignore
        assert timeout == DEFAULT_TIMEOUT

        request = self.client._build_request(
            FinalRequestOptions(method="get", url="/foo", timeout=httpx.Timeout(100.0))
        )
        timeout = httpx.Timeout(**request.extensions["timeout"])  # type: ignore
        assert timeout == httpx.Timeout(100.0)

    async def test_client_timeout_option(self) -> None:
        """
        Tests that the async client applies the specified timeout option when building a request.
        """
        client = AsyncEarnApp(
            base_url=base_url, api_key=api_key, _strict_response_validation=True, timeout=httpx.Timeout(0)
        )

        request = client._build_request(FinalRequestOptions(method="get", url="/foo"))
        timeout = httpx.Timeout(**request.extensions["timeout"])  # type: ignore
        assert timeout == httpx.Timeout(0)

    async def test_http_client_timeout_option(self) -> None:
        # custom timeout given to the httpx client should be used
        """
        Tests that the timeout configuration from a custom async HTTP client is correctly respected or overridden by the AsyncEarnApp client.
        
        Verifies that:
        - An explicit `None` timeout on the provided HTTP client is used as-is.
        - If no timeout is set on the HTTP client, the AsyncEarnApp default timeout is applied.
        - Passing the HTTPX library's default timeout results in the AsyncEarnApp default timeout being used.
        """
        async with httpx.AsyncClient(timeout=None) as http_client:
            client = AsyncEarnApp(
                base_url=base_url, api_key=api_key, _strict_response_validation=True, http_client=http_client
            )

            request = client._build_request(FinalRequestOptions(method="get", url="/foo"))
            timeout = httpx.Timeout(**request.extensions["timeout"])  # type: ignore
            assert timeout == httpx.Timeout(None)

        # no timeout given to the httpx client should not use the httpx default
        async with httpx.AsyncClient() as http_client:
            client = AsyncEarnApp(
                base_url=base_url, api_key=api_key, _strict_response_validation=True, http_client=http_client
            )

            request = client._build_request(FinalRequestOptions(method="get", url="/foo"))
            timeout = httpx.Timeout(**request.extensions["timeout"])  # type: ignore
            assert timeout == DEFAULT_TIMEOUT

        # explicitly passing the default timeout currently results in it being ignored
        async with httpx.AsyncClient(timeout=HTTPX_DEFAULT_TIMEOUT) as http_client:
            client = AsyncEarnApp(
                base_url=base_url, api_key=api_key, _strict_response_validation=True, http_client=http_client
            )

            request = client._build_request(FinalRequestOptions(method="get", url="/foo"))
            timeout = httpx.Timeout(**request.extensions["timeout"])  # type: ignore
            assert timeout == DEFAULT_TIMEOUT  # our default

    def test_invalid_http_client(self) -> None:
        """
        Test that passing a synchronous HTTP client to the asynchronous client raises a TypeError.
        """
        with pytest.raises(TypeError, match="Invalid `http_client` arg"):
            with httpx.Client() as http_client:
                AsyncEarnApp(
                    base_url=base_url,
                    api_key=api_key,
                    _strict_response_validation=True,
                    http_client=cast(Any, http_client),
                )

    def test_default_headers_option(self) -> None:
        """
        Tests that default headers are correctly included in requests and can be overridden by specifying new values.
        """
        client = AsyncEarnApp(
            base_url=base_url, api_key=api_key, _strict_response_validation=True, default_headers={"X-Foo": "bar"}
        )
        request = client._build_request(FinalRequestOptions(method="get", url="/foo"))
        assert request.headers.get("x-foo") == "bar"
        assert request.headers.get("x-stainless-lang") == "python"

        client2 = AsyncEarnApp(
            base_url=base_url,
            api_key=api_key,
            _strict_response_validation=True,
            default_headers={
                "X-Foo": "stainless",
                "X-Stainless-Lang": "my-overriding-header",
            },
        )
        request = client2._build_request(FinalRequestOptions(method="get", url="/foo"))
        assert request.headers.get("x-foo") == "stainless"
        assert request.headers.get("x-stainless-lang") == "my-overriding-header"

    def test_validate_headers(self) -> None:
        """
        Tests that the Authorization header is correctly set when an API key is provided and that an error is raised if the API key is missing.
        """
        client = AsyncEarnApp(base_url=base_url, api_key=api_key, _strict_response_validation=True)
        request = client._build_request(FinalRequestOptions(method="get", url="/foo"))
        assert request.headers.get("Authorization") == f"Bearer {api_key}"

        with pytest.raises(EarnAppError):
            with update_env(**{"EARN_APP_API_KEY": Omit()}):
                client2 = AsyncEarnApp(base_url=base_url, api_key=None, _strict_response_validation=True)
            _ = client2

    def test_default_query_option(self) -> None:
        """
        Test that the async client applies default query parameters and allows them to be overridden per request.
        """
        client = AsyncEarnApp(
            base_url=base_url, api_key=api_key, _strict_response_validation=True, default_query={"query_param": "bar"}
        )
        request = client._build_request(FinalRequestOptions(method="get", url="/foo"))
        url = httpx.URL(request.url)
        assert dict(url.params) == {"query_param": "bar"}

        request = client._build_request(
            FinalRequestOptions(
                method="get",
                url="/foo",
                params={"foo": "baz", "query_param": "overridden"},
            )
        )
        url = httpx.URL(request.url)
        assert dict(url.params) == {"foo": "baz", "query_param": "overridden"}

    def test_request_extra_json(self) -> None:
        """
        Tests that extra JSON data provided in request options is merged with or overrides the main JSON payload when building a request.
        
        Verifies that:
        - Both `json_data` and `extra_json` are merged in the request body.
        - If only `extra_json` is provided, it becomes the request body.
        - When keys overlap, values from `extra_json` take precedence over those in `json_data`.
        """
        request = self.client._build_request(
            FinalRequestOptions(
                method="post",
                url="/foo",
                json_data={"foo": "bar"},
                extra_json={"baz": False},
            ),
        )
        data = json.loads(request.content.decode("utf-8"))
        assert data == {"foo": "bar", "baz": False}

        request = self.client._build_request(
            FinalRequestOptions(
                method="post",
                url="/foo",
                extra_json={"baz": False},
            ),
        )
        data = json.loads(request.content.decode("utf-8"))
        assert data == {"baz": False}

        # `extra_json` takes priority over `json_data` when keys clash
        request = self.client._build_request(
            FinalRequestOptions(
                method="post",
                url="/foo",
                json_data={"foo": "bar", "baz": True},
                extra_json={"baz": None},
            ),
        )
        data = json.loads(request.content.decode("utf-8"))
        assert data == {"foo": "bar", "baz": None}

    def test_request_extra_headers(self) -> None:
        """
        Tests that extra headers provided in a request are included and take precedence over default headers when keys overlap.
        """
        request = self.client._build_request(
            FinalRequestOptions(
                method="post",
                url="/foo",
                **make_request_options(extra_headers={"X-Foo": "Foo"}),
            ),
        )
        assert request.headers.get("X-Foo") == "Foo"

        # `extra_headers` takes priority over `default_headers` when keys clash
        request = self.client.with_options(default_headers={"X-Bar": "true"})._build_request(
            FinalRequestOptions(
                method="post",
                url="/foo",
                **make_request_options(
                    extra_headers={"X-Bar": "false"},
                ),
            ),
        )
        assert request.headers.get("X-Bar") == "false"

    def test_request_extra_query(self) -> None:
        """
        Tests that extra query parameters are correctly merged into the request, with `extra_query` taking precedence over `query` when keys overlap.
        """
        request = self.client._build_request(
            FinalRequestOptions(
                method="post",
                url="/foo",
                **make_request_options(
                    extra_query={"my_query_param": "Foo"},
                ),
            ),
        )
        params = dict(request.url.params)
        assert params == {"my_query_param": "Foo"}

        # if both `query` and `extra_query` are given, they are merged
        request = self.client._build_request(
            FinalRequestOptions(
                method="post",
                url="/foo",
                **make_request_options(
                    query={"bar": "1"},
                    extra_query={"foo": "2"},
                ),
            ),
        )
        params = dict(request.url.params)
        assert params == {"bar": "1", "foo": "2"}

        # `extra_query` takes priority over `query` when keys clash
        request = self.client._build_request(
            FinalRequestOptions(
                method="post",
                url="/foo",
                **make_request_options(
                    query={"foo": "1"},
                    extra_query={"foo": "2"},
                ),
            ),
        )
        params = dict(request.url.params)
        assert params == {"foo": "2"}

    def test_multipart_repeating_array(self, async_client: AsyncEarnApp) -> None:
        """
        Tests that building a multipart/form-data request with a repeating array field and a file using the async client produces the correct multipart body format with repeated array keys.
        """
        request = async_client._build_request(
            FinalRequestOptions.construct(
                method="get",
                url="/foo",
                headers={"Content-Type": "multipart/form-data; boundary=6b7ba517decee4a450543ea6ae821c82"},
                json_data={"array": ["foo", "bar"]},
                files=[("foo.txt", b"hello world")],
            )
        )

        assert request.read().split(b"\r\n") == [
            b"--6b7ba517decee4a450543ea6ae821c82",
            b'Content-Disposition: form-data; name="array[]"',
            b"",
            b"foo",
            b"--6b7ba517decee4a450543ea6ae821c82",
            b'Content-Disposition: form-data; name="array[]"',
            b"",
            b"bar",
            b"--6b7ba517decee4a450543ea6ae821c82",
            b'Content-Disposition: form-data; name="foo.txt"; filename="upload"',
            b"Content-Type: application/octet-stream",
            b"",
            b"hello world",
            b"--6b7ba517decee4a450543ea6ae821c82--",
            b"",
        ]

    @pytest.mark.respx(base_url=base_url)
    async def test_basic_union_response(self, respx_mock: MockRouter) -> None:
        """
        Tests that the client correctly parses a response into the appropriate model when casting to a union of Pydantic models.
        
        Asserts that when the response JSON matches one of the union types, the correct model is instantiated.
        """
        class Model1(BaseModel):
            name: str

        class Model2(BaseModel):
            foo: str

        respx_mock.get("/foo").mock(return_value=httpx.Response(200, json={"foo": "bar"}))

        response = await self.client.get("/foo", cast_to=cast(Any, Union[Model1, Model2]))
        assert isinstance(response, Model2)
        assert response.foo == "bar"

    @pytest.mark.respx(base_url=base_url)
    async def test_union_response_different_types(self, respx_mock: MockRouter) -> None:
        """
        Tests that the client correctly parses a response into the appropriate model when using a union of models with the same field name but different types.
        """

        class Model1(BaseModel):
            foo: int

        class Model2(BaseModel):
            foo: str

        respx_mock.get("/foo").mock(return_value=httpx.Response(200, json={"foo": "bar"}))

        response = await self.client.get("/foo", cast_to=cast(Any, Union[Model1, Model2]))
        assert isinstance(response, Model2)
        assert response.foo == "bar"

        respx_mock.get("/foo").mock(return_value=httpx.Response(200, json={"foo": 1}))

        response = await self.client.get("/foo", cast_to=cast(Any, Union[Model1, Model2]))
        assert isinstance(response, Model1)
        assert response.foo == 1

    @pytest.mark.respx(base_url=base_url)
    async def test_non_application_json_content_type_for_json_data(self, respx_mock: MockRouter) -> None:
        """
        Tests that a response with a non-JSON content type but containing JSON data is correctly parsed and cast to the specified model.
        """

        class Model(BaseModel):
            foo: int

        respx_mock.get("/foo").mock(
            return_value=httpx.Response(
                200,
                content=json.dumps({"foo": 2}),
                headers={"Content-Type": "application/text"},
            )
        )

        response = await self.client.get("/foo", cast_to=Model)
        assert isinstance(response, Model)
        assert response.foo == 2

    def test_base_url_setter(self) -> None:
        """
        Tests that setting the base URL on the async client normalizes it with a trailing slash.
        """
        client = AsyncEarnApp(
            base_url="https://example.com/from_init", api_key=api_key, _strict_response_validation=True
        )
        assert client.base_url == "https://example.com/from_init/"

        client.base_url = "https://example.com/from_setter"  # type: ignore[assignment]

        assert client.base_url == "https://example.com/from_setter/"

    def test_base_url_env(self) -> None:
        """
        Tests that the async client resolves the base URL from the `EARN_APP_BASE_URL` environment variable, enforces explicit base_url handling when the environment is set, and defaults to the correct URL when `base_url=None` is provided with an environment.
        """
        with update_env(EARN_APP_BASE_URL="http://localhost:5000/from/env"):
            client = AsyncEarnApp(api_key=api_key, _strict_response_validation=True)
            assert client.base_url == "http://localhost:5000/from/env/"

        # explicit environment arg requires explicitness
        with update_env(EARN_APP_BASE_URL="http://localhost:5000/from/env"):
            with pytest.raises(ValueError, match=r"you must pass base_url=None"):
                AsyncEarnApp(api_key=api_key, _strict_response_validation=True, environment="production")

            client = AsyncEarnApp(
                base_url=None, api_key=api_key, _strict_response_validation=True, environment="production"
            )
            assert str(client.base_url).startswith("https://api.slerfhub.xyz/api")

    @pytest.mark.parametrize(
        "client",
        [
            AsyncEarnApp(
                base_url="http://localhost:5000/custom/path/", api_key=api_key, _strict_response_validation=True
            ),
            AsyncEarnApp(
                base_url="http://localhost:5000/custom/path/",
                api_key=api_key,
                _strict_response_validation=True,
                http_client=httpx.AsyncClient(),
            ),
        ],
        ids=["standard", "custom http client"],
    )
    def test_base_url_trailing_slash(self, client: AsyncEarnApp) -> None:
        """
        Tests that the client's base URL with a trailing slash correctly concatenates with a relative request path.
        """
        request = client._build_request(
            FinalRequestOptions(
                method="post",
                url="/foo",
                json_data={"foo": "bar"},
            ),
        )
        assert request.url == "http://localhost:5000/custom/path/foo"

    @pytest.mark.parametrize(
        "client",
        [
            AsyncEarnApp(
                base_url="http://localhost:5000/custom/path/", api_key=api_key, _strict_response_validation=True
            ),
            AsyncEarnApp(
                base_url="http://localhost:5000/custom/path/",
                api_key=api_key,
                _strict_response_validation=True,
                http_client=httpx.AsyncClient(),
            ),
        ],
        ids=["standard", "custom http client"],
    )
    def test_base_url_no_trailing_slash(self, client: AsyncEarnApp) -> None:
        """
        Tests that the client's base URL without a trailing slash is correctly joined with a relative request path.
        """
        request = client._build_request(
            FinalRequestOptions(
                method="post",
                url="/foo",
                json_data={"foo": "bar"},
            ),
        )
        assert request.url == "http://localhost:5000/custom/path/foo"

    @pytest.mark.parametrize(
        "client",
        [
            AsyncEarnApp(
                base_url="http://localhost:5000/custom/path/", api_key=api_key, _strict_response_validation=True
            ),
            AsyncEarnApp(
                base_url="http://localhost:5000/custom/path/",
                api_key=api_key,
                _strict_response_validation=True,
                http_client=httpx.AsyncClient(),
            ),
        ],
        ids=["standard", "custom http client"],
    )
    def test_absolute_request_url(self, client: AsyncEarnApp) -> None:
        """
        Tests that an absolute URL in a request is used as-is by the async client, ignoring the client's base URL.
        """
        request = client._build_request(
            FinalRequestOptions(
                method="post",
                url="https://myapi.com/foo",
                json_data={"foo": "bar"},
            ),
        )
        assert request.url == "https://myapi.com/foo"

    async def test_copied_client_does_not_close_http(self) -> None:
        """
        Verify that copying an asynchronous client does not close the original client's underlying HTTP connection.
        
        This test ensures that deleting a copied client instance does not affect the open state of the original client.
        """
        client = AsyncEarnApp(base_url=base_url, api_key=api_key, _strict_response_validation=True)
        assert not client.is_closed()

        copied = client.copy()
        assert copied is not client

        del copied

        await asyncio.sleep(0.2)
        assert not client.is_closed()

    async def test_client_context_manager(self) -> None:
        """
        Tests that the asynchronous client supports the async context manager protocol, ensuring the client is open within the context and closed after exiting.
        """
        client = AsyncEarnApp(base_url=base_url, api_key=api_key, _strict_response_validation=True)
        async with client as c2:
            assert c2 is client
            assert not c2.is_closed()
            assert not client.is_closed()
        assert client.is_closed()

    @pytest.mark.respx(base_url=base_url)
    @pytest.mark.asyncio
    async def test_client_response_validation_error(self, respx_mock: MockRouter) -> None:
        """
        Tests that an APIResponseValidationError is raised when the response JSON does not match the expected Pydantic model, and verifies that the underlying cause is a Pydantic ValidationError.
        """
        class Model(BaseModel):
            foo: str

        respx_mock.get("/foo").mock(return_value=httpx.Response(200, json={"foo": {"invalid": True}}))

        with pytest.raises(APIResponseValidationError) as exc:
            await self.client.get("/foo", cast_to=Model)

        assert isinstance(exc.value.__cause__, ValidationError)

    async def test_client_max_retries_validation(self) -> None:
        """
        Test that passing None for max_retries to AsyncEarnApp raises a TypeError.
        """
        with pytest.raises(TypeError, match=r"max_retries cannot be None"):
            AsyncEarnApp(
                base_url=base_url, api_key=api_key, _strict_response_validation=True, max_retries=cast(Any, None)
            )

    @pytest.mark.respx(base_url=base_url)
    @pytest.mark.asyncio
    async def test_received_text_for_expected_json(self, respx_mock: MockRouter) -> None:
        """
        Tests handling of text responses when JSON is expected in asynchronous client requests.
        
        Verifies that strict response validation raises an error when the response is plain text but a JSON model is expected, and that non-strict validation returns the raw text instead.
        """
        class Model(BaseModel):
            name: str

        respx_mock.get("/foo").mock(return_value=httpx.Response(200, text="my-custom-format"))

        strict_client = AsyncEarnApp(base_url=base_url, api_key=api_key, _strict_response_validation=True)

        with pytest.raises(APIResponseValidationError):
            await strict_client.get("/foo", cast_to=Model)

        client = AsyncEarnApp(base_url=base_url, api_key=api_key, _strict_response_validation=False)

        response = await client.get("/foo", cast_to=Model)
        assert isinstance(response, str)  # type: ignore[unreachable]

    @pytest.mark.parametrize(
        "remaining_retries,retry_after,timeout",
        [
            [3, "20", 20],
            [3, "0", 0.5],
            [3, "-10", 0.5],
            [3, "60", 60],
            [3, "61", 0.5],
            [3, "Fri, 29 Sep 2023 16:26:57 GMT", 20],
            [3, "Fri, 29 Sep 2023 16:26:37 GMT", 0.5],
            [3, "Fri, 29 Sep 2023 16:26:27 GMT", 0.5],
            [3, "Fri, 29 Sep 2023 16:27:37 GMT", 60],
            [3, "Fri, 29 Sep 2023 16:27:38 GMT", 0.5],
            [3, "99999999999999999999999999999999999", 0.5],
            [3, "Zun, 29 Sep 2023 16:26:27 GMT", 0.5],
            [3, "", 0.5],
            [2, "", 0.5 * 2.0],
            [1, "", 0.5 * 4.0],
            [-1100, "", 8],  # test large number potentially overflowing
        ],
    )
    @mock.patch("time.time", mock.MagicMock(return_value=1696004797))
    @pytest.mark.asyncio
    async def test_parse_retry_after_header(self, remaining_retries: int, retry_after: str, timeout: float) -> None:
        """
        Tests that the asynchronous client correctly calculates the retry timeout based on the `Retry-After` HTTP header value.
        
        Parameters:
            remaining_retries (int): The number of retries left for the request.
            retry_after (str): The value of the `Retry-After` header to test.
            timeout (float): The expected timeout value to compare against.
        """
        client = AsyncEarnApp(base_url=base_url, api_key=api_key, _strict_response_validation=True)

        headers = httpx.Headers({"retry-after": retry_after})
        options = FinalRequestOptions(method="get", url="/foo", max_retries=3)
        calculated = client._calculate_retry_timeout(remaining_retries, options, headers)
        assert calculated == pytest.approx(timeout, 0.5 * 0.875)  # pyright: ignore[reportUnknownMemberType]

    @mock.patch("earn_app._base_client.BaseClient._calculate_retry_timeout", _low_retry_timeout)
    @pytest.mark.respx(base_url=base_url)
    async def test_retrying_timeout_errors_doesnt_leak(
        self, respx_mock: MockRouter, async_client: AsyncEarnApp
    ) -> None:
        """
        Tests that repeated timeout errors during async requests do not cause HTTP connection leaks.
        
        Simulates repeated timeout exceptions on a POST to `/users`, asserts that `APITimeoutError` is raised, and verifies that no open HTTP connections remain after the operation.
        """
        respx_mock.post("/users").mock(side_effect=httpx.TimeoutException("Test timeout error"))

        with pytest.raises(APITimeoutError):
            await async_client.users.with_streaming_response.create(wallet_address="walletAddress").__aenter__()

        assert _get_open_connections(self.client) == 0

    @mock.patch("earn_app._base_client.BaseClient._calculate_retry_timeout", _low_retry_timeout)
    @pytest.mark.respx(base_url=base_url)
    async def test_retrying_status_errors_doesnt_leak(self, respx_mock: MockRouter, async_client: AsyncEarnApp) -> None:
        """
        Tests that repeated HTTP 500 status errors during async client requests do not result in leaked open HTTP connections.
        
        Asserts that an APIStatusError is raised and all HTTP connections are properly closed after the failed request.
        """
        respx_mock.post("/users").mock(return_value=httpx.Response(500))

        with pytest.raises(APIStatusError):
            await async_client.users.with_streaming_response.create(wallet_address="walletAddress").__aenter__()
        assert _get_open_connections(self.client) == 0

    @pytest.mark.parametrize("failures_before_success", [0, 2, 4])
    @mock.patch("earn_app._base_client.BaseClient._calculate_retry_timeout", _low_retry_timeout)
    @pytest.mark.respx(base_url=base_url)
    @pytest.mark.asyncio
    @pytest.mark.parametrize("failure_mode", ["status", "exception"])
    async def test_retries_taken(
        self,
        async_client: AsyncEarnApp,
        failures_before_success: int,
        failure_mode: Literal["status", "exception"],
        respx_mock: MockRouter,
    ) -> None:
        """
        Tests that the async client retries failed requests the expected number of times before succeeding.
        
        Parameters:
            failures_before_success (int): Number of failures to simulate before a successful response.
            failure_mode (Literal["status", "exception"]): Determines whether failures are simulated as HTTP 500 responses or raised exceptions.
        
        Asserts that the response includes the correct retry count in both the response metadata and the request headers.
        """
        client = async_client.with_options(max_retries=4)

        nb_retries = 0

        def retry_handler(_request: httpx.Request) -> httpx.Response:
            """
            Simulates a retry scenario by returning a failure response or raising an exception for a specified number of attempts before returning a success response.
            
            Returns:
                httpx.Response: A 500 response for failed attempts or a 200 response after the specified number of failures.
            """
            nonlocal nb_retries
            if nb_retries < failures_before_success:
                nb_retries += 1
                if failure_mode == "exception":
                    raise RuntimeError("oops")
                return httpx.Response(500)
            return httpx.Response(200)

        respx_mock.post("/users").mock(side_effect=retry_handler)

        response = await client.users.with_raw_response.create(wallet_address="walletAddress")

        assert response.retries_taken == failures_before_success
        assert int(response.http_request.headers.get("x-stainless-retry-count")) == failures_before_success

    @pytest.mark.parametrize("failures_before_success", [0, 2, 4])
    @mock.patch("earn_app._base_client.BaseClient._calculate_retry_timeout", _low_retry_timeout)
    @pytest.mark.respx(base_url=base_url)
    @pytest.mark.asyncio
    async def test_omit_retry_count_header(
        self, async_client: AsyncEarnApp, failures_before_success: int, respx_mock: MockRouter
    ) -> None:
        """
        Test that omitting the retry count header results in no `x-stainless-retry-count` header being sent in the request.
        
        Simulates a series of failed requests before a successful one, ensuring that when the retry count header is explicitly omitted via `extra_headers`, it is not present in the outgoing HTTP request.
        """
        client = async_client.with_options(max_retries=4)

        nb_retries = 0

        def retry_handler(_request: httpx.Request) -> httpx.Response:
            """
            Simulates a retry handler that returns a 500 response for a specified number of attempts before returning a 200 response.
            
            Parameters:
                _request (httpx.Request): The incoming HTTP request (unused).
            
            Returns:
                httpx.Response: An HTTP 500 response until the retry limit is reached, then an HTTP 200 response.
            """
            nonlocal nb_retries
            if nb_retries < failures_before_success:
                nb_retries += 1
                return httpx.Response(500)
            return httpx.Response(200)

        respx_mock.post("/users").mock(side_effect=retry_handler)

        response = await client.users.with_raw_response.create(
            wallet_address="walletAddress", extra_headers={"x-stainless-retry-count": Omit()}
        )

        assert len(response.http_request.headers.get_list("x-stainless-retry-count")) == 0

    @pytest.mark.parametrize("failures_before_success", [0, 2, 4])
    @mock.patch("earn_app._base_client.BaseClient._calculate_retry_timeout", _low_retry_timeout)
    @pytest.mark.respx(base_url=base_url)
    @pytest.mark.asyncio
    async def test_overwrite_retry_count_header(
        self, async_client: AsyncEarnApp, failures_before_success: int, respx_mock: MockRouter
    ) -> None:
        """
        Tests that explicitly setting the retry count header in an async request overrides the default value, even after retries.
        
        Parameters:
            failures_before_success (int): Number of simulated failures before a successful response is returned.
        """
        client = async_client.with_options(max_retries=4)

        nb_retries = 0

        def retry_handler(_request: httpx.Request) -> httpx.Response:
            """
            Simulates a retry handler that returns a 500 response for a specified number of attempts before returning a 200 response.
            
            Parameters:
                _request (httpx.Request): The incoming HTTP request (unused).
            
            Returns:
                httpx.Response: An HTTP 500 response until the retry limit is reached, then an HTTP 200 response.
            """
            nonlocal nb_retries
            if nb_retries < failures_before_success:
                nb_retries += 1
                return httpx.Response(500)
            return httpx.Response(200)

        respx_mock.post("/users").mock(side_effect=retry_handler)

        response = await client.users.with_raw_response.create(
            wallet_address="walletAddress", extra_headers={"x-stainless-retry-count": "42"}
        )

        assert response.http_request.headers.get("x-stainless-retry-count") == "42"

    def test_get_platform(self) -> None:
        # A previous implementation of asyncify could leave threads unterminated when
        # used with nest_asyncio.
        #
        # Since nest_asyncio.apply() is global and cannot be un-applied, this
        # test is run in a separate process to avoid affecting other tests.
        """
        Tests that calling `get_platform` via `asyncify` with `nest_asyncio` applied does not hang or leave threads unterminated by running the code in a separate subprocess.
        
        Raises:
            AssertionError: If the subprocess exits with a non-zero code or hangs beyond the timeout.
        """
        test_code = dedent("""
        import asyncio
        import nest_asyncio
        import threading

        from earn_app._utils import asyncify
        from earn_app._base_client import get_platform

        async def test_main() -> None:
            result = await asyncify(get_platform)()
            print(result)
            for thread in threading.enumerate():
                print(thread.name)

        nest_asyncio.apply()
        asyncio.run(test_main())
        """)
        with subprocess.Popen(
            [sys.executable, "-c", test_code],
            text=True,
        ) as process:
            timeout = 10  # seconds

            start_time = time.monotonic()
            while True:
                return_code = process.poll()
                if return_code is not None:
                    if return_code != 0:
                        raise AssertionError("calling get_platform using asyncify resulted in a non-zero exit code")

                    # success
                    break

                if time.monotonic() - start_time > timeout:
                    process.kill()
                    raise AssertionError("calling get_platform using asyncify resulted in a hung process")

                time.sleep(0.1)

    async def test_proxy_environment_variables(self, monkeypatch: pytest.MonkeyPatch) -> None:
        # Test that the proxy environment variables are set correctly
        """
        Tests that the default asynchronous HTTP client correctly applies proxy settings from environment variables.
        """
        monkeypatch.setenv("HTTPS_PROXY", "https://example.org")

        client = DefaultAsyncHttpxClient()

        mounts = tuple(client._mounts.items())
        assert len(mounts) == 1
        assert mounts[0][0].pattern == "https://"

    @pytest.mark.filterwarnings("ignore:.*deprecated.*:DeprecationWarning")
    async def test_default_client_creation(self) -> None:
        # Ensure that the client can be initialized without any exceptions
        """
        Tests that the default asynchronous HTTP client can be created with various configuration options without raising exceptions.
        """
        DefaultAsyncHttpxClient(
            verify=True,
            cert=None,
            trust_env=True,
            http1=True,
            http2=False,
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
        )

    @pytest.mark.respx(base_url=base_url)
    async def test_follow_redirects(self, respx_mock: MockRouter) -> None:
        # Test that the default follow_redirects=True allows following redirects
        """
        Tests that the asynchronous client follows HTTP redirects by default when making a POST request, resulting in a successful final response.
        """
        respx_mock.post("/redirect").mock(
            return_value=httpx.Response(302, headers={"Location": f"{base_url}/redirected"})
        )
        respx_mock.get("/redirected").mock(return_value=httpx.Response(200, json={"status": "ok"}))

        response = await self.client.post("/redirect", body={"key": "value"}, cast_to=httpx.Response)
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    @pytest.mark.respx(base_url=base_url)
    async def test_follow_redirects_disabled(self, respx_mock: MockRouter) -> None:
        # Test that follow_redirects=False prevents following redirects
        """
        Test that disabling redirect following raises an APIStatusError on HTTP 302 responses.
        
        Asserts that when `follow_redirects` is set to False, the client does not follow redirects and raises an error containing the original 302 response.
        """
        respx_mock.post("/redirect").mock(
            return_value=httpx.Response(302, headers={"Location": f"{base_url}/redirected"})
        )

        with pytest.raises(APIStatusError) as exc_info:
            await self.client.post(
                "/redirect", body={"key": "value"}, options={"follow_redirects": False}, cast_to=httpx.Response
            )

        assert exc_info.value.response.status_code == 302
        assert exc_info.value.response.headers["Location"] == f"{base_url}/redirected"
