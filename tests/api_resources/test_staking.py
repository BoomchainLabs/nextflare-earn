# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from earn_app import EarnApp, AsyncEarnApp
from tests.utils import assert_matches_type
from earn_app.types import StakingListVaultsResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestStaking:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    def test_method_list_vaults(self, client: EarnApp) -> None:
        """
        Test that the staking.list_vaults method returns a response of type StakingListVaultsResponse.
        """
        staking = client.staking.list_vaults()
        assert_matches_type(StakingListVaultsResponse, staking, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_list_vaults(self, client: EarnApp) -> None:
        """
        Test that the raw response from staking.list_vaults is closed, has the correct headers, and parses to the expected type.
        """
        response = client.staking.with_raw_response.list_vaults()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        staking = response.parse()
        assert_matches_type(StakingListVaultsResponse, staking, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_list_vaults(self, client: EarnApp) -> None:
        """
        Test that the streaming response from staking.list_vaults returns the correct type, validates headers, and manages response state.
        """
        with client.staking.with_streaming_response.list_vaults() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            staking = response.parse()
            assert_matches_type(StakingListVaultsResponse, staking, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncStaking:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip()
    @parametrize
    async def test_method_list_vaults(self, async_client: AsyncEarnApp) -> None:
        """
        Test that the asynchronous staking.list_vaults method returns a response matching StakingListVaultsResponse.
        """
        staking = await async_client.staking.list_vaults()
        assert_matches_type(StakingListVaultsResponse, staking, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_list_vaults(self, async_client: AsyncEarnApp) -> None:
        """
        Test that the async staking.list_vaults method returns a valid raw HTTP response and correct parsed data.
        
        Verifies that the response is closed after the call, the custom request header is set, and the parsed response matches the expected type.
        """
        response = await async_client.staking.with_raw_response.list_vaults()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        staking = await response.parse()
        assert_matches_type(StakingListVaultsResponse, staking, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_list_vaults(self, async_client: AsyncEarnApp) -> None:
        """
        Test that the streaming response from the async staking list_vaults endpoint returns the correct type, validates headers, and manages response state.
        """
        async with async_client.staking.with_streaming_response.list_vaults() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            staking = await response.parse()
            assert_matches_type(StakingListVaultsResponse, staking, path=["response"])

        assert cast(Any, response.is_closed) is True
