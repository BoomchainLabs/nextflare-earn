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
from ..types.token_retrieve_info_response import TokenRetrieveInfoResponse

__all__ = ["TokenResource", "AsyncTokenResource"]


class TokenResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> TokenResourceWithRawResponse:
        """
        Returns a wrapper that enables retrieval of raw HTTP response objects for token-related API calls.
        
        Use this property to access the full HTTP response, including headers and status code, instead of just the parsed content.
        """
        return TokenResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> TokenResourceWithStreamingResponse:
        """
        Returns a wrapper that enables streaming response handling for token information requests.
        
        Use this property to access the response body as a stream, allowing processing of large or partial responses without loading the entire content into memory.
        """
        return TokenResourceWithStreamingResponse(self)

    def retrieve_info(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> TokenRetrieveInfoResponse:
        """
        Retrieve the latest information about the $LERF token.
        
        Parameters:
            extra_headers (dict, optional): Additional HTTP headers to include in the request.
            extra_query (dict, optional): Additional query parameters for the request.
            extra_body (dict, optional): Additional body content for the request.
            timeout (float or httpx.Timeout, optional): Timeout setting for the request.
        
        Returns:
            TokenRetrieveInfoResponse: Parsed response containing $LERF token information.
        """
        return self._get(
            "/token/info",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=TokenRetrieveInfoResponse,
        )


class AsyncTokenResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncTokenResourceWithRawResponse:
        """
        Returns a wrapper that enables retrieval of raw HTTP response objects for all API method calls.
        
        Use this property to access full response details, such as headers and status codes, instead of only parsed content.
        """
        return AsyncTokenResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncTokenResourceWithStreamingResponse:
        """
        Returns a wrapper that enables streamed response handling for the token info endpoint without eagerly reading the response body.
        
        Returns:
            AsyncTokenResourceWithStreamingResponse: Wrapper for handling streamed HTTP responses asynchronously.
        """
        return AsyncTokenResourceWithStreamingResponse(self)

    async def retrieve_info(
        self,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> TokenRetrieveInfoResponse:
        """
        Asynchronously retrieve the latest information about the $LERF token.
        
        Parameters:
            extra_headers: Optional additional HTTP headers to include in the request.
            extra_query: Optional additional query parameters for the request.
            extra_body: Optional additional body content for the request.
            timeout: Optional timeout setting for the request.
        
        Returns:
            TokenRetrieveInfoResponse: Parsed response containing $LERF token information.
        """
        return await self._get(
            "/token/info",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=TokenRetrieveInfoResponse,
        )


class TokenResourceWithRawResponse:
    def __init__(self, token: TokenResource) -> None:
        """
        Initialize the wrapper to provide raw HTTP responses for token information retrieval.
        
        Parameters:
            token (TokenResource): The underlying token resource to be wrapped.
        """
        self._token = token

        self.retrieve_info = to_raw_response_wrapper(
            token.retrieve_info,
        )


class AsyncTokenResourceWithRawResponse:
    def __init__(self, token: AsyncTokenResource) -> None:
        """
        Initialize the wrapper to provide raw HTTP responses for asynchronous token info retrieval.
        
        Parameters:
            token (AsyncTokenResource): The asynchronous token resource to wrap.
        """
        self._token = token

        self.retrieve_info = async_to_raw_response_wrapper(
            token.retrieve_info,
        )


class TokenResourceWithStreamingResponse:
    def __init__(self, token: TokenResource) -> None:
        """
        Initialize the streaming response wrapper for the TokenResource.
        
        Replaces the `retrieve_info` method to return a streamed HTTP response instead of eagerly reading the response body.
        """
        self._token = token

        self.retrieve_info = to_streamed_response_wrapper(
            token.retrieve_info,
        )


class AsyncTokenResourceWithStreamingResponse:
    def __init__(self, token: AsyncTokenResource) -> None:
        """
        Initialize the streaming response wrapper for the asynchronous token resource.
        
        Parameters:
            token (AsyncTokenResource): The asynchronous token resource to be wrapped for streaming responses.
        """
        self._token = token

        self.retrieve_info = async_to_streamed_response_wrapper(
            token.retrieve_info,
        )
