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
        mission = client.missions.retrieve(
            0,
        )
        assert_matches_type(Mission, mission, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_retrieve(self, client: EarnApp) -> None:
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
        mission = client.missions.list()
        assert_matches_type(MissionListResponse, mission, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_method_list_with_all_params(self, client: EarnApp) -> None:
        mission = client.missions.list(
            category="category",
            status="active",
        )
        assert_matches_type(MissionListResponse, mission, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_raw_response_list(self, client: EarnApp) -> None:
        response = client.missions.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        mission = response.parse()
        assert_matches_type(MissionListResponse, mission, path=["response"])

    @pytest.mark.skip()
    @parametrize
    def test_streaming_response_list(self, client: EarnApp) -> None:
        with client.missions.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            mission = response.parse()
            assert_matches_type(MissionListResponse, mission, path=["response"])

        assert cast(Any, response.is_closed) is True


class TestAsyncMissions:
    parametrize = pytest.mark.parametrize("async_client", [False, True], indirect=True, ids=["loose", "strict"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_retrieve(self, async_client: AsyncEarnApp) -> None:
        mission = await async_client.missions.retrieve(
            0,
        )
        assert_matches_type(Mission, mission, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_retrieve(self, async_client: AsyncEarnApp) -> None:
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
        mission = await async_client.missions.list()
        assert_matches_type(MissionListResponse, mission, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_method_list_with_all_params(self, async_client: AsyncEarnApp) -> None:
        mission = await async_client.missions.list(
            category="category",
            status="active",
        )
        assert_matches_type(MissionListResponse, mission, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_raw_response_list(self, async_client: AsyncEarnApp) -> None:
        response = await async_client.missions.with_raw_response.list()

        assert response.is_closed is True
        assert response.http_request.headers.get("X-Stainless-Lang") == "python"
        mission = await response.parse()
        assert_matches_type(MissionListResponse, mission, path=["response"])

    @pytest.mark.skip()
    @parametrize
    async def test_streaming_response_list(self, async_client: AsyncEarnApp) -> None:
        async with async_client.missions.with_streaming_response.list() as response:
            assert not response.is_closed
            assert response.http_request.headers.get("X-Stainless-Lang") == "python"

            mission = await response.parse()
            assert_matches_type(MissionListResponse, mission, path=["response"])

        assert cast(Any, response.is_closed) is True
