# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime
from typing_extensions import Literal, TypeAlias

from pydantic import Field as FieldInfo

from .user import User
from .._models import BaseModel

__all__ = ["UserListReferralsResponse", "UserListReferralsResponseItem"]


class UserListReferralsResponseItem(BaseModel):
    id: Optional[int] = None
    """Unique referral identifier"""

    code: Optional[str] = None
    """Referral code used"""

    created_at: Optional[datetime] = FieldInfo(alias="createdAt", default=None)
    """Referral creation timestamp"""

    referee: Optional[User] = None

    referee_id: Optional[int] = FieldInfo(alias="refereeId", default=None)
    """Referred user identifier"""

    referrer_id: Optional[int] = FieldInfo(alias="referrerId", default=None)
    """Referrer user identifier"""

    reward_amount: Optional[float] = FieldInfo(alias="rewardAmount", default=None)
    """Reward amount given to referrer"""

    rewarded_at: Optional[datetime] = FieldInfo(alias="rewardedAt", default=None)
    """Reward timestamp"""

    status: Optional[Literal["pending", "rewarded", "expired"]] = None
    """Referral status"""


UserListReferralsResponse: TypeAlias = List[UserListReferralsResponseItem]
