# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List
from typing_extensions import TypeAlias

from .user_stake import UserStake

__all__ = ["StakeListResponse"]

StakeListResponse: TypeAlias = List[UserStake]
