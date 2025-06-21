# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from earn_app import EarnApp, AsyncEarnApp
from tests.utils import assert_matches_type
from earn_app.types.users import UserStake, StakeListResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestStakes:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    def test_method_create(self, client: EarnApp) -> None:
        stake = client.users.stakes.create(
            user_id=0,
            amount=0,
            vault_id=0,
        )
        assert_matches_type(UserStake, stake, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_method_create_with_all_params(self, client: EarnApp) -> None:
        stake = client.users.stakes.create(
            user_id=0,
            amount=0,
            vault_id=0,
            auto_compound=True,
            lock_period=0,
        )
        assert_matches_type(UserStake, stake, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_create(self, client: EarnApp) -> None:
        response = client.users.stakes.with_raw_response.create(
            user_id=0,
            amount=0,
            vault_id=0,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        stake = response.parse()
        assert_matches_type(UserStake, stake, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_create(self, client: EarnApp) -> None:
        with client.users.stakes.with_streaming_response.create(
            user_id=0,
            amount=0,
            vault_id=0,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            stake = response.parse()
            assert_matches_type(UserStake, stake, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_list(self, client: EarnApp) -> None:
        stake = client.users.stakes.list(
            0,
        )
        assert_matches_type(StakeListResponse, stake, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_list(self, client: EarnApp) -> None:
        response = client.users.stakes.with_raw_response.list(
            0,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        stake = response.parse()
        assert_matches_type(StakeListResponse, stake, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_list(self, client: EarnApp) -> None:
        with client.users.stakes.with_streaming_response.list(
            0,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            stake = response.parse()
            assert_matches_type(StakeListResponse, stake, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncStakes:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip()
    @parametrize
    async def test_method_create(self, async_client: AsyncEarnApp) -> None:
        stake = await async_client.users.stakes.create(
            user_id=0,
            amount=0,
            vault_id=0,
        )
        assert_matches_type(UserStake, stake, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncEarnApp) -> None:
        stake = await async_client.users.stakes.create(
            user_id=0,
            amount=0,
            vault_id=0,
            auto_compound=True,
            lock_period=0,
        )
        assert_matches_type(UserStake, stake, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncEarnApp) -> None:
        response = await async_client.users.stakes.with_raw_response.create(
            user_id=0,
            amount=0,
            vault_id=0,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        stake = await response.parse()
        assert_matches_type(UserStake, stake, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncEarnApp) -> None:
        async with async_client.users.stakes.with_streaming_response.create(
            user_id=0,
            amount=0,
            vault_id=0,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            stake = await response.parse()
            assert_matches_type(UserStake, stake, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_list(self, async_client: AsyncEarnApp) -> None:
        stake = await async_client.users.stakes.list(
            0,
        )
        assert_matches_type(StakeListResponse, stake, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncEarnApp) -> None:
        response = await async_client.users.stakes.with_raw_response.list(
            0,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        stake = await response.parse()
        assert_matches_type(StakeListResponse, stake, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncEarnApp) -> None:
        async with async_client.users.stakes.with_streaming_response.list(
            0,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            stake = await response.parse()
            assert_matches_type(StakeListResponse, stake, path=["response"])

        assert cast(Any, response.is_closed) is True
