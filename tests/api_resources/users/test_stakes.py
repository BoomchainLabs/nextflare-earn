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
        """
        Tests creating a user stake with the minimum required parameters and asserts the response type is UserStake.
        """
        stake = client.users.stakes.create(
            user_id=0,
            amount=0,
            vault_id=0,
        )
        assert_matches_type(UserStake, stake, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_method_create_with_all_params(self, client: EarnApp) -> None:
        """
        Tests creating a user stake with all available parameters using the EarnApp client.
        
        Asserts that the response is of type UserStake.
        """
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
        """
        Tests creating a user stake using the raw response interface and verifies response closure, HTTP headers, and response type.
        """
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
        """
        Tests creating a user stake using the streaming response context manager and verifies response state and headers.
        
        Asserts that the response is open within the context, checks for the expected HTTP header, parses the response as a `UserStake`, and confirms the response is closed after exiting the context.
        """
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
        """
        Tests listing all stakes for a user and asserts the response matches the expected StakeListResponse type.
        """
        stake = client.users.stakes.list(
            0,
        )
        assert_matches_type(StakeListResponse, stake, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_list(self, client: EarnApp) -> None:
        """
        Tests listing user stakes using the raw response interface and verifies response closure, headers, and parsed type.
        """
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
        """
        Tests listing user stakes using a streaming response context manager and verifies response headers, open/closed state, and response type.
        """
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
        """
        Asynchronously tests creating a user stake with minimal required parameters using the EarnApp client.
        
        Awaits the creation of a stake and asserts that the response matches the expected UserStake type.
        """
        stake = await async_client.users.stakes.create(
            user_id=0,
            amount=0,
            vault_id=0,
        )
        assert_matches_type(UserStake, stake, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncEarnApp) -> None:
        """
        Asynchronously tests creating a user stake with all available parameters using the async EarnApp client.
        
        Verifies that the response matches the expected UserStake type.
        """
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
        """
        Asynchronously tests creating a user stake using the raw response interface of the async client.
        
        Verifies that the HTTP response is closed, checks for the expected custom header, parses the response, and asserts the result is a `UserStake` instance.
        """
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
        """
        Asynchronously tests creating a user stake using a streaming response context manager.
        
        Verifies that the response is initially open, checks for the expected HTTP header, awaits parsing of the response as a `UserStake`, and confirms the response is closed after exiting the context.
        """
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
        """
        Asynchronously tests listing user stakes using the async EarnApp client.
        
        Awaits the list operation for user stakes and asserts that the response matches the expected StakeListResponse type.
        """
        stake = await async_client.users.stakes.list(
            0,
        )
        assert_matches_type(StakeListResponse, stake, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncEarnApp) -> None:
        """
        Asynchronously tests listing user stakes using the raw response interface of the async client.
        
        Awaits the raw response, verifies the response is closed, checks the custom HTTP header, parses the response, and asserts the result matches the expected `StakeListResponse` type.
        """
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
        """
        Asynchronously tests listing user stakes using a streaming response context manager.
        
        Verifies that the response is initially open, checks for the correct HTTP header, awaits parsing of the response to ensure it matches the `StakeListResponse` type, and confirms the response is closed after exiting the context.
        """
        async with async_client.users.stakes.with_streaming_response.list(
            0,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            stake = await response.parse()
            assert_matches_type(StakeListResponse, stake, path=["response"])

        assert cast(Any, response.is_closed) is True
