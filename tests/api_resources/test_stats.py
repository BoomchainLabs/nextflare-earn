# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from earn_app import EarnApp, AsyncEarnApp
from tests.utils import assert_matches_type
from earn_app.types import StatRetrieveResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestStats:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    def test_method_retrieve(self, client: EarnApp) -> None:
        """
        Tests that the `stats.retrieve` method returns a response matching the `StatRetrieveResponse` type.
        """
        stat = client.stats.retrieve()
        assert_matches_type(StatRetrieveResponse, stat, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_retrieve(self, client: EarnApp) -> None:
        """
        Test that retrieving stats with raw response returns a closed response, includes the correct HTTP header, and parses to the expected type.
        """
        response = client.stats.with_raw_response.retrieve()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        stat = response.parse()
        assert_matches_type(StatRetrieveResponse, stat, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_retrieve(self, client: EarnApp) -> None:
        """
        Test that the streaming response from the stats.retrieve endpoint is handled correctly.
        
        Verifies that the response is open within the context, checks for the expected HTTP header, asserts the parsed response type, and ensures the response is closed after exiting the context.
        """
        with client.stats.with_streaming_response.retrieve() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            stat = response.parse()
            assert_matches_type(StatRetrieveResponse, stat, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncStats:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip()
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncEarnApp) -> None:
        """
        Test that the asynchronous stats.retrieve method returns a StatRetrieveResponse object.
        """
        stat = await async_client.stats.retrieve()
        assert_matches_type(StatRetrieveResponse, stat, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncEarnApp) -> None:
        """
        Test that retrieving stats with raw response using the async client returns the expected type and includes the correct HTTP header.
        """
        response = await async_client.stats.with_raw_response.retrieve()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        stat = await response.parse()
        assert_matches_type(StatRetrieveResponse, stat, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncEarnApp) -> None:
        """
        Test that the async streaming response from stats.retrieve is handled correctly.
        
        Verifies the response is open during the context, checks for the expected HTTP header, asserts the parsed response type, and ensures the response is closed after exiting the context.
        """
        async with async_client.stats.with_streaming_response.retrieve() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            stat = await response.parse()
            assert_matches_type(StatRetrieveResponse, stat, path=["response"])

        assert cast(Any, response.is_closed) is True
