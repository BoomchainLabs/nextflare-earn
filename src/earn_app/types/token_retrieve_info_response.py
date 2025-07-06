# File generated from our OpenAPI spec by Stainless. See CONTRIBUTING.md for details.

from typing import List, Optional

from pydantic import Field as FieldInfo

from .._models import BaseModel

__all__ = ["TokenRetrieveInfoResponse", "Listing"]


class Listing(BaseModel):
    exchange: Optional[str] = None
    """Exchange name"""

    pair: Optional[str] = None
    """Trading pair"""

    url: Optional[str] = None
    """Link to exchange"""


class TokenRetrieveInfoResponse(BaseModel):
    address: Optional[str] = None
    """Token contract address"""

    circulating_supply: Optional[float] = FieldInfo(alias="circulatingSupply", default=None)
    """Circulating token supply"""

    decimals: Optional[int] = None
    """Token decimals"""

    listings: Optional[List[Listing]] = None
    """Exchanges where the token is listed"""

    market_cap: Optional[float] = FieldInfo(alias="marketCap", default=None)
    """Current market capitalization"""

    name: Optional[str] = None
    """Token name"""

    price: Optional[float] = None
    """Current token price in USD"""

    price_change24h: Optional[float] = FieldInfo(alias="priceChange24h", default=None)
    """24-hour price change percentage"""

    symbol: Optional[str] = None
    """Token symbol"""

    total_supply: Optional[float] = FieldInfo(alias="totalSupply", default=None)
    """Total token supply"""

    volume24h: Optional[float] = None
    """24-hour trading volume"""
