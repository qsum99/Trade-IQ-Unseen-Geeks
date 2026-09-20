"""
Monte Carlo Risk Simulation Engine
====================================
Generates thousands of possible portfolio paths for risk analysis.
Uses historical return distribution for sampling.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.quant import formulas as f
from app.core.schemas.risk import MonteCarloResult


def run_monte_carlo(
    returns: pd.Series,
    num_simulations: int = 10_000,
    num_days: int = 252,
    initial_value: float = 100_000.0,
    confidence_level: float = 0.95,
    num_sample_paths: int = 10,
) -> MonteCarloResult:
    """
    Run Monte Carlo simulation based on historical return distribution.

    Architecture:
      Historical Returns → Estimate parameters → Generate paths
        → Thousands of simulations → Distribution → Risk metrics

    Parameters
    ----------
    returns : pd.Series
        Daily return series.
    num_simulations : int
        Number of simulation paths.
    num_days : int
        Forecast horizon in trading days.
    initial_value : float
        Starting portfolio value.
    confidence_level : float
        For VaR/CVaR calculation.
    num_sample_paths : int
        Number of paths to return for visualisation.
    """
    mu = returns.mean()
    sigma = returns.std()

    # Generate random return paths
    rng = np.random.default_rng(seed=42)
    random_returns = rng.normal(mu, sigma, size=(num_simulations, num_days))

    # Build price paths: cumulative product of (1 + return)
    price_paths = initial_value * np.cumprod(1 + random_returns, axis=1)

    # Final values
    final_values = price_paths[:, -1]

    # Drawdowns per path
    max_drawdowns = np.zeros(num_simulations)
    for i in range(num_simulations):
        path = price_paths[i]
        running_max = np.maximum.accumulate(path)
        dd = (path - running_max) / running_max
        max_drawdowns[i] = dd.min()

    # Portfolio returns
    portfolio_returns = final_values / initial_value - 1

    # VaR and CVaR on final values
    loss_threshold = np.percentile(final_values, (1 - confidence_level) * 100)
    var_loss = initial_value - loss_threshold
    tail = final_values[final_values <= loss_threshold]
    cvar_loss = initial_value - tail.mean() if len(tail) > 0 else var_loss

    # Sample paths for visualisation
    sample_indices = rng.choice(num_simulations, size=min(num_sample_paths, num_simulations), replace=False)
    sample_paths = [price_paths[i].tolist() for i in sample_indices]

    return MonteCarloResult(
        symbol="",
        num_simulations=num_simulations,
        num_days=num_days,
        initial_value=initial_value,
        mean_final_value=float(np.mean(final_values)),
        median_final_value=float(np.median(final_values)),
        std_final_value=float(np.std(final_values)),
        var=float(var_loss),
        cvar=float(cvar_loss),
        probability_of_loss=float(np.mean(final_values < initial_value)),
        percentile_5=float(np.percentile(final_values, 5)),
        percentile_25=float(np.percentile(final_values, 25)),
        percentile_75=float(np.percentile(final_values, 75)),
        percentile_95=float(np.percentile(final_values, 95)),
        max_drawdown_mean=float(np.mean(max_drawdowns)),
        max_drawdown_95=float(np.percentile(max_drawdowns, 5)),  # worst 5% DD
        sample_paths=sample_paths,
    )
