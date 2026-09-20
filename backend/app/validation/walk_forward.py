"""
Walk-Forward Validation Engine
================================
Prevents single-period fitting by rolling train/test windows.

Architecture:
  Historical period → Calibration → Out-of-sample test → Move window → Repeat
"""

from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd

from app.quant import formulas as f


class WalkForwardResult:
    def __init__(self):
        self.windows: list[dict] = []
        self.oos_returns: list[float] = []
        self.oos_sharpes: list[float] = []
        self.is_sharpes: list[float] = []

    def to_dict(self) -> dict:
        return {
            "num_windows": len(self.windows),
            "windows": self.windows,
            "oos_mean_return": float(np.mean(self.oos_returns)) if self.oos_returns else 0.0,
            "oos_mean_sharpe": float(np.mean(self.oos_sharpes)) if self.oos_sharpes else 0.0,
            "is_mean_sharpe": float(np.mean(self.is_sharpes)) if self.is_sharpes else 0.0,
            "performance_decay": _performance_decay(self.is_sharpes, self.oos_sharpes),
            "oos_consistency": _consistency_ratio(self.oos_sharpes),
        }


def walk_forward_validation(
    returns: pd.Series,
    strategy_fn: Callable[[pd.Series], pd.Series],
    train_size: int = 252,
    test_size: int = 63,
    step_size: int | None = None,
    risk_free_rate: float = 0.05,
    trading_days: int = 252,
) -> WalkForwardResult:
    """
    Run walk-forward validation.

    Parameters
    ----------
    returns : pd.Series
        Full return series.
    strategy_fn : callable
        Given a return series, returns strategy returns for the period.
    train_size : int
        Number of observations for training window.
    test_size : int
        Number of observations for test window.
    step_size : int | None
        Steps to advance each iteration (defaults to test_size).
    risk_free_rate : float
    trading_days : int
    """
    if step_size is None:
        step_size = test_size

    result = WalkForwardResult()
    n = len(returns)
    start = 0

    while start + train_size + test_size <= n:
        train_end = start + train_size
        test_end = train_end + test_size

        train_returns = returns.iloc[start:train_end]
        test_returns = returns.iloc[train_end:test_end]

        # Run strategy on train and test
        is_strat_returns = strategy_fn(train_returns)
        oos_strat_returns = strategy_fn(test_returns)

        is_sharpe = f.sharpe_ratio(is_strat_returns, risk_free_rate, trading_days)
        oos_sharpe = f.sharpe_ratio(oos_strat_returns, risk_free_rate, trading_days)
        oos_ret = f.annualized_return(oos_strat_returns, trading_days)

        window_info = {
            "window_id": len(result.windows),
            "train_start": str(returns.index[start]) if hasattr(returns.index[start], 'strftime') else start,
            "train_end": str(returns.index[train_end - 1]) if hasattr(returns.index[train_end - 1], 'strftime') else train_end - 1,
            "test_start": str(returns.index[train_end]) if hasattr(returns.index[train_end], 'strftime') else train_end,
            "test_end": str(returns.index[test_end - 1]) if hasattr(returns.index[test_end - 1], 'strftime') else test_end - 1,
            "is_sharpe": is_sharpe,
            "oos_sharpe": oos_sharpe,
            "oos_return": oos_ret,
        }

        result.windows.append(window_info)
        result.oos_returns.append(oos_ret)
        result.oos_sharpes.append(oos_sharpe)
        result.is_sharpes.append(is_sharpe)

        start += step_size

    return result


def _performance_decay(is_sharpes: list[float], oos_sharpes: list[float]) -> float:
    """Ratio of OOS to IS performance — values close to 1.0 are good."""
    if not is_sharpes or not oos_sharpes:
        return 0.0
    is_mean = np.mean(is_sharpes)
    oos_mean = np.mean(oos_sharpes)
    if is_mean == 0:
        return 0.0
    return float(1.0 - oos_mean / is_mean)


def _consistency_ratio(oos_sharpes: list[float]) -> float:
    """Fraction of OOS windows with positive Sharpe."""
    if not oos_sharpes:
        return 0.0
    positive = sum(1 for s in oos_sharpes if s > 0)
    return float(positive / len(oos_sharpes))
