# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

import os
from typing import Any, cast

import pytest

from earn_app import EarnApp, AsyncEarnApp
from tests.utils import assert_matches_type
from earn_app.types import Mission, MissionListResponse

base_url = os.environ.get("TEST_API_BASE_URL", "http://127.0.0.1:4010")


class TestMissions:
    parametrize = pytest.mark.parametrize("client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    def test_method_retrieve(self, client: EarnApp) -> None:
        """
        Test retrieving a mission by ID using the synchronous EarnApp client.
        
        Asserts that the returned object is of type Mission.
        """
        mission = client.missions.retrieve(
            0,
        )
        assert_matches_type(Mission, mission, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_retrieve(self, client: EarnApp) -> None:
        """
        Test retrieving a mission by ID using the raw response interface and verify response closure, headers, and parsed type.
        """
        response = client.missions.with_raw_response.retrieve(
            0,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        mission = response.parse()
        assert_matches_type(Mission, mission, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_retrieve(self, client: EarnApp) -> None:
        """
        Test retrieving a mission using the streaming response interface and verify response state, headers, and parsed type.
        """
        with client.missions.with_streaming_response.retrieve(
            0,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            mission = response.parse()
            assert_matches_type(Mission, mission, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    def test_method_list(self, client: EarnApp) -> None:
        """
        Test that the missions list endpoint returns a MissionListResponse object.
        """
        mission = client.missions.list()
        assert_matches_type(MissionListResponse, mission, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_method_list_with_all_params(self, client: EarnApp) -> None:
        """
        Test retrieving a list of missions with all available filter parameters applied.
        
        Asserts that the response is of type MissionListResponse.
        """
        mission = client.missions.list(
            category="category",
            status="active",
        )
        assert_matches_type(MissionListResponse, mission, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_list(self, client: EarnApp) -> None:
        """
        Test that the missions list endpoint returns a closed raw HTTP response with the correct header and a valid MissionListResponse object.
        """
        response = client.missions.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        mission = response.parse()
        assert_matches_type(MissionListResponse, mission, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_list(self, client: EarnApp) -> None:
        """
        Test that the streaming response for listing missions returns the correct type and handles response closure and headers as expected.
        """
        with client.missions.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            mission = response.parse()
            assert_matches_type(MissionListResponse, mission, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncMissions:
    parametrize = pytest.mark.parametrize(
        "async_client", [False, True, {"http_client": "aiohttp"}], indirect=True, ids=["loose", "strict", "aiohttp"]
    )

    @pytest.mark.skip()
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncEarnApp) -> None:
        """
        Test retrieving a mission by ID using the asynchronous EarnApp client.
        
        Asserts that the returned object is of type Mission.
        """
        mission = await async_client.missions.retrieve(
            0,
        )
        assert_matches_type(Mission, mission, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncEarnApp) -> None:
        """
        Test that retrieving a mission with the async client using the raw response interface returns a closed response, includes the expected HTTP header, and parses to a Mission object.
        """
        response = await async_client.missions.with_raw_response.retrieve(
            0,
        )

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        mission = await response.parse()
        assert_matches_type(Mission, mission, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_retrieve(self, async_client: AsyncEarnApp) -> None:
        """
        Test retrieving a mission using the streaming response interface of the asynchronous client.
        
        Verifies that the response is open during the context, contains the expected HTTP header, and that the parsed data matches the Mission type. Ensures the response is closed after exiting the context.
        """
        async with async_client.missions.with_streaming_response.retrieve(
            0,
        ) as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            mission = await response.parse()
            assert_matches_type(Mission, mission, path=["response"])

        assert cast(Any, response.is_closed) is True

    @pytest.mark.skip()
    @parametrize
    async def test_method_list(self, async_client: AsyncEarnApp) -> None:
        """
        Test that the asynchronous missions client returns a valid MissionListResponse when listing missions.
        """
        mission = await async_client.missions.list()
        assert_matches_type(MissionListResponse, mission, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncEarnApp) -> None:
        """
        Test that the asynchronous missions list endpoint returns a MissionListResponse when called with all parameters.
        """
        mission = await async_client.missions.list(
            category="category",
            status="active",
        )
        assert_matches_type(MissionListResponse, mission, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncEarnApp) -> None:
        """
        Test that the asynchronous missions list endpoint returns a closed raw HTTP response with the expected header and correctly parses to a MissionListResponse.
        """
        response = await async_client.missions.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        mission = await response.parse()
        assert_matches_type(MissionListResponse, mission, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncEarnApp) -> None:
        """
        Test that the asynchronous streaming response for listing missions returns the correct type and handles response state and headers as expected.
        """
        async with async_client.missions.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            mission = await response.parse()
            assert_matches_type(MissionListResponse, mission, path=["response"])

        assert cast(Any, response.is_closed) is True
