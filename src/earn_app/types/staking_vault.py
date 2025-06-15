# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from typing_extensions import Literal

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["StakingVault", "Reward"]


class Reward(BaseModel):
    id: Optional[int] = None
    """Unique reward identifier"""

    description: Optional[str] = None
    """Reward description"""

    distribution: Optional[Literal["daily", "weekly", "monthly", "end"]] = None
    """When the reward is distributed"""

    rate: Optional[float] = None
    """Reward rate"""

    type: Optional[Literal["token", "nft", "boost", "other"]] = None
    """Type of reward"""


class StakingVault(BaseModel):
    id: Optional[int] = None
    """Unique vault identifier"""

    active: Optional[bool] = None
    """Whether the vault is active"""

    apr: Optional[float] = None
    """Annual percentage rate"""

    description: Optional[str] = None
    """Vault description"""

    min_lock_period: Optional[int] = FieldInfo(alias="minLockPeriod", default=None)
    """Minimum lock period in days"""

    name: Optional[str] = None
    """Vault name"""

    rewards: Optional[List[Reward]] = None
    """Rewards offered by this vault"""

    total_staked: Optional[float] = FieldInfo(alias="totalStaked", default=None)
    """Total amount staked in this vault"""
