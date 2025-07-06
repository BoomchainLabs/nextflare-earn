# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["Mission", "Requirement"]


class Requirement(BaseModel):
    id: Optional[int] = None
    """Unique requirement identifier"""

    description: Optional[str] = None
    """Requirement description"""

    target: Optional[int] = None
    """Target value to reach"""

    type: Optional[Literal["transaction", "social", "quiz", "game", "other"]] = None
    """Type of requirement"""

    verification_method: Optional[Literal["automatic", "manual"]] = FieldInfo(alias="verificationMethod", default=None)
    """How the requirement is verified"""


class Mission(BaseModel):
    id: Optional[int] = None
    """Unique mission identifier"""

    category: Optional[str] = None
    """Mission category"""

    description: Optional[str] = None
    """Detailed mission description"""

    end_date: Optional[datetime] = FieldInfo(alias="endDate", default=None)
    """Mission end timestamp"""

    points: Optional[int] = None
    """Points rewarded for completing the mission"""

    requirements: Optional[List[Requirement]] = None
    """List of requirements to complete the mission"""

    start_date: Optional[datetime] = FieldInfo(alias="startDate", default=None)
    """Mission start timestamp"""

    status: Optional[Literal["active", "inactive", "completed"]] = None
    """Current mission status"""

    title: Optional[str] = None
    """Mission title"""

    token_reward: Optional[float] = FieldInfo(alias="tokenReward", default=None)
    """Token amount rewarded for completing the mission"""
