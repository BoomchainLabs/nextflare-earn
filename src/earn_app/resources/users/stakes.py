# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

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
from ...types.users import stake_create_params
from ..._base_client import make_request_options
from ...types.users.user_stake import UserStake
from ...types.users.stake_list_response import StakeListResponse

__all__ = ["StakesResource", "AsyncStakesResource"]


class StakesResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> StakesResourceWithRawResponse:
        """
        Returns a wrapper that enables access to raw HTTP response objects for all methods in this resource.
        
        Use this property to receive the full HTTP response, including headers and status code, instead of only the parsed content.
        """
        return StakesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> StakesResourceWithStreamingResponse:
        """
        Returns a wrapper that provides streaming HTTP responses for all stake-related methods without eagerly reading the response body.
        
        Use this to access streamed responses when working with large payloads or when you need to process the response incrementally.
        """
        return StakesResourceWithStreamingResponse(self)

    def create(
        self,
        user_id: int,
        *,
        amount: float,
        vault_id: int,
        auto_compound: bool | NotGiven = NOT_GIVEN,
        lock_period: int | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> UserStake:
        """
        Create a new staking position for a user in a specified vault.
        
        Parameters:
            user_id (int): The unique identifier of the user for whom the stake is being created.
            amount (float): The amount of tokens to stake.
            vault_id (int): The identifier of the vault where tokens will be staked.
            auto_compound (bool, optional): If set, enables automatic compounding of staking rewards.
            lock_period (int, optional): The duration (in days) to lock the staked tokens.
        
        Returns:
            UserStake: An object representing the newly created staking position.
        """
        return self._post(
            f"/users/{user_id}/stakes",
            body=maybe_transform(
                {
                    "amount": amount,
                    "vault_id": vault_id,
                    "auto_compound": auto_compound,
                    "lock_period": lock_period,
                },
                stake_create_params.StakeCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UserStake,
        )

    def list(
        self,
        user_id: int,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> StakeListResponse:
        """
        Retrieve all staking positions for the specified user.
        
        Parameters:
            user_id (int): The unique identifier of the user whose stakes are to be listed.
        
        Returns:
            StakeListResponse: An object containing the user's staking positions.
        """
        return self._get(
            f"/users/{user_id}/stakes",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=StakeListResponse,
        )


class AsyncStakesResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncStakesResourceWithRawResponse:
        """
        Returns a wrapper that enables all API methods to return raw HTTP response objects instead of parsed content.
        
        Use this property to access response metadata such as headers or status codes for asynchronous stake operations.
        """
        return AsyncStakesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncStakesResourceWithStreamingResponse:
        """
        Returns a wrapper that enables streaming HTTP responses for asynchronous stake operations, allowing response bodies to be processed incrementally without eager reading.
        """
        return AsyncStakesResourceWithStreamingResponse(self)

    async def create(
        self,
        user_id: int,
        *,
        amount: float,
        vault_id: int,
        auto_compound: bool | NotGiven = NOT_GIVEN,
        lock_period: int | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> UserStake:
        """
        Asynchronously creates a new stake for a user in a specified vault.
        
        Parameters:
            user_id (int): The unique identifier of the user for whom the stake is being created.
            amount (float): The amount of tokens to stake.
            vault_id (int): The identifier of the vault where tokens will be staked.
            auto_compound (bool, optional): If set, enables automatic compounding of rewards.
            lock_period (int, optional): The lock period for the stake in days.
        
        Returns:
            UserStake: The created stake object for the user.
        """
        return await self._post(
            f"/users/{user_id}/stakes",
            body=await async_maybe_transform(
                {
                    "amount": amount,
                    "vault_id": vault_id,
                    "auto_compound": auto_compound,
                    "lock_period": lock_period,
                },
                stake_create_params.StakeCreateParams,
            ),
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=UserStake,
        )

    async def list(
        self,
        user_id: int,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> StakeListResponse:
        """
        Asynchronously retrieves all staking positions for the specified user.
        
        Parameters:
            user_id (int): The unique identifier of the user whose stakes are to be listed.
        
        Returns:
            StakeListResponse: An object containing the list of all staking positions for the user.
        """
        return await self._get(
            f"/users/{user_id}/stakes",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=StakeListResponse,
        )


class StakesResourceWithRawResponse:
    def __init__(self, stakes: StakesResource) -> None:
        """
        Initialize the wrapper to provide raw HTTP responses for stake creation and listing operations.
        
        Parameters:
        	stakes (StakesResource): The underlying resource used to perform stake-related API calls.
        """
        self._stakes = stakes

        self.create = to_raw_response_wrapper(
            stakes.create,
        )
        self.list = to_raw_response_wrapper(
            stakes.list,
        )


class AsyncStakesResourceWithRawResponse:
    def __init__(self, stakes: AsyncStakesResource) -> None:
        """
        Initializes the wrapper to provide raw HTTP responses for asynchronous stake operations.
        
        Parameters:
            stakes (AsyncStakesResource): The asynchronous stakes resource to wrap.
        """
        self._stakes = stakes

        self.create = async_to_raw_response_wrapper(
            stakes.create,
        )
        self.list = async_to_raw_response_wrapper(
            stakes.list,
        )


class StakesResourceWithStreamingResponse:
    def __init__(self, stakes: StakesResource) -> None:
        """
        Initialize the streaming response wrapper for the StakesResource.
        
        This sets up methods to create and list user stakes, returning streamed HTTP responses instead of parsed objects.
        """
        self._stakes = stakes

        self.create = to_streamed_response_wrapper(
            stakes.create,
        )
        self.list = to_streamed_response_wrapper(
            stakes.list,
        )


class AsyncStakesResourceWithStreamingResponse:
    def __init__(self, stakes: AsyncStakesResource) -> None:
        """
        Initializes the streaming response wrapper for asynchronous user stake operations.
        
        Parameters:
            stakes (AsyncStakesResource): The asynchronous stakes resource to wrap.
        """
        self._stakes = stakes

        self.create = async_to_streamed_response_wrapper(
            stakes.create,
        )
        self.list = async_to_streamed_response_wrapper(
            stakes.list,
        )
