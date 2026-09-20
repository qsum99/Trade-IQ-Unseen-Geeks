"""
Common schemas used across all domains.
Shared response envelope, pagination, error codes.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: str
    message: str
    details: dict[str, Any] = Field(default_factory=dict)


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T | None = None
    meta: dict[str, Any] = Field(default_factory=dict)
    error: ErrorDetail | None = None


class ErrorResponse(BaseModel):
    success: bool = False
    data: None = None
    meta: dict[str, Any] = Field(default_factory=dict)
    error: ErrorDetail


# Central error codes
ERROR_CODES = {
    "INVALID_REQUEST",
    "INVALID_PARAMETER",
    "ASSET_NOT_FOUND",
    "DATA_NOT_FOUND",
    "DATA_PROVIDER_ERROR",
    "DATA_VALIDATION_FAILED",
    "INSUFFICIENT_DATA",
    "INTERNAL_ERROR",
}


# ── Enums ───────────────────────────────────────────────────────────────

class AssetClass(str, Enum):
    EQUITY = "equity"
    CRYPTO = "crypto"
    COMMODITY = "commodity"
    MACRO = "macro"
    INDEX = "index"


class Provider(str, Enum):
    YAHOO = "yahoo"
    BINANCE = "binance"
    NSE = "nse"
    ZERODHA = "zerodha"
    FRED = "fred"
    GOLD = "gold"
    COINGECKO = "coingecko"


class Interval(str, Enum):
    ONE_MIN = "1m"
    FIVE_MIN = "5m"
    FIFTEEN_MIN = "15m"
    ONE_HOUR = "1h"
    DAILY = "1d"
    WEEKLY = "1wk"
    MONTHLY = "1mo"


class SignalType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"
    HOLD = "HOLD"


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class RegimeLabel(str, Enum):
    BULL = "bull"
    BEAR = "bear"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"


# ── Helpers ─────────────────────────────────────────────────────────────

def make_request_id() -> str:
    return f"req_{uuid.uuid4().hex[:12]}"
