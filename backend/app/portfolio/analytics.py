"""
Portfolio Analytics Engine
===========================
Computes portfolio-level performance, risk, and structural metrics.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.quant import formulas as f
from app.core.schemas.portfolio import PortfolioAnalyticsResult


def analyse_portfolio(
    returns_df: pd.DataFrame,
    weights: np.ndarray,
    risk_free_rate: float = 0.05,
    trading_days: int = 252,
) -> PortfolioAnalyticsResult:
    """
    Full portfolio analytics given a DataFrame of asset returns and weights.

    Parameters
    ----------
    returns_df : pd.DataFrame
        Columns are asset symbols, rows are daily returns.
    weights : np.ndarray
        Portfolio weights (same order as columns).
    risk_free_rate : float
    trading_days : int
    """
    # Annualised expected returns per asset
    expected_returns = returns_df.mean() * trading_days
    cov = f.covariance_matrix(returns_df, trading_days)
    corr = f.correlation_matrix(returns_df)

    # Ensure weights is a numpy array in column order
    if isinstance(weights, dict):
        w_arr = np.array([weights.get(col, 0.0) for col in returns_df.columns], dtype=float)
    else:
        w_arr = np.asarray(weights, dtype=float)

    # Portfolio aggregates
    port_ret = f.portfolio_return(w_arr, expected_returns.values)
    port_vol = f.portfolio_volatility(w_arr, cov)
    port_sharpe = f.portfolio_sharpe(w_arr, expected_returns.values, cov, risk_free_rate)


    # Individual metrics
    individual_returns = {
        col: float(expected_returns[col]) for col in returns_df.columns
    }
    individual_vols = {
        col: float(returns_df[col].std() * np.sqrt(trading_days))
        for col in returns_df.columns
    }

    # Concentration (HHI)
    hhi = float(np.sum(w_arr ** 2))

    # Effective number of holdings
    eff_n = float(1.0 / hhi) if hhi > 0 else 0.0

    return PortfolioAnalyticsResult(
        portfolio_return=port_ret,
        portfolio_volatility=port_vol,
        portfolio_sharpe=port_sharpe,
        correlation_matrix=corr.tolist(),
        covariance_matrix=cov.tolist(),
        individual_returns=individual_returns,
        individual_volatilities=individual_vols,
        concentration=hhi,
        effective_n=eff_n,
        turnover=None,
    )
