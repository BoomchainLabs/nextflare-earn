# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import httpx

from .._types import NOT_GIVEN, Body, Query, Headers, NotGiven
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .._base_client import make_request_options
from ..types.staking_list_vaults_response import StakingListVaultsResponse

__all__ = ["StakingResource", "AsyncStakingResource"]


class StakingResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> StakingResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/stainless-sdks/earn-app-python#accessing-raw-response-data-eg-headers
        """
        return StakingResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> StakingResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/stainless-sdks/earn-app-python#with_streaming_response
        """
        return StakingResourceWithStreamingResponse(self)

    def list_vaults(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> StakingListVaultsResponse:
        """Retrieve all available staking vaults"""
        return self._get(
            "/staking/vaults",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=StakingListVaultsResponse,
        )


class AsyncStakingResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncStakingResourceWithRawResponse:
        """
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/stainless-sdks/earn-app-python#accessing-raw-response-data-eg-headers
        """
        return AsyncStakingResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncStakingResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/stainless-sdks/earn-app-python#with_streaming_response
        """
        return AsyncStakingResourceWithStreamingResponse(self)

    async def list_vaults(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> StakingListVaultsResponse:
        """Retrieve all available staking vaults"""
        return await self._get(
            "/staking/vaults",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=StakingListVaultsResponse,
        )


class StakingResourceWithRawResponse:
    def __init__(self, staking: StakingResource) -> None:
        self._staking = staking

        self.list_vaults = to_raw_response_wrapper(
            staking.list_vaults,
        )


class AsyncStakingResourceWithRawResponse:
    def __init__(self, staking: AsyncStakingResource) -> None:
        self._staking = staking

        self.list_vaults = async_to_raw_response_wrapper(
            staking.list_vaults,
        )


class StakingResourceWithStreamingResponse:
    def __init__(self, staking: StakingResource) -> None:
        self._staking = staking

        self.list_vaults = to_streamed_response_wrapper(
            staking.list_vaults,
        )


class AsyncStakingResourceWithStreamingResponse:
    def __init__(self, staking: AsyncStakingResource) -> None:
        self._staking = staking

        self.list_vaults = async_to_streamed_response_wrapper(
            staking.list_vaults,
        )
