"""
Robustness / Stress-Testing Engine
====================================
Tests strategy stability under parameter, cost, and period perturbations.
"""

from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd

from app.quant import formulas as f


class RobustnessResult:
    def __init__(self):
        self.parameter_results: list[dict] = []
        self.cost_results: list[dict] = []
        self.period_results: list[dict] = []

    def to_dict(self) -> dict:
        return {
            "parameter_sensitivity": self.parameter_results,
            "cost_sensitivity": self.cost_results,
            "period_sensitivity": self.period_results,
            "summary": self._summary(),
        }

    def _summary(self) -> dict:
        if not self.parameter_results:
            return {}
        sharpes = [r["sharpe"] for r in self.parameter_results if r.get("sharpe")]
        return {
            "trials_tested": len(self.parameter_results),
            "best_raw_sharpe": float(max(sharpes)) if sharpes else 0.0,
            "worst_sharpe": float(min(sharpes)) if sharpes else 0.0,
            "mean_sharpe": float(np.mean(sharpes)) if sharpes else 0.0,
            "std_sharpe": float(np.std(sharpes)) if sharpes else 0.0,
            "parameter_stability": _parameter_stability(sharpes),
        }


def parameter_stress(
    returns: pd.Series,
    strategy_fn: Callable,
    param_grid: list[dict],
    risk_free_rate: float = 0.05,
    trading_days: int = 252,
) -> RobustnessResult:
    """
    Sweep strategy parameters and record performance.

    Parameters
    ----------
    returns : pd.Series
    strategy_fn : callable
        Accepts (returns, **params) and returns strategy returns.
    param_grid : list[dict]
        List of parameter dictionaries to test.
    """
    result = RobustnessResult()

    for params in param_grid:
        try:
            strat_returns = strategy_fn(returns, **params)
            prices = (1 + strat_returns).cumprod()
            sharpe = f.sharpe_ratio(strat_returns, risk_free_rate, trading_days)
            sortino = f.sortino_ratio(strat_returns, risk_free_rate, trading_days)
            mdd = f.max_drawdown(prices)
            ann_ret = f.annualized_return(strat_returns, trading_days)

            result.parameter_results.append({
                "params": params,
                "sharpe": sharpe,
                "sortino": sortino,
                "max_drawdown": mdd,
                "annualized_return": ann_ret,
            })
        except Exception as e:
            result.parameter_results.append({
                "params": params,
                "error": str(e),
            })

    return result


def cost_stress(
    base_returns: pd.Series | None = None,
    trade_count: int = 50,
    total_days: int | None = None,
    cost_levels: list[float] | None = None,
    risk_free_rate: float = 0.05,
    trading_days: int = 252,
    returns: pd.Series | None = None,
) -> list[dict]:
    """
    Test strategy viability under increasing transaction costs.

    Simulates the drag of transaction costs at various levels.
    """
    if base_returns is None:
        if returns is not None:
            base_returns = returns
        else:
            raise ValueError("base_returns or returns series must be provided.")

    if total_days is None:
        total_days = len(base_returns)

    if cost_levels is None:
        cost_levels = [0.0, 0.0005, 0.001, 0.002, 0.005, 0.01]

    results = []
    trades_per_day = trade_count / total_days if total_days > 0 else 0


    for cost in cost_levels:
        # Subtract daily cost drag: cost × trades_per_day × 2 (round-trip)
        daily_drag = cost * trades_per_day * 2
        adjusted_returns = base_returns - daily_drag
        prices = (1 + adjusted_returns).cumprod()

        results.append({
            "cost_bps": cost * 10000,
            "cost_pct": cost,
            "sharpe": f.sharpe_ratio(adjusted_returns, risk_free_rate, trading_days),
            "annualized_return": f.annualized_return(adjusted_returns, trading_days),
            "max_drawdown": f.max_drawdown(prices),
            "net_viable": f.sharpe_ratio(adjusted_returns, risk_free_rate, trading_days) > 0,
        })

    return results


def period_stress(
    returns: pd.Series,
    strategy_fn: Callable[[pd.Series], pd.Series],
    periods: list[tuple[str, str]] | None = None,
    risk_free_rate: float = 0.05,
    trading_days: int = 252,
) -> list[dict]:
    """
    Test strategy across different time periods.

    Parameters
    ----------
    returns : pd.Series
    strategy_fn : callable
    periods : list of (start, end) tuples
    """
    if periods is None:
        # Auto-split into halves
        n = len(returns)
        mid = n // 2
        periods_idx = [(0, mid), (mid, n)]
    else:
        periods_idx = None

    results = []

    if periods_idx:
        for i, (start, end) in enumerate(periods_idx):
            sub = returns.iloc[start:end]
            strat_ret = strategy_fn(sub)
            prices = (1 + strat_ret).cumprod()
            results.append({
                "period": f"half_{i+1}",
                "start": str(sub.index[0]) if hasattr(sub.index[0], 'strftime') else start,
                "end": str(sub.index[-1]) if hasattr(sub.index[-1], 'strftime') else end,
                "sharpe": f.sharpe_ratio(strat_ret, risk_free_rate, trading_days),
                "max_drawdown": f.max_drawdown(prices),
                "annualized_return": f.annualized_return(strat_ret, trading_days),
            })

    return results


def _parameter_stability(sharpes: list[float]) -> float:
    """How stable is Sharpe across parameter variations (0 to 1)."""
    if len(sharpes) < 2:
        return 1.0
    mean_s = np.mean(sharpes)
    if mean_s == 0:
        return 0.0
    cv = np.std(sharpes) / abs(mean_s)
    return float(max(0, 1 - cv))
