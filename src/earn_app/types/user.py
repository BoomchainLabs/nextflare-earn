# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import Optional
from datetime import datetime

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["User"]


class User(BaseModel):
    id: Optional[int] = None
    """Unique user identifier"""

    created_at: Optional[datetime] = FieldInfo(alias="createdAt", default=None)
    """User creation timestamp"""

    email: Optional[str] = None
    """User's email address"""

    level: Optional[int] = None
    """User's current level"""

    referral_code: Optional[str] = FieldInfo(alias="referralCode", default=None)
    """User's unique referral code"""

    total_points: Optional[int] = FieldInfo(alias="totalPoints", default=None)
    """Total points earned by the user"""

    updated_at: Optional[datetime] = FieldInfo(alias="updatedAt", default=None)
    """Last update timestamp"""

    username: Optional[str] = None
    """User's chosen username"""

    wallet_address: Optional[str] = FieldInfo(alias="walletAddress", default=None)
    """User's blockchain wallet address"""
