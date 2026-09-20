"""
Tail-Risk Analysis Engine
==========================
Measures strategy behaviour during extreme market events.
Interpretable measures rather than arbitrary AI scores.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.quant import formulas as f
from app.core.schemas.risk import TailRiskResult


def compute_tail_risk(
    returns: pd.Series,
    benchmark_returns: pd.Series,
    tail_percentile: float = 0.05,
) -> TailRiskResult:
    """
    Analyse strategy behaviour during the worst benchmark periods.

    Provides:
      - Worst 5% / 1% benchmark days
      - Strategy return during those periods
      - Tail correlation
      - Downside beta
      - Maximum loss
      - CVaR

    Parameters
    ----------
    returns : pd.Series
        Strategy daily returns.
    benchmark_returns : pd.Series
        Benchmark daily returns.
    tail_percentile : float
        e.g. 0.05 for worst 5% of days.
    """
    # Align series
    aligned = pd.concat(
        [returns.rename("strategy"), benchmark_returns.rename("benchmark")],
        axis=1,
    ).dropna()

    strat = aligned["strategy"]
    bench = aligned["benchmark"]

    # Identify worst benchmark days
    threshold = np.percentile(bench, tail_percentile * 100)
    worst_mask = bench <= threshold

    # Benchmark's worst return in the tail
    benchmark_worst = float(bench[worst_mask].mean())

    # Strategy return during worst benchmark days
    strategy_during_worst = float(strat[worst_mask].mean())

    # Tail correlation (correlation only in the tail)
    if worst_mask.sum() > 2:
        tail_corr = float(strat[worst_mask].corr(bench[worst_mask]))
    else:
        tail_corr = 0.0

    # Downside beta (regression only on down-market days)
    down_market = bench < 0
    if down_market.sum() > 2:
        cov = np.cov(strat[down_market], bench[down_market])
        d_beta = float(cov[0, 1] / cov[1, 1]) if cov[1, 1] != 0 else 0.0
    else:
        d_beta = 0.0

    # Maximum single-day loss
    max_loss = float(strat.min())

    # CVaR
    cvar = f.conditional_var(strat, 1 - tail_percentile, method="historical")

    return TailRiskResult(
        symbol="",
        worst_days_pct=tail_percentile,
        benchmark_worst_return=benchmark_worst,
        strategy_return_during_worst=strategy_during_worst,
        tail_correlation=tail_corr,
        downside_beta=d_beta,
        maximum_loss=max_loss,
        cvar=cvar,
    )
