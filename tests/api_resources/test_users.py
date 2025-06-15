# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from earn_app import EarnApp, AsyncEarnApp
from tests.utils import assert_matches_type
from earn_app.types import User, UserListMissionsResponse, UserListReferralsResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestUsers:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    def test_method_create(self, client: EarnApp) -> None:
        user = client.users.create(
            wallet_address="walletAddress",
        )
        assert_matches_type(User, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_method_create_with_all_params(self, client: EarnApp) -> None:
        user = client.users.create(
            wallet_address="walletAddress",
            email="dev@stainless.com",
            referral_code="referralCode",
            username="username",
        )
        assert_matches_type(User, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_create(self, client: EarnApp) -> None:
        response = client.users.with_raw_response.create(
            wallet_address="walletAddress",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        user = response.parse()
        assert_matches_type(User, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_create(self, client: EarnApp) -> None:
        with client.users.with_streaming_response.create(
            wallet_address="walletAddress",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            user = response.parse()
            assert_matches_type(User, user, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_list_missions(self, client: EarnApp) -> None:
        user = client.users.list_missions(
            0,
        )
        assert_matches_type(UserListMissionsResponse, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_list_missions(self, client: EarnApp) -> None:
        response = client.users.with_raw_response.list_missions(
            0,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        user = response.parse()
        assert_matches_type(UserListMissionsResponse, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_list_missions(self, client: EarnApp) -> None:
        with client.users.with_streaming_response.list_missions(
            0,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            user = response.parse()
            assert_matches_type(UserListMissionsResponse, user, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_list_referrals(self, client: EarnApp) -> None:
        user = client.users.list_referrals(
            0,
        )
        assert_matches_type(UserListReferralsResponse, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_list_referrals(self, client: EarnApp) -> None:
        response = client.users.with_raw_response.list_referrals(
            0,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        user = response.parse()
        assert_matches_type(UserListReferralsResponse, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_list_referrals(self, client: EarnApp) -> None:
        with client.users.with_streaming_response.list_referrals(
            0,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            user = response.parse()
            assert_matches_type(UserListReferralsResponse, user, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_retrieve_by_wallet(self, client: EarnApp) -> None:
        user = client.users.retrieve_by_wallet(
            "address",
        )
        assert_matches_type(User, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_retrieve_by_wallet(self, client: EarnApp) -> None:
        response = client.users.with_raw_response.retrieve_by_wallet(
            "address",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        user = response.parse()
        assert_matches_type(User, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_retrieve_by_wallet(self, client: EarnApp) -> None:
        with client.users.with_streaming_response.retrieve_by_wallet(
            "address",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            user = response.parse()
            assert_matches_type(User, user, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_path_params_retrieve_by_wallet(self, client: EarnApp) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `address` but received ''"):
            client.users.with_raw_response.retrieve_by_wallet(
                "",
            )


class TestAsyncUsers:
    parametrize = pytest.mark.parametrize("async_client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_create(self, async_client: AsyncEarnApp) -> None:
        user = await async_client.users.create(
            wallet_address="walletAddress",
        )
        assert_matches_type(User, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncEarnApp) -> None:
        user = await async_client.users.create(
            wallet_address="walletAddress",
            email="dev@stainless.com",
            referral_code="referralCode",
            username="username",
        )
        assert_matches_type(User, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_create(self, async_client: AsyncEarnApp) -> None:
        response = await async_client.users.with_raw_response.create(
            wallet_address="walletAddress",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        user = await response.parse()
        assert_matches_type(User, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_create(self, async_client: AsyncEarnApp) -> None:
        async with async_client.users.with_streaming_response.create(
            wallet_address="walletAddress",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            user = await response.parse()
            assert_matches_type(User, user, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_list_missions(self, async_client: AsyncEarnApp) -> None:
        user = await async_client.users.list_missions(
            0,
        )
        assert_matches_type(UserListMissionsResponse, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_list_missions(self, async_client: AsyncEarnApp) -> None:
        response = await async_client.users.with_raw_response.list_missions(
            0,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        user = await response.parse()
        assert_matches_type(UserListMissionsResponse, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_list_missions(self, async_client: AsyncEarnApp) -> None:
        async with async_client.users.with_streaming_response.list_missions(
            0,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            user = await response.parse()
            assert_matches_type(UserListMissionsResponse, user, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_list_referrals(self, async_client: AsyncEarnApp) -> None:
        user = await async_client.users.list_referrals(
            0,
        )
        assert_matches_type(UserListReferralsResponse, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_list_referrals(self, async_client: AsyncEarnApp) -> None:
        response = await async_client.users.with_raw_response.list_referrals(
            0,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        user = await response.parse()
        assert_matches_type(UserListReferralsResponse, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_list_referrals(self, async_client: AsyncEarnApp) -> None:
        async with async_client.users.with_streaming_response.list_referrals(
            0,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            user = await response.parse()
            assert_matches_type(UserListReferralsResponse, user, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_retrieve_by_wallet(self, async_client: AsyncEarnApp) -> None:
        user = await async_client.users.retrieve_by_wallet(
            "address",
        )
        assert_matches_type(User, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_retrieve_by_wallet(self, async_client: AsyncEarnApp) -> None:
        response = await async_client.users.with_raw_response.retrieve_by_wallet(
            "address",
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        user = await response.parse()
        assert_matches_type(User, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_retrieve_by_wallet(self, async_client: AsyncEarnApp) -> None:
        async with async_client.users.with_streaming_response.retrieve_by_wallet(
            "address",
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            user = await response.parse()
            assert_matches_type(User, user, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_path_params_retrieve_by_wallet(self, async_client: AsyncEarnApp) -> None:
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `address` but received ''"):
            await async_client.users.with_raw_response.retrieve_by_wallet(
                "",
            )
