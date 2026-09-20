"""Backtesting package: execution simulator + engine (samarth.md §4)."""

from samarth_work.backtesting.engine import BacktestEngine
from samarth_work.backtesting.execution import (
    ExecutionConfig,
    apply_slippage,
    estimate_impact,
    resolve_price,
)

__all__ = [
    "BacktestEngine",
    "ExecutionConfig",
    "apply_slippage",
    "estimate_impact",
    "resolve_price",
]
