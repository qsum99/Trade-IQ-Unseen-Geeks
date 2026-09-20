"""
Unit Tests — Risk Engine
========================
Tests risk metrics, VaR/CVaR, Monte Carlo, and tail-risk analysis.
"""

import numpy as np
import pandas as pd
import pytest

from app.risk.metrics import compute_risk_metrics
from app.risk.var import compute_var
from app.risk.monte_carlo import run_monte_carlo
from app.risk.tail import compute_tail_risk


@pytest.fixture
def return_series():
    rng = np.random.default_rng(42)
    return pd.Series(rng.normal(0.0005, 0.012, 500))


@pytest.fixture
def benchmark_series():
    rng = np.random.default_rng(123)
    return pd.Series(rng.normal(0.0003, 0.010, 500))


def test_compute_risk_metrics(return_series, benchmark_series):
    result = compute_risk_metrics(
        returns=return_series,
        benchmark_returns=benchmark_series,
        risk_free_rate=0.05,
    )
    assert result.annualized_volatility > 0
    assert result.var_95 is not None
    assert result.cvar_95 is not None
    assert result.max_drawdown <= 0


def test_compute_var(return_series):
    var_res = compute_var(return_series, confidence_level=0.95)
    assert var_res.confidence_level == 0.95
    assert isinstance(var_res.var, float)
    assert isinstance(var_res.cvar, float)


def test_monte_carlo_simulation(return_series):
    mc_res = run_monte_carlo(
        returns=return_series,
        initial_value=100.0,
        num_days=30,
        num_simulations=100,
    )
    assert mc_res.num_simulations == 100
    assert mc_res.num_days == 30
    assert mc_res.percentile_5 <= mc_res.percentile_95



def test_tail_risk(return_series, benchmark_series):
    tail_res = compute_tail_risk(
        returns=return_series,
        benchmark_returns=benchmark_series,
    )
    assert tail_res.worst_days_pct == 0.05
    assert tail_res.maximum_loss <= 0
    assert tail_res.cvar <= 0
