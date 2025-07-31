# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal

import httpx

from ..types import mission_list_params
from .._types import NOT_GIVEN, Body, Query, Headers, NotGiven
from .._utils import maybe_transform, async_maybe_transform
from .._compat import cached_property
from .._resource import SyncAPIResource, AsyncAPIResource
from .._response import (
    to_raw_response_wrapper,
    to_streamed_response_wrapper,
    async_to_raw_response_wrapper,
    async_to_streamed_response_wrapper,
)
from .._base_client import make_request_options
from ..types.mission import Mission
from ..types.mission_list_response import MissionListResponse

__all__ = ["MissionsResource", "AsyncMissionsResource"]


class MissionsResource(SyncAPIResource):
    @cached_property
    def with_raw_response(self) -> MissionsResourceWithRawResponse:
        """
        Returns a wrapper that enables all HTTP method calls to return raw HTTP response objects instead of parsed data.
        
        Use this property to access response metadata such as headers and status codes directly.
        """
        return MissionsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> MissionsResourceWithStreamingResponse:
        """
        Returns a wrapper that enables streaming HTTP responses for all methods without buffering the response body.
        
        Use this to access response data as a stream rather than as a fully-read object.
        """
        return MissionsResourceWithStreamingResponse(self)

    def retrieve(
        self,
        id: int,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> Mission:
        """
        Retrieve detailed information about a mission by its unique ID.
        
        Parameters:
            id (int): The unique identifier of the mission to retrieve.
        
        Returns:
            Mission: The mission object containing detailed information.
        """
        return self._get(
            f"/missions/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Mission,
        )

    def list(
        self,
        *,
        category: str | NotGiven = NOT_GIVEN,
        status: Literal["active", "inactive", "completed"] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> MissionListResponse:
        """
        Retrieve a list of missions, optionally filtered by category and status.
        
        Parameters:
            category (str, optional): Filter missions by category.
            status (Literal["active", "inactive", "completed"], optional): Filter missions by status.
        
        Returns:
            MissionListResponse: A response object containing the list of missions matching the specified filters.
        """
        return self._get(
            "/missions",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=maybe_transform(
                    {
                        "category": category,
                        "status": status,
                    },
                    mission_list_params.MissionListParams,
                ),
            ),
            cast_to=MissionListResponse,
        )


class AsyncMissionsResource(AsyncAPIResource):
    @cached_property
    def with_raw_response(self) -> AsyncMissionsResourceWithRawResponse:
        """
        Returns a wrapper that enables all API methods to return raw HTTP response objects instead of parsed data.
        
        Use this property to access response metadata such as headers and status codes for all asynchronous mission API calls.
        """
        return AsyncMissionsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncMissionsResourceWithStreamingResponse:
        """
        Returns a wrapper that enables streaming HTTP responses for all methods without buffering the response body.
        
        Use this to access response data as a stream rather than as a fully-read object.
        """
        return AsyncMissionsResourceWithStreamingResponse(self)

    async def retrieve(
        self,
        id: int,
        *,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> Mission:
        """
        Asynchronously retrieves detailed information about a mission by its unique ID.
        
        Parameters:
            id (int): The unique identifier of the mission to retrieve.
        
        Returns:
            Mission: The mission object containing detailed information.
        """
        return await self._get(
            f"/missions/{id}",
            options=make_request_options(
                extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
            ),
            cast_to=Mission,
        )

    async def list(
        self,
        *,
        category: str | NotGiven = NOT_GIVEN,
        status: Literal["active", "inactive", "completed"] | NotGiven = NOT_GIVEN,
        # Use the following arguments if you need to pass additional parameters to the API that aren't available via kwargs.
        # The extra values given here take precedence over values defined on the client or passed to this method.
        extra_headers: Headers | None = None,
        extra_query: Query | None = None,
        extra_body: Body | None = None,
        timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    ) -> MissionListResponse:
        """
        Asynchronously retrieves a list of missions, optionally filtered by category and status.
        
        Parameters:
            category (str, optional): Filter missions by category.
            status (Literal["active", "inactive", "completed"], optional): Filter missions by status.
        
        Returns:
            MissionListResponse: A response object containing the list of missions matching the provided filters.
        """
        return await self._get(
            "/missions",
            options=make_request_options(
                extra_headers=extra_headers,
                extra_query=extra_query,
                extra_body=extra_body,
                timeout=timeout,
                query=await async_maybe_transform(
                    {
                        "category": category,
                        "status": status,
                    },
                    mission_list_params.MissionListParams,
                ),
            ),
            cast_to=MissionListResponse,
        )


class MissionsResourceWithRawResponse:
    def __init__(self, missions: MissionsResource) -> None:
        """
        Initialize a wrapper for MissionsResource methods to return raw HTTP responses.
        
        Parameters:
        	missions (MissionsResource): The missions resource instance to wrap.
        """
        self._missions = missions

        self.retrieve = to_raw_response_wrapper(
            missions.retrieve,
        )
        self.list = to_raw_response_wrapper(
            missions.list,
        )


class AsyncMissionsResourceWithRawResponse:
    def __init__(self, missions: AsyncMissionsResource) -> None:
        """
        Initialize the wrapper to provide raw HTTP responses for asynchronous mission resource methods.
        
        Parameters:
        	missions (AsyncMissionsResource): The asynchronous missions resource to wrap.
        """
        self._missions = missions

        self.retrieve = async_to_raw_response_wrapper(
            missions.retrieve,
        )
        self.list = async_to_raw_response_wrapper(
            missions.list,
        )


class MissionsResourceWithStreamingResponse:
    def __init__(self, missions: MissionsResource) -> None:
        """
        Initialize a streaming response wrapper for the MissionsResource.
        
        Wraps the `retrieve` and `list` methods to return streaming HTTP responses instead of parsed content.
        """
        self._missions = missions

        self.retrieve = to_streamed_response_wrapper(
            missions.retrieve,
        )
        self.list = to_streamed_response_wrapper(
            missions.list,
        )


class AsyncMissionsResourceWithStreamingResponse:
    def __init__(self, missions: AsyncMissionsResource) -> None:
        """
        Initialize the streaming response wrapper for asynchronous missions API methods.
        
        Parameters:
        	missions (AsyncMissionsResource): The asynchronous missions resource to wrap.
        """
        self._missions = missions

        self.retrieve = async_to_streamed_response_wrapper(
            missions.retrieve,
        )
        self.list = async_to_streamed_response_wrapper(
            missions.list,
        )
