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
from ..types.stat_retrieve_response import StatRetrieveResponse

__all__ = ["StatsResource", "AsyncStatsResource"]


class StatsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> StatsResourceWithRawResponse:
        """
        Returns a wrapper that enables retrieval of raw HTTP responses for stats API calls instead of parsed data.
        
        Use this property to access response metadata such as headers or status codes when calling resource methods.
        """
        return StatsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> StatsResourceWithStreamingResponse:
        """
        Returns a wrapper that enables streaming HTTP responses from the `/stats` endpoint without eagerly reading the response body.
        
        Use this property to access the `retrieve` method with streamed response handling.
        """
        return StatsResourceWithStreamingResponse(self)

    def retrieve(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> StatRetrieveResponse:
        """
        Retrieve overall platform statistics and metrics from the `/stats` endpoint.
        
        Parameters:
            extra_headers (dict, optional): Additional HTTP headers to include in the request.
            extra_query (dict, optional): Additional query parameters to include in the request.
            extra_body (dict, optional): Additional body content to include in the request.
            timeout (float or httpx.Timeout or None, optional): Override the default request timeout.
        
        Returns:
            StatRetrieveResponse: Parsed response containing platform statistics and metrics.
        """
        return self._get(
            "/stats",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=StatRetrieveResponse,
        )


class AsyncStatsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncStatsResourceWithRawResponse:
        """
        Returns a wrapper that enables retrieval of raw HTTP responses for asynchronous stats API calls.
        
        Use this property to access the full HTTP response object, including headers and status code, instead of the parsed content.
        """
        return AsyncStatsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncStatsResourceWithStreamingResponse:
        """
        Returns a wrapper that enables streaming HTTP responses for the `retrieve` method without eagerly reading the response body.
        
        Use this to process large or continuous responses efficiently.
        """
        return AsyncStatsResourceWithStreamingResponse(self)

    async def retrieve(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> StatRetrieveResponse:
        """
        Asynchronously retrieve overall platform statistics and metrics from the `/stats` endpoint.
        
        Parameters:
            extra_headers (dict, optional): Additional HTTP headers to include in the request.
            extra_query (dict, optional): Additional query parameters to include in the request.
            extra_body (dict, optional): Additional body content to include in the request.
            timeout (float or httpx.Timeout or None, optional): Timeout setting for the request.
        
        Returns:
            StatRetrieveResponse: Parsed response containing platform statistics and metrics.
        """
        return await self._get(
            "/stats",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=StatRetrieveResponse,
        )


class StatsResourceWithRawResponse:
    def __init__(self, stats: StatsResource) -> None:
        """
        Initialize the wrapper to provide raw HTTP responses for the stats resource.
        
        Parameters:
            stats (StatsResource): The stats resource instance to wrap.
        """
        self._stats = stats

        self.retrieve = to_raw_response_wrapper(
            stats.retrieve,
        )


class AsyncStatsResourceWithRawResponse:
    def __init__(self, stats: AsyncStatsResource) -> None:
        """
        Initialize the wrapper to provide raw HTTP responses for asynchronous stats retrieval.
        
        Parameters:
            stats (AsyncStatsResource): The asynchronous stats resource to wrap.
        """
        self._stats = stats

        self.retrieve = async_to_raw_response_wrapper(
            stats.retrieve,
        )


class StatsResourceWithStreamingResponse:
    def __init__(self, stats: StatsResource) -> None:
        """
        Initialize the streaming response wrapper for the StatsResource.
        
        Parameters:
            stats (StatsResource): The StatsResource instance to wrap.
        """
        self._stats = stats

        self.retrieve = to_streamed_response_wrapper(
            stats.retrieve,
        )


class AsyncStatsResourceWithStreamingResponse:
    def __init__(self, stats: AsyncStatsResource) -> None:
        """
        Initialize the streaming response wrapper for asynchronous stats retrieval.
        
        Parameters:
            stats (AsyncStatsResource): The asynchronous stats resource to wrap.
        """
        self._stats = stats

        self.retrieve = async_to_streamed_response_wrapper(
            stats.retrieve,
        )
