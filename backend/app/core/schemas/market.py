"""
Market data schemas – canonical representation for all providers.
"""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel, Field

from .common import AssetClass, Interval, Provider


class MarketData(BaseModel):
    """Canonical market-data record normalised from any provider."""
    timestamp: datetime
    symbol: str
    open: float
    high: float
    low: float
    close: float
    adjusted_close: float | None = None
    volume: float | None = None
    currency: str = "USD"
    exchange: str = "UNKNOWN"
    provider: str = "mock"
    interval: str = "1d"


class Asset(BaseModel):
    symbol: str
    name: str
    asset_class: str = "equity"  # equity | crypto | commodity | index | macro
    currency: str = "USD"
    exchange: str = "UNKNOWN"
    provider: str = "mock"
    active: bool = True


class HistoryRequest(BaseModel):
    symbol: str
    start_date: str
    end_date: str
    interval: Interval = Interval.DAILY
    provider: Provider | None = None
    adjusted: bool = True


class DataQualityReport(BaseModel):
    symbol: str
    records: int
    missing_values: int = 0
    duplicate_records: int = 0
    invalid_prices: int = 0
    date_gaps: int = 0
    quality_score: float = 100.0


SUPPORTED_ASSETS: list[Asset] = [
    Asset(symbol="NVDA", name="NVIDIA Corporation", asset_class="equity", currency="USD", exchange="NASDAQ", provider="yahoo"),
    Asset(symbol="RELIANCE.NS", name="Reliance Industries", asset_class="equity", currency="INR", exchange="NSE", provider="yahoo"),
    Asset(symbol="BTC-USD", name="Bitcoin", asset_class="crypto", currency="USD", exchange="CRYPTO", provider="binance"),
    Asset(symbol="GC=F", name="Gold Futures", asset_class="commodity", currency="USD", exchange="COMEX", provider="yahoo"),
    Asset(symbol="^NSEI", name="Nifty 50", asset_class="index", currency="INR", exchange="NSE", provider="yahoo"),
]
