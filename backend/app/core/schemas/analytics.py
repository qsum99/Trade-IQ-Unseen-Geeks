"""Analytics request/response contracts. Owned by Satish."""
from __future__ import annotations

from pydantic import BaseModel, Field


class IndicatorRequest(BaseModel):
    symbol: str = "NVDA"
    start_date: str = "2024-01-01"
    end_date: str = "2025-01-01"
    period: int = 20
    window: int = 20
    risk_free_rate: float = 0.05
    annualization_factor: int = 252
    method: str = "simple"  # simple | log


class IndicatorPoint(BaseModel):
    date: str
    value: float | None = None


class AnalyticsSummaryRequest(BaseModel):
    symbol: str = "NVDA"
    start_date: str = "2024-01-01"
    end_date: str = "2025-01-01"
    indicators: dict = Field(default_factory=lambda: {"sma": [20, 50], "ema": [20], "returns": True, "volatility": True, "sharpe": True, "drawdown": True})


class CorrelationMatrixRequest(BaseModel):
    symbols: list[str] = Field(default_factory=lambda: ["BTC-USD", "NVDA", "GC=F"])
    start_date: str = "2024-01-01"
    end_date: str = "2025-01-01"
    method: str = "pearson"


class RollingCorrelationRequest(BaseModel):
    symbols: list[str] = Field(default_factory=lambda: ["BTC-USD", "NVDA"])
    window: int = 30
    start_date: str = "2024-01-01"
    end_date: str = "2025-01-01"


class DataValidateRequest(BaseModel):
    symbol: str = "NVDA"
    start_date: str = "2024-01-01"
    end_date: str = "2025-01-01"
    provider: str = "yahoo"
