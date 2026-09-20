"""Strategies package: re-exports + registry (work_divide §§13-14)."""
from samarth_work.strategies.base import Strategy
from samarth_work.strategies.ema import EmaTrend
from samarth_work.strategies.mean_reversion import MeanReversion
from samarth_work.strategies.momentum import MomentumStrategy
from samarth_work.strategies.regime import DEFAULT_MAPPING, RegimeAdaptive
from samarth_work.strategies.registry import STRATEGIES, describe, get_strategy
from samarth_work.strategies.sma import SmaCrossover

__all__ = [
    "Strategy",
    "SmaCrossover",
    "EmaTrend",
    "MomentumStrategy",
    "MeanReversion",
    "RegimeAdaptive",
    "DEFAULT_MAPPING",
    "STRATEGIES",
    "get_strategy",
    "describe",
]
