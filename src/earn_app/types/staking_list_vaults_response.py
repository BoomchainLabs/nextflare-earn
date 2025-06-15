# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List
from typing_extensions import TypeAlias

from .staking_vault import StakingVault

__all__ = ["StakingListVaultsResponse"]

StakingListVaultsResponse: TypeAlias = List[StakingVault]
