# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from .stakes import (
    StakesResource,
    AsyncStakesResource,
    StakesResourceWithRawResponse,
    AsyncStakesResourceWithRawResponse,
    StakesResourceWithStreamingResponse,
    AsyncStakesResourceWithStreamingResponse,
)
from ...types import user_create_params
from ..._types import NOT_GIVEN, Body, Query, Headers, NotGiven
from ..._utils import maybe_transform, async_maybe_transform
from ..._compat import cached_property
from ..._resource import SyncAPIResource, AsyncAPIResource
from ..._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from ...types.user import User
from ..._base_client import make_request_options
from ...types.user_list_missions_response import UserListMissionsResponse
from ...types.user_list_referrals_response import UserListReferralsResponse

__all__ = ["UsersResource", "AsyncUsersResource"]


class UsersResource(SyncAPIResource):
    @cached_property
    def stakes(self) -> StakesResource:
        """
        Provides access to stake-related operations for users.
        
        Returns:
            StakesResource: Resource for managing user stakes.
        """
        return StakesResource(self._client)

    @cached_property
    def with_raw_response(self) -> UsersResourceWithRawResponse:
        """
        Returns a variant of this resource where all method calls return raw HTTP response objects instead of parsed data.
        
        Use this property to access response metadata such as headers or status codes alongside the response body.
        """
        return UsersResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> UsersResourceWithStreamingResponse:
        """
        Returns a variant of this resource that provides streaming HTTP responses without eagerly reading the response body.
        """
        return UsersResourceWithStreamingResponse(self)

    def create(
        self,
        *,
        wallet_address: str,
        email: str | NotGiven = NOT_GIVEN,
        referral_code: str | NotGiven = NOT_GIVEN,
        username: str | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> User:
        """
        Registers a new user with the specified wallet address and optional details.
        
        Parameters:
            wallet_address (str): The blockchain wallet address for the new user.
            email (str, optional): The user's email address.
            referral_code (str, optional): A referral code used during signup.
            username (str, optional): The user's chosen username.
        
        Returns:
            User: The created user object.
        """
        return self._post(
            "/users",
            body=maybe_transform(
                {
                    "wallet_address": wallet_address,
                    "email": email,
                    "referral_code": referral_code,
                    "username": username,
                },
                user_create_params.UserCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=User,
        )

    def list_missions(
        self,
        user_id: int,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> UserListMissionsResponse:
        """
        Retrieve all missions associated with the specified user.
        
        Parameters:
            user_id (int): The unique identifier of the user whose missions are to be retrieved.
        
        Returns:
            UserListMissionsResponse: An object containing the list of missions for the user.
        """
        return self._get(
            f"/users/{user_id}/missions",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UserListMissionsResponse,
        )

    def list_referrals(
        self,
        user_id: int,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> UserListReferralsResponse:
        """
        Retrieve all referrals made by the specified user.
        
        Parameters:
            user_id (int): The unique identifier of the user whose referrals are to be retrieved.
        
        Returns:
            UserListReferralsResponse: A response object containing the list of referrals made by the user.
        """
        return self._get(
            f"/users/{user_id}/referrals",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UserListReferralsResponse,
        )

    def retrieve_by_wallet(
        self,
        address: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> User:
        """
        Retrieve user details using a blockchain wallet address.
        
        Parameters:
            address (str): The blockchain wallet address to look up.
        
        Returns:
            User: The user associated with the specified wallet address.
        
        Raises:
            ValueError: If the provided address is empty.
        """
        if not address:
            raise ValueError(f"Expected a non-empty value for `address` but received {address!r}")
        return self._get(
            f"/users/wallet/{address}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=User,
        )


class AsyncUsersResource(AsyncAPIResource):
    @cached_property
    def stakes(self) -> AsyncStakesResource:
        """
        Returns the asynchronous stakes resource for managing user-related stake operations.
        """
        return AsyncStakesResource(self._client)

    @cached_property
    def with_raw_response(self) -> AsyncUsersResourceWithRawResponse:
        """
        Returns a variant of this resource where all method calls yield raw HTTP response objects instead of parsed data.
        
        Use this property to access response metadata such as headers or status codes alongside the response body.
        """
        return AsyncUsersResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncUsersResourceWithStreamingResponse:
        """
        Returns a variant of this resource that provides streaming HTTP responses without eagerly reading the response body.
        """
        return AsyncUsersResourceWithStreamingResponse(self)

    async def create(
        self,
        *,
        wallet_address: str,
        email: str | NotGiven = NOT_GIVEN,
        referral_code: str | NotGiven = NOT_GIVEN,
        username: str | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> User:
        """
        Asynchronously registers a new user with the specified wallet address and optional details.
        
        Parameters:
            wallet_address (str): The user's blockchain wallet address. Required.
            email (str, optional): The user's email address.
            referral_code (str, optional): Referral code used during signup.
            username (str, optional): The user's chosen username.
        
        Returns:
            User: The newly created user object.
        """
        return await self._post(
            "/users",
            body=await async_maybe_transform(
                {
                    "wallet_address": wallet_address,
                    "email": email,
                    "referral_code": referral_code,
                    "username": username,
                },
                user_create_params.UserCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=User,
        )

    async def list_missions(
        self,
        user_id: int,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> UserListMissionsResponse:
        """
        Asynchronously retrieves all missions associated with a specific user.
        
        Parameters:
            user_id (int): The unique identifier of the user whose missions are to be retrieved.
        
        Returns:
            UserListMissionsResponse: An object containing the list of missions for the specified user.
        """
        return await self._get(
            f"/users/{user_id}/missions",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UserListMissionsResponse,
        )

    async def list_referrals(
        self,
        user_id: int,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> UserListReferralsResponse:
        """
        Asynchronously retrieves all referrals made by the specified user.
        
        Parameters:
            user_id (int): The unique identifier of the user whose referrals are to be retrieved.
        
        Returns:
            UserListReferralsResponse: A response object containing the list of referrals made by the user.
        """
        return await self._get(
            f"/users/{user_id}/referrals",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UserListReferralsResponse,
        )

    async def retrieve_by_wallet(
        self,
        address: str,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> User:
        """
        Asynchronously retrieves user details using the specified blockchain wallet address.
        
        Parameters:
            address (str): The blockchain wallet address of the user to retrieve.
        
        Returns:
            User: The user associated with the provided wallet address.
        
        Raises:
            ValueError: If the provided address is empty.
        """
        if not address:
            raise ValueError(f"Expected a non-empty value for `address` but received {address!r}")
        return await self._get(
            f"/users/wallet/{address}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=User,
        )


class UsersResourceWithRawResponse:
    def __init__(self, users: UsersResource) -> None:
        """
        Initialize a wrapper for UsersResource methods to return raw HTTP responses.
        
        Parameters:
            users (UsersResource): The UsersResource instance to wrap.
        """
        self._users = users

        self.create = to_raw_response_wrapper(
            users.create,
        )
        self.list_missions = to_raw_response_wrapper(
            users.list_missions,
        )
        self.list_referrals = to_raw_response_wrapper(
            users.list_referrals,
        )
        self.retrieve_by_wallet = to_raw_response_wrapper(
            users.retrieve_by_wallet,
        )

    @cached_property
    def stakes(self) -> StakesResourceWithRawResponse:
        """
        Provides access to the stakes resource with raw HTTP response handling for user-related operations.
        
        Returns:
            StakesResourceWithRawResponse: A resource for managing user stakes that returns raw HTTP responses.
        """
        return StakesResourceWithRawResponse(self._users.stakes)


class AsyncUsersResourceWithRawResponse:
    def __init__(self, users: AsyncUsersResource) -> None:
        """
        Initialize an asynchronous users resource wrapper that returns raw HTTP responses for user-related operations.
        
        Parameters:
            users (AsyncUsersResource): The asynchronous users resource to be wrapped.
        """
        self._users = users

        self.create = async_to_raw_response_wrapper(
            users.create,
        )
        self.list_missions = async_to_raw_response_wrapper(
            users.list_missions,
        )
        self.list_referrals = async_to_raw_response_wrapper(
            users.list_referrals,
        )
        self.retrieve_by_wallet = async_to_raw_response_wrapper(
            users.retrieve_by_wallet,
        )

    @cached_property
    def stakes(self) -> AsyncStakesResourceWithRawResponse:
        """
        Provides access to the stakes sub-resource with raw HTTP response handling for asynchronous operations.
        
        Returns:
            AsyncStakesResourceWithRawResponse: The stakes resource wrapper that returns raw HTTP responses.
        """
        return AsyncStakesResourceWithRawResponse(self._users.stakes)


class UsersResourceWithStreamingResponse:
    def __init__(self, users: UsersResource) -> None:
        """
        Initialize a UsersResourceWithStreamingResponse instance that wraps a UsersResource to provide streaming HTTP response variants of user-related API methods.
        
        Parameters:
            users (UsersResource): The UsersResource instance to be wrapped for streaming response support.
        """
        self._users = users

        self.create = to_streamed_response_wrapper(
            users.create,
        )
        self.list_missions = to_streamed_response_wrapper(
            users.list_missions,
        )
        self.list_referrals = to_streamed_response_wrapper(
            users.list_referrals,
        )
        self.retrieve_by_wallet = to_streamed_response_wrapper(
            users.retrieve_by_wallet,
        )

    @cached_property
    def stakes(self) -> StakesResourceWithStreamingResponse:
        """
        Provides access to the stakes resource with streaming HTTP response support.
        """
        return StakesResourceWithStreamingResponse(self._users.stakes)


class AsyncUsersResourceWithStreamingResponse:
    def __init__(self, users: AsyncUsersResource) -> None:
        """
        Initialize an asynchronous users resource wrapper that returns streaming HTTP responses.
        
        Parameters:
            users (AsyncUsersResource): The asynchronous users resource to wrap.
        """
        self._users = users

        self.create = async_to_streamed_response_wrapper(
            users.create,
        )
        self.list_missions = async_to_streamed_response_wrapper(
            users.list_missions,
        )
        self.list_referrals = async_to_streamed_response_wrapper(
            users.list_referrals,
        )
        self.retrieve_by_wallet = async_to_streamed_response_wrapper(
            users.retrieve_by_wallet,
        )

    @cached_property
    def stakes(self) -> AsyncStakesResourceWithStreamingResponse:
        """
        Provides access to the streaming response variant of the stakes sub-resource for asynchronous user operations.
        
        Returns:
            AsyncStakesResourceWithStreamingResponse: The stakes resource with streaming HTTP response support.
        """
        return AsyncStakesResourceWithStreamingResponse(self._users.stakes)
