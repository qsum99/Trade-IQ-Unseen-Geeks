"""
Unit Tests — Quantitative Formulas
===================================
Tests all core mathematical functions in app/quant/formulas.py.
"""

import numpy as np
import pandas as pd
import pytest

from app.quant import formulas as f


@pytest.fixture
def sample_prices():
    return pd.Series([100.0, 102.0, 101.0, 105.0, 107.0, 106.0, 110.0])


@pytest.fixture
def sample_returns():
    return pd.Series([0.02, -0.01, 0.04, 0.02, -0.01, 0.038])


def test_simple_returns(sample_prices):
    ret = f.simple_return(sample_prices)
    assert len(ret) == len(sample_prices) - 1
    assert pytest.approx(ret.iloc[0], rel=1e-3) == 0.02


def test_cagr(sample_prices):
    cagr_val = f.cagr(sample_prices, trading_days=252)
    assert isinstance(cagr_val, float)
    assert cagr_val > 0


def test_volatility(sample_returns):
    vol = f.volatility(sample_returns, trading_days=252)
    assert vol > 0


def test_sharpe_ratio(sample_returns):
    sr = f.sharpe_ratio(sample_returns, risk_free_rate=0.0, trading_days=252)
    assert isinstance(sr, float)


def test_sortino_ratio(sample_returns):
    sortino = f.sortino_ratio(sample_returns, risk_free_rate=0.0, trading_days=252)
    assert isinstance(sortino, float)


def test_max_drawdown(sample_prices):
    mdd = f.max_drawdown(sample_prices)
    assert -1.0 <= mdd <= 0.0


def test_var_historical(sample_returns):
    var_95 = f.value_at_risk(sample_returns, confidence=0.95, method="historical")
    assert isinstance(var_95, float)


def test_cvar(sample_returns):
    cvar_95 = f.conditional_var(sample_returns, confidence=0.95, method="historical")
    var_95 = f.value_at_risk(sample_returns, confidence=0.95, method="historical")
    # CVaR is expected loss beyond VaR, so in magnitude CVaR <= VaR (more negative)
    assert cvar_95 <= var_95 or pytest.approx(cvar_95, rel=1e-2) == var_95


def test_portfolio_math():
    weights = np.array([0.5, 0.5])
    returns = np.array([0.10, 0.12])
    cov_matrix = np.array([[0.04, 0.01], [0.01, 0.05]])

    p_ret = f.portfolio_return(weights, returns)
    assert pytest.approx(p_ret, rel=1e-3) == 0.11

    p_var = f.portfolio_variance(weights, cov_matrix)
    assert p_var > 0

    p_vol = f.portfolio_volatility(weights, cov_matrix)
    assert pytest.approx(p_vol, rel=1e-3) == np.sqrt(p_var)
