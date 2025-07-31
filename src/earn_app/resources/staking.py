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
        Returns a wrapper that enables HTTP method calls to return raw HTTP response objects instead of parsed content.
        """
        return StakingResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> StakingResourceWithStreamingResponse:
        """
        Returns a wrapper that enables streaming HTTP responses for staking vault API calls.
        
        Use this property to access methods that return streamed responses, allowing you to process response data incrementally without reading the entire body at once.
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
        """
        Retrieve all available staking vaults.
        
        Sends a GET request to the `/staking/vaults` endpoint and returns a parsed response containing the list of staking vaults.
        
        Parameters:
            extra_headers (dict, optional): Additional HTTP headers to include in the request.
            extra_query (dict, optional): Additional query parameters to include in the request.
            extra_body (dict, optional): Additional body content to include in the request.
            timeout (float or httpx.Timeout, optional): Timeout setting for the request.
        
        Returns:
            StakingListVaultsResponse: Parsed response containing staking vault information.
        """
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
        Returns a wrapper that enables access to raw HTTP response objects for all staking-related API calls.
        
        Use this property to receive unparsed HTTP responses instead of parsed content when calling API methods.
        """
        return AsyncStakingResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncStakingResourceWithStreamingResponse:
        """
        Returns a wrapper that enables streamed HTTP responses for staking API calls without eagerly reading the response body.
        
        Use this property to access asynchronous staking endpoints with streaming response handling.
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
        """
        Asynchronously retrieves all available staking vaults.
        
        Parameters:
            extra_headers: Optional additional HTTP headers to include in the request.
            extra_query: Optional additional query parameters to include in the request.
            extra_body: Optional additional body content to include in the request.
            timeout: Optional timeout setting for the request.
        
        Returns:
            StakingListVaultsResponse: Parsed response containing the list of staking vaults.
        """
        return await self._get(
            "/staking/vaults",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=StakingListVaultsResponse,
        )


class StakingResourceWithRawResponse:
    def __init__(self, staking: StakingResource) -> None:
        """
        Initialize the wrapper to provide raw HTTP responses for staking vault operations.
        
        Parameters:
            staking (StakingResource): The staking resource instance to wrap.
        """
        self._staking = staking

        self.list_vaults = to_raw_response_wrapper(
            staking.list_vaults,
        )


class AsyncStakingResourceWithRawResponse:
    def __init__(self, staking: AsyncStakingResource) -> None:
        """
        Initialize the wrapper to provide raw HTTP responses for asynchronous staking vault operations.
        
        Parameters:
            staking (AsyncStakingResource): The asynchronous staking resource to wrap.
        """
        self._staking = staking

        self.list_vaults = async_to_raw_response_wrapper(
            staking.list_vaults,
        )


class StakingResourceWithStreamingResponse:
    def __init__(self, staking: StakingResource) -> None:
        """
        Initialize the streaming response wrapper for staking resource methods.
        
        Parameters:
            staking (StakingResource): The staking resource instance to wrap.
        """
        self._staking = staking

        self.list_vaults = to_streamed_response_wrapper(
            staking.list_vaults,
        )


class AsyncStakingResourceWithStreamingResponse:
    def __init__(self, staking: AsyncStakingResource) -> None:
        """
        Initialize the streaming response wrapper for asynchronous staking resource methods.
        
        Parameters:
            staking (AsyncStakingResource): The asynchronous staking resource to be wrapped.
        """
        self._staking = staking

        self.list_vaults = async_to_streamed_response_wrapper(
            staking.list_vaults,
        )
