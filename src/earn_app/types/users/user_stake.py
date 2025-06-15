# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from ..._models import BaseModel
from ..staking_vault import StakingVault

__all__ = ["UserStake"]


class UserStake(BaseModel):
    id: Optional[int] = None
    """Unique stake identifier"""

    amount: Optional[float] = None
    """Staked amount"""

    auto_compound: Optional[bool] = FieldInfo(alias="autoCompound", default=None)
    """Whether rewards are auto-compounded"""

    end_date: Optional[datetime] = FieldInfo(alias="endDate", default=None)
    """End timestamp"""

    lock_period: Optional[int] = FieldInfo(alias="lockPeriod", default=None)
    """Lock period in days"""

    start_date: Optional[datetime] = FieldInfo(alias="startDate", default=None)
    """Start timestamp"""

    status: Optional[Literal["active", "completed", "claimed"]] = None
    """Stake status"""

    total_rewards: Optional[float] = FieldInfo(alias="totalRewards", default=None)
    """Total rewards earned"""

    user_id: Optional[int] = FieldInfo(alias="userId", default=None)
    """User identifier"""

    vault: Optional[StakingVault] = None

    vault_id: Optional[int] = FieldInfo(alias="vaultId", default=None)
    """Vault identifier"""
