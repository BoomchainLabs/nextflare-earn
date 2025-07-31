# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from earn_app import EarnApp, AsyncEarnApp
from tests.utils import assert_matches_type
from earn_app.types import TokenRetrieveInfoResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestToken:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    def test_method_retrieve_info(self, client: EarnApp) -> None:
        """
        Tests that the `retrieve_info` method of the token resource returns a response matching the `TokenRetrieveInfoResponse` type.
        """
        token = client.token.retrieve_info()
        assert_matches_type(TokenRetrieveInfoResponse, token, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_retrieve_info(self, client: EarnApp) -> None:
        """
        Test that `token.retrieve_info` returns a closed raw response with correct headers and a valid parsed result.
        """
        response = client.token.with_raw_response.retrieve_info()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        token = response.parse()
        assert_matches_type(TokenRetrieveInfoResponse, token, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_retrieve_info(self, client: EarnApp) -> None:
        """
        Test that the streaming response from `token.retrieve_info` is handled correctly, including response state and header validation.
        
        Verifies that the response is open within the context, the custom HTTP header is set, the parsed response matches the expected type, and the response is closed after exiting the context.
        """
        with client.token.with_streaming_response.retrieve_info() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            token = response.parse()
            assert_matches_type(TokenRetrieveInfoResponse, token, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncToken:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip()
    @parametrize
    async def test_method_retrieve_info(self, async_client: AsyncEarnApp) -> None:
        """
        Test that the asynchronous token info retrieval method returns a valid TokenRetrieveInfoResponse object.
        """
        token = await async_client.token.retrieve_info()
        assert_matches_type(TokenRetrieveInfoResponse, token, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_retrieve_info(self, async_client: AsyncEarnApp) -> None:
        """
        Test that the async token.retrieve_info method returns a valid raw response and correct headers.
        
        Verifies that the response is closed, the custom HTTP header is set to "python", and the parsed response matches the expected type.
        """
        response = await async_client.token.with_raw_response.retrieve_info()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        token = await response.parse()
        assert_matches_type(TokenRetrieveInfoResponse, token, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_retrieve_info(self, async_client: AsyncEarnApp) -> None:
        """
        Test that the async streaming response from `token.retrieve_info` is handled correctly and matches the expected type.
        
        Verifies that the response is open within the context, checks for the correct HTTP request header, asserts the parsed response type, and ensures the response is closed after exiting the context.
        """
        async with async_client.token.with_streaming_response.retrieve_info() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            token = await response.parse()
            assert_matches_type(TokenRetrieveInfoResponse, token, path=["response"])

        assert cast(Any, response.is_closed) is True
