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
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/stainless-sdks/earn-app-python#accessing-raw-response-data-eg-headers
        """
        return StakesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> StakesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/stainless-sdks/earn-app-python#with_streaming_response
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
        Stake tokens in a vault

        Args:
          amount: Amount to stake

          vault_id: Vault identifier

          auto_compound: Whether to auto-compound rewards

          lock_period: Lock period in days

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
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
        Retrieve all staking positions for a specific user

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
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
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/stainless-sdks/earn-app-python#accessing-raw-response-data-eg-headers
        """
        return AsyncStakesResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncStakesResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/stainless-sdks/earn-app-python#with_streaming_response
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
        Stake tokens in a vault

        Args:
          amount: Amount to stake

          vault_id: Vault identifier

          auto_compound: Whether to auto-compound rewards

          lock_period: Lock period in days

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
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
        Retrieve all staking positions for a specific user

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
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
        self._stakes = stakes

        self.create = to_raw_response_wrapper(
            stakes.create,
        )
        self.list = to_raw_response_wrapper(
            stakes.list,
        )


class AsyncStakesResourceWithRawResponse:
    def __init__(self, stakes: AsyncStakesResource) -> None:
        self._stakes = stakes

        self.create = async_to_raw_response_wrapper(
            stakes.create,
        )
        self.list = async_to_raw_response_wrapper(
            stakes.list,
        )


class StakesResourceWithStreamingResponse:
    def __init__(self, stakes: StakesResource) -> None:
        self._stakes = stakes

        self.create = to_streamed_response_wrapper(
            stakes.create,
        )
        self.list = to_streamed_response_wrapper(
            stakes.list,
        )


class AsyncStakesResourceWithStreamingResponse:
    def __init__(self, stakes: AsyncStakesResource) -> None:
        self._stakes = stakes

        self.create = async_to_streamed_response_wrapper(
            stakes.create,
        )
        self.list = async_to_streamed_response_wrapper(
            stakes.list,
        )
