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
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/stainless-sdks/earn-app-python#accessing-raw-response-data-eg-headers
        """
        return MissionsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> MissionsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/stainless-sdks/earn-app-python#with_streaming_response
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
        Retrieve detailed information about a specific mission

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
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
        Retrieve the list of all available missions

        Args:
          category: Filter missions by category

          status: Filter missions by status

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
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
        This property can be used as a prefix for any HTTP method call to return
        the raw response object instead of the parsed content.

        For more information, see https://www.github.com/stainless-sdks/earn-app-python#accessing-raw-response-data-eg-headers
        """
        return AsyncMissionsResourceWithRawResponse(self)

    @cached_property
    def with_streaming_response(self) -> AsyncMissionsResourceWithStreamingResponse:
        """
        An alternative to `.with_raw_response` that doesn't eagerly read the response body.

        For more information, see https://www.github.com/stainless-sdks/earn-app-python#with_streaming_response
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
        Retrieve detailed information about a specific mission

        Args:
          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
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
        Retrieve the list of all available missions

        Args:
          category: Filter missions by category

          status: Filter missions by status

          extra_headers: Send extra headers

          extra_query: Add additional query parameters to the request

          extra_body: Add additional JSON properties to the request

          timeout: Override the client-level default timeout for this request, in seconds
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
        self._missions = missions

        self.retrieve = to_raw_response_wrapper(
            missions.retrieve,
        )
        self.list = to_raw_response_wrapper(
            missions.list,
        )


class AsyncMissionsResourceWithRawResponse:
    def __init__(self, missions: AsyncMissionsResource) -> None:
        self._missions = missions

        self.retrieve = async_to_raw_response_wrapper(
            missions.retrieve,
        )
        self.list = async_to_raw_response_wrapper(
            missions.list,
        )


class MissionsResourceWithStreamingResponse:
    def __init__(self, missions: MissionsResource) -> None:
        self._missions = missions

        self.retrieve = to_streamed_response_wrapper(
            missions.retrieve,
        )
        self.list = to_streamed_response_wrapper(
            missions.list,
        )


class AsyncMissionsResourceWithStreamingResponse:
    def __init__(self, missions: AsyncMissionsResource) -> None:
        self._missions = missions

        self.retrieve = async_to_streamed_response_wrapper(
            missions.retrieve,
        )
        self.list = async_to_streamed_response_wrapper(
            missions.list,
        )
