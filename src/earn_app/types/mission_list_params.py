# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Literal, TypedDict

__all__ = ["MissionListParams"]


class MissionListParams(TypedDict, total=False):
    category: str
    """Filter missions by category"""

    status: Literal["active", "inactive", "completed"]
    """Filter missions by status"""
