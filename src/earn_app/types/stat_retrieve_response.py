# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["StatRetrieveResponse"]


class StatRetrieveResponse(BaseModel):
    active_missions: Optional[int] = FieldInfo(alias="activeMissions", default=None)
    """Number of active missions"""

    active_quests: Optional[int] = FieldInfo(alias="activeQuests", default=None)
    """Number of active quests"""

    daily_active_users: Optional[int] = FieldInfo(alias="dailyActiveUsers", default=None)
    """Daily active users"""

    monthly_active_users: Optional[int] = FieldInfo(alias="monthlyActiveUsers", default=None)
    """Monthly active users"""

    total_staked: Optional[float] = FieldInfo(alias="totalStaked", default=None)
    """Total amount staked across all vaults"""

    total_tokens_distributed: Optional[float] = FieldInfo(alias="totalTokensDistributed", default=None)
    """Total tokens distributed as rewards"""

    total_users: Optional[int] = FieldInfo(alias="totalUsers", default=None)
    """Total number of users"""

    weekly_active_users: Optional[int] = FieldInfo(alias="weeklyActiveUsers", default=None)
    """Weekly active users"""
