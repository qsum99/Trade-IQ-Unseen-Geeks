"""
Portfolio Optimization Engine
==============================
Classical optimisation methods using SciPy.
Supports: Equal Weight, Inverse Volatility, Min Variance,
          Max Sharpe, Risk Parity.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import minimize

from app.quant import formulas as f
from app.core.schemas.portfolio import PortfolioResult


def optimize_portfolio(
    returns_df: pd.DataFrame,
    method: str = "max_sharpe",
    risk_free_rate: float = 0.05,
    trading_days: int = 252,
    min_weight: float = 0.0,
    max_weight: float = 1.0,
    target_return: float | None = None,
    target_volatility: float | None = None,
    objective: str | None = None,
) -> PortfolioResult:
    """
    Optimise portfolio weights.

    Methods / Objectives
    --------------------
    - equal_weight
    - inverse_vol / inverse_volatility
    - min_variance
    - max_sharpe
    - risk_parity
    """
    if objective is not None:
        method = objective
    if method == "inverse_volatility":
        method = "inverse_vol"

    n = len(returns_df.columns)
    expected_returns = (returns_df.mean() * trading_days).values
    cov = f.covariance_matrix(returns_df, trading_days)

    if method == "equal_weight":
        weights = f.equal_weight(n)

    elif method == "inverse_vol":
        vols = np.array([
            returns_df[col].std() * np.sqrt(trading_days)
            for col in returns_df.columns
        ])
        weights = f.inverse_volatility_weight(vols)

    elif method == "min_variance":
        weights = _scipy_optimize(
            n, expected_returns, cov,
            objective="min_variance",
            risk_free_rate=risk_free_rate,
            min_w=min_weight, max_w=max_weight,
        )

    elif method == "max_sharpe":
        weights = _scipy_optimize(
            n, expected_returns, cov,
            objective="max_sharpe",
            risk_free_rate=risk_free_rate,
            min_w=min_weight, max_w=max_weight,
        )

    elif method == "risk_parity":
        weights = _risk_parity(n, cov, min_weight, max_weight)

    else:
        raise ValueError(f"Unknown method: {method}")

    # Compute resulting portfolio stats
    port_ret = f.portfolio_return(weights, expected_returns)
    port_vol = f.portfolio_volatility(weights, cov)
    port_sharpe = f.portfolio_sharpe(weights, expected_returns, cov, risk_free_rate)
    corr = f.correlation_matrix(returns_df)

    return PortfolioResult(
        symbols=list(returns_df.columns),
        weights=weights.tolist(),
        expected_return=port_ret,
        volatility=port_vol,
        sharpe_ratio=port_sharpe,
        correlation_matrix=corr.tolist(),
        covariance_matrix=cov.tolist(),
        effective_n=float(1.0 / np.sum(weights ** 2)),
        concentration=float(np.sum(weights ** 2)),
    )


# ── Internal helpers ────────────────────────────────────────────────────

def _scipy_optimize(
    n: int,
    expected_returns: np.ndarray,
    cov: np.ndarray,
    objective: str,
    risk_free_rate: float,
    min_w: float,
    max_w: float,
) -> np.ndarray:
    """Optimise with SciPy SLSQP."""
    x0 = np.ones(n) / n
    bounds = [(min_w, max_w)] * n
    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]

    if objective == "min_variance":
        fun = lambda w: f.portfolio_variance(w, cov)
    elif objective == "max_sharpe":
        fun = lambda w: -f.portfolio_sharpe(w, expected_returns, cov, risk_free_rate)
    else:
        raise ValueError(objective)

    result = minimize(
        fun, x0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"maxiter": 1000, "ftol": 1e-12},
    )
    return result.x


def _risk_parity(
    n: int,
    cov: np.ndarray,
    min_w: float,
    max_w: float,
) -> np.ndarray:
    """
    Risk-parity: each asset contributes equally to portfolio risk.
    Minimises Σ(RC_i − target)^2 where RC_i = w_i (Σw)_i / σ_p.
    """
    x0 = np.ones(n) / n
    bounds = [(min_w, max_w)] * n
    constraints = [{"type": "eq", "fun": lambda w: np.sum(w) - 1.0}]

    def risk_contribution_error(w: np.ndarray) -> float:
        port_vol = np.sqrt(w @ cov @ w)
        if port_vol == 0:
            return 0.0
        marginal = cov @ w
        rc = w * marginal / port_vol
        target = port_vol / n
        return float(np.sum((rc - target) ** 2))

    result = minimize(
        risk_contribution_error, x0,
        method="SLSQP",
        bounds=bounds,
        constraints=constraints,
        options={"maxiter": 1000},
    )
    return result.x
