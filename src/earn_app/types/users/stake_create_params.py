# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from ..._utils import PropertyInfo

__all__ = ["StakeCreateParams"]


class StakeCreateParams(TypedDict, total=False):
    amount: Required[float]
    """Amount to stake"""

    vault_id: Required[Annotated[int, PropertyInfo(alias="vaultId")]]
    """Vault identifier"""

    auto_compound: Annotated[bool, PropertyInfo(alias="autoCompound")]
    """Whether to auto-compound rewards"""

    lock_period: Annotated[int, PropertyInfo(alias="lockPeriod")]
    """Lock period in days"""
