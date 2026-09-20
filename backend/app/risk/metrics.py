"""
Advanced Risk Metrics Service
=============================
Computes comprehensive risk analytics for any return series.
All formulas come from app.quant.formulas.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.quant import formulas as f
from app.core.schemas.risk import RiskMetricsResult


def compute_risk_metrics(
    returns: pd.Series,
    benchmark_returns: pd.Series | None = None,
    risk_free_rate: float = 0.05,
    trading_days: int = 252,
    confidence_levels: list[float] | None = None,
) -> RiskMetricsResult:
    """
    Compute the full suite of risk metrics for a return series.

    Parameters
    ----------
    returns : pd.Series
        Daily simple returns.
    benchmark_returns : pd.Series | None
        Benchmark daily returns for relative metrics.
    risk_free_rate : float
        Annual risk-free rate.
    trading_days : int
        Trading days per year.
    confidence_levels : list[float]
        Confidence levels for VaR/CVaR.

    Returns
    -------
    RiskMetricsResult
    """
    if confidence_levels is None:
        confidence_levels = [0.95, 0.99]

    prices = (1 + returns).cumprod()

    # Get annualized volatility (scalar)
    vol_series = f.volatility(returns, window=min(len(returns)-1, 60), trading_days=trading_days)
    vol = float(vol_series.dropna().iloc[-1]) if len(vol_series.dropna()) > 0 else 0.0
    
    # Downside deviation (scalar)
    dd = f.downside_deviation(returns, target=0.0, trading_days=trading_days)

    result = dict(
        symbol="",
        volatility=float(returns.std()),
        annualized_volatility=vol,
        sharpe_ratio=f.sharpe_ratio(returns, risk_free_rate=risk_free_rate, trading_days=trading_days),
        sortino_ratio=f.sortino_ratio(returns, risk_free_rate=risk_free_rate, trading_days=trading_days),
        calmar_ratio=f.calmar_ratio(returns, prices, trading_days),
        omega_ratio=f.omega_ratio(returns),
        max_drawdown=f.max_drawdown(prices)["max_drawdown"],
        max_drawdown_duration_days=f.drawdown_duration(prices),
        downside_deviation=dd,
        var_95=f.value_at_risk(returns, 0.95),
var_99=f.value_at_risk(returns, 0.99),
        cvar_95=f.conditional_var(returns, 0.95, method="historical"),
        cvar_99=f.conditional_var(returns, 0.99, method="historical"),
    )

    # Benchmark-relative metrics
    if benchmark_returns is not None:
        aligned = pd.concat(
            [returns.rename("r"), benchmark_returns.rename("b")], axis=1
        ).dropna()
        r, b = aligned["r"], aligned["b"]

        result.update(
            beta=f.beta(r, b),
            alpha=f.alpha(r, b, market_or_rf=risk_free_rate, trading_days=trading_days),
            treynor_ratio=f.treynor_ratio(r, b, risk_free=risk_free_rate, trading_days=trading_days),
            information_ratio=f.information_ratio(r, b, annualization=trading_days),
            tracking_error=f.tracking_error(r, b, annualization=trading_days),
        )

    return RiskMetricsResult(**result)
