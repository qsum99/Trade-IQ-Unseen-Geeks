"""
Unit Tests — Portfolio Engine
=============================
Tests portfolio analytics, optimization (Max Sharpe, Min Variance), and weight allocation.
"""

import numpy as np
import pandas as pd
import pytest

from app.portfolio.analytics import analyse_portfolio
from app.portfolio.optimization import optimize_portfolio
from app.portfolio.allocation import allocate_weights


@pytest.fixture
def multi_asset_returns():
    rng = np.random.default_rng(42)
    assets = ["AAPL", "MSFT", "GOOGL"]
    df = pd.DataFrame(
        rng.normal(0.0005, 0.012, (252, 3)),
        columns=assets,
    )
    return df


def test_analyse_portfolio(multi_asset_returns):
    weights = {"AAPL": 0.4, "MSFT": 0.4, "GOOGL": 0.2}
    result = analyse_portfolio(multi_asset_returns, weights=weights, risk_free_rate=0.05)
    assert result.volatility > 0
    assert result.effective_number_of_holdings > 1.0


def test_optimize_max_sharpe(multi_asset_returns):
    result = optimize_portfolio(
        multi_asset_returns,
        objective="max_sharpe",
        risk_free_rate=0.05,
    )
    total_w = sum(result.optimal_weights.values())
    assert pytest.approx(total_w, rel=1e-3) == 1.0
    assert result.expected_volatility > 0


def test_optimize_min_variance(multi_asset_returns):
    result = optimize_portfolio(
        multi_asset_returns,
        objective="min_variance",
        risk_free_rate=0.05,
    )
    total_w = sum(result.optimal_weights.values())
    assert pytest.approx(total_w, rel=1e-3) == 1.0


def test_allocate_weights(multi_asset_returns):
    # Equal weight
    ew = allocate_weights(multi_asset_returns, strategy="equal_weight")
    assert pytest.approx(ew["AAPL"], rel=1e-3) == 1.0 / 3.0

    # Inverse volatility
    iv = allocate_weights(multi_asset_returns, strategy="inverse_volatility")
    assert pytest.approx(sum(iv.values()), rel=1e-3) == 1.0
