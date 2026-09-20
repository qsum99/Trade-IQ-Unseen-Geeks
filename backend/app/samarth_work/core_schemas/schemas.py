"""Shared-contract schemas (work_divide §5, api.md §3). Stdlib dataclasses.

Mirrors quantum-hackthon/backend/app/core/schemas/*.py.
Field names are FROZEN for Day-0 contract compatibility.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class MarketBar:
    timestamp: str  # ISO date, e.g. "2024-01-02"
    symbol: str
    open: float
    high: float
    low: float
    close: float
    adjusted_close: float | None = None
    volume: float | None = None
    currency: str = "INR"
    exchange: str = "NSE"
    provider: str = "synthetic"


@dataclass
class StrategySignal:
    date: str
    signal: str  # BUY | SELL | HOLD
    price: float


@dataclass
class Trade:
    id: int
    date: str
    side: str  # BUY | SELL
    price: float  # execution fill price
    quantity: float
    transaction_cost: float


@dataclass
class EquityPoint:
    date: str
    portfolio_value: float
    benchmark_value: float = 0.0


@dataclass
class BacktestRequest:
    symbol: str = "RELIANCE"
    strategy: str = "sma_crossover"
    parameters: dict = field(default_factory=dict)
    start_date: str = ""
    end_date: str = ""
    initial_capital: float = 100000.0
    position_sizing: str = "full"  # full | fixed | risk_based
    fixed_quantity: float = 0.0
    risk_fraction: float = 0.01
    stop_distance: float = 10.0
    transaction_cost: float = 0.001
    slippage: float = 0.0005
    execution_price: str = "next_open"  # next_open | next_close
    benchmark: str = "buy_and_hold"
    risk_free_rate: float = 0.0  # annualized, for Sharpe (math_eq §12)


@dataclass
class BacktestResult:
    backtest_id: str
    status: str
    initial_capital: float
    final_value: float
    total_return: float
    sharpe: float = 0.0
    volatility: float = 0.0
    max_drawdown: float = 0.0
    total_trades: int = 0
    win_rate: float = 0.0
    profit_factor: float = 0.0


def envelope(data: object, request_id: str = "req_local") -> dict:
    return {"success": True, "data": data, "meta": {"request_id": request_id}, "error": None}


def error_envelope(code: str, message: str, request_id: str = "req_local") -> dict:
    return {
        "success": False,
        "data": None,
        "meta": {"request_id": request_id},
        "error": {"code": code, "message": message, "details": {}},
    }
