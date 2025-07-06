# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional
from datetime import datetime
from typing_extensions import TypeAlias

from pydantic import Field as FieldInfo

from .mission import Mission
from .._models import BaseModel

__all__ = ["UserListMissionsResponse", "UserListMissionsResponseItem"]


class UserListMissionsResponseItem(BaseModel):
    id: Optional[int] = None
    """Unique progress identifier"""

    claimed: Optional[bool] = None
    """Whether the reward has been claimed"""

    claimed_at: Optional[datetime] = FieldInfo(alias="claimedAt", default=None)
    """Reward claim timestamp"""

    completed: Optional[bool] = None
    """Whether the mission is completed"""

    completed_at: Optional[datetime] = FieldInfo(alias="completedAt", default=None)
    """Completion timestamp"""

    mission: Optional[Mission] = None

    mission_id: Optional[int] = FieldInfo(alias="missionId", default=None)
    """Mission identifier"""

    progress: Optional[float] = None
    """Current progress percentage (0-100)"""

    user_id: Optional[int] = FieldInfo(alias="userId", default=None)
    """User identifier"""


UserListMissionsResponse: TypeAlias = List[UserListMissionsResponseItem]
