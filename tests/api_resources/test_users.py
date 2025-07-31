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
        """
        Tests the creation of a user with a wallet address using the EarnApp client.
        
        Asserts that the response is of type User.
        """
        user = client.users.create(
            wallet_address="walletAddress",
        )
        assert_matches_type(User, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_method_create_with_all_params(self, client: EarnApp) -> None:
        """
        Tests the creation of a user with all optional parameters provided.
        
        Asserts that the response is of type `User`.
        """
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
        """
        Test that `users.create` returns a valid raw HTTP response and parses correctly to a `User` object.
        
        Asserts that the response is closed, the correct request header is set, and the parsed response matches the `User` model.
        """
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
        """
        Tests that the `users.create` endpoint supports streaming responses and returns a valid `User` object.
        
        Verifies that the response is open within the context manager, contains the correct HTTP header, parses to a `User` object, and is closed after exiting the context.
        """
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
        """
        Tests the `list_missions` method of the `users` endpoint, verifying the response type is `UserListMissionsResponse`.
        """
        user = client.users.list_missions(
            0,
        )
        assert_matches_type(UserListMissionsResponse, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_list_missions(self, client: EarnApp) -> None:
        """
        Test that `users.list_missions` returns a valid raw response and parses correctly.
        
        Asserts that the response is closed, contains the expected HTTP header, and can be parsed into a `UserListMissionsResponse` object.
        """
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
        """
        Test streaming response handling for the `users.list_missions` endpoint.
        
        Verifies that the response is open within the context manager, checks for the correct HTTP header, parses the response to `UserListMissionsResponse`, and confirms the response is closed after exiting the context.
        """
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
        """
        Tests the `list_referrals` method of the `users` endpoint, asserting the response is a `UserListReferralsResponse` object.
        """
        user = client.users.list_referrals(
            0,
        )
        assert_matches_type(UserListReferralsResponse, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_list_referrals(self, client: EarnApp) -> None:
        """
        Test that `users.list_referrals` returns a valid raw response and parses correctly.
        
        Asserts that the response is closed, the expected HTTP header is present, and the parsed response matches `UserListReferralsResponse`.
        """
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
        """
        Test streaming response handling for the `users.list_referrals` endpoint.
        
        Verifies that the response is open within the context, checks for the correct HTTP header, parses the response to `UserListReferralsResponse`, and confirms the response is closed after exiting the context.
        """
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
        """
        Tests retrieving a user by wallet address using the `retrieve_by_wallet` method.
        
        Asserts that the returned object is of type `User`.
        """
        user = client.users.retrieve_by_wallet(
            "address",
        )
        assert_matches_type(User, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_retrieve_by_wallet(self, client: EarnApp) -> None:
        """
        Tests that retrieving a user by wallet address using the raw response interface returns a closed response with correct headers and parses to a User object.
        """
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
        """
        Test streaming response handling for retrieving a user by wallet address.
        
        Verifies that the response is open within the context, checks for the correct HTTP header, parses the response to a `User` object, and confirms the response is closed after exiting the context.
        """
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
        """
        Test that retrieving a user by an empty wallet address raises a ValueError.
        
        Asserts that calling `retrieve_by_wallet` with an empty string triggers a ValueError with the expected error message.
        """
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `address` but received ''"):
            client.users.with_raw_response.retrieve_by_wallet(
                "",
            )


class TestAsyncUsers:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip()
    @parametrize
    async def test_method_create(self, async_client: AsyncEarnApp) -> None:
        """
        Asynchronously tests the creation of a user with a wallet address using the users API.
        
        Verifies that the response is of type User.
        """
        user = await async_client.users.create(
            wallet_address="walletAddress",
        )
        assert_matches_type(User, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_create_with_all_params(self, async_client: AsyncEarnApp) -> None:
        """
        Asynchronously tests creating a user with all optional parameters using the users API endpoint.
        
        Verifies that the response is of type User when providing wallet address, email, referral code, and username.
        """
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
        """
        Asynchronously tests the raw HTTP response from the `users.create` endpoint.
        
        Verifies that the response is closed, the correct request header is present, and the parsed response matches the `User` model.
        """
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
        """
        Asynchronously tests the streaming response of the `users.create` endpoint.
        
        Verifies that the response is open during the context, checks the request header, parses the response to a `User` object, and confirms the response is closed after exiting the context.
        """
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
        """
        Asynchronously tests the `list_missions` method of the users endpoint to ensure it returns a `UserListMissionsResponse` for a given user ID.
        """
        user = await async_client.users.list_missions(
            0,
        )
        assert_matches_type(UserListMissionsResponse, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_list_missions(self, async_client: AsyncEarnApp) -> None:
        """
        Asynchronously tests the raw HTTP response handling of the `users.list_missions` endpoint.
        
        Verifies that the response is closed after retrieval, checks for the correct request header, and asserts that the parsed response matches the `UserListMissionsResponse` model.
        """
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
        """
        Asynchronously tests the streaming response of the `users.list_missions` endpoint.
        
        Verifies that the response is open within the context, checks for the correct HTTP header, parses the response to a `UserListMissionsResponse` object, and confirms the response is closed after exiting the context.
        """
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
        """
        Asynchronously tests the `list_referrals` method of the users endpoint, asserting the response type is `UserListReferralsResponse`.
        """
        user = await async_client.users.list_referrals(
            0,
        )
        assert_matches_type(UserListReferralsResponse, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_list_referrals(self, async_client: AsyncEarnApp) -> None:
        """
        Asynchronously tests that the raw HTTP response from `users.list_referrals` returns a valid `UserListReferralsResponse` and includes the expected headers.
        """
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
        """
        Asynchronously tests the streaming response of the `users.list_referrals` endpoint.
        
        Verifies that the response is open within the context, checks for the correct HTTP header, parses the response to a `UserListReferralsResponse`, and confirms the response is closed after exiting the context.
        """
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
        """
        Asynchronously tests retrieving a user by wallet address using the users API.
        
        Asserts that the response is of type User.
        """
        user = await async_client.users.retrieve_by_wallet(
            "address",
        )
        assert_matches_type(User, user, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_retrieve_by_wallet(self, async_client: AsyncEarnApp) -> None:
        """
        Tests that retrieving a user by wallet address using the async client returns a valid raw response and user object.
        
        Asserts that the raw response is closed, contains the correct HTTP header, and parses to a `User` instance.
        """
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
        """
        Asynchronously tests streaming response handling for retrieving a user by wallet address.
        
        Verifies that the response is open within the context, checks for the correct HTTP header, parses the response to a `User` object, and confirms the response is closed after exiting the context.
        """
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
        """
        Test that retrieving a user by an empty wallet address raises a ValueError.
        
        Asserts that calling `retrieve_by_wallet` with an empty string triggers a ValueError with the expected error message.
        """
        with pytest.raises(ValueError, match=r"Expected a non-empty value for `address` but received ''"):
            await async_client.users.with_raw_response.retrieve_by_wallet(
                "",
            )
