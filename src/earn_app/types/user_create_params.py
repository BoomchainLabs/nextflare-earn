# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from __future__ import annotations

from typing_extensions import Required, Annotated, TypedDict

from .._utils import PropertyInfo

__all__ = ["UserCreateParams"]


class UserCreateParams(TypedDict, total=False):
    wallet_address: Required[Annotated[str, PropertyInfo(alias="walletAddress")]]
    """User's blockchain wallet address"""

    email: str
    """User's email address"""

    referral_code: Annotated[str, PropertyInfo(alias="referralCode")]
    """Referral code used during signup"""

    username: str
    """User's chosen username"""
