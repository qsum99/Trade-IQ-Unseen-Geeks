"""Exhaustive logic tests for quant formulas — correctness + edge cases."""
import math

import numpy as np
import pandas as pd

from app.quant import formulas as F


def test_return_math():
    prices = pd.Series([100.0, 110.0, 104.5, 125.4])
    simple = F.simple_return(prices)
    assert abs(simple.iloc[1] - 0.10) < 1e-9
    assert abs(simple.iloc[2] - (-0.05)) < 1e-9
    log = F.log_return(prices)
    assert abs(log.iloc[1] - math.log(1.10)) < 1e-9
    # cumulative: (1.1)(0.95)(1.2)-1 = 0.254
    assert abs(F.cumulative_return(pd.Series([0.10, -0.05, 0.20])) - 0.254) < 1e-9
    assert F.cumulative_return(pd.Series([], dtype=float)) == 0.0
    assert abs(F.cagr(100, 200, 1) - 1.0) < 1e-9
    assert F.cagr(0, 200, 1) == 0.0
    assert F.cagr(100, 200, 0) == 0.0
    assert F.annualized_return(pd.Series([], dtype=float)) == 0.0
    ann = F.annualized_return(pd.Series([0.01] * 252))
    assert ann > 0


def test_indicators_logic():
    s = pd.Series([1, 2, 3, 4, 5], dtype=float)
    assert F.sma(s, 3).iloc[-1] == 4.0
    assert pd.isna(F.sma(s, 3).iloc[0])
    e = F.ema(s, 3)
    assert e.iloc[-1] > e.iloc[0]  # uptrend
    m = F.momentum(pd.Series([100, 110, 121], dtype=float), 1)
    assert abs(m.iloc[2] - 0.10) < 1e-9
    z = F.z_score(pd.Series(range(30), dtype=float), 10)
    assert z.dropna().shape[0] > 0
    # constant series -> sigma 0 -> NaN, no crash
    zc = F.z_score(pd.Series([5.0] * 30), 10)
    assert zc.isna().all() or (zc == 0).all() or zc.dropna().empty
    pr = F.percentile_rank(pd.Series(range(300), dtype=float), 50)
    assert pr.dropna().between(0, 1).all()


def test_risk_logic():
    rets = pd.Series([0.01, 0.02, -0.01, 0.015, -0.005] * 20, dtype=float)
    vol = F.volatility(rets, 10)
    assert (vol.dropna() > 0).all()
    assert F.downside_deviation(rets) >= 0
    assert F.downside_deviation(pd.Series([0.01, 0.02, 0.03])) == 0.0 or F.downside_deviation(pd.Series([0.01, 0.02, 0.03])) >= 0
    sr = F.sharpe_ratio(rets)
    assert isinstance(sr, float)
    assert F.sharpe_ratio(pd.Series([0.01] * 30)) == 0.0  # zero variance
    assert F.sharpe_ratio(pd.Series([0.01])) == 0.0  # too short
    so = F.sortino_ratio(rets)
    assert isinstance(so, float)
    assert F.sortino_ratio(pd.Series([0.05] * 30)) == 0.0  # no downside
    # drawdown
    eq = pd.Series([100, 110, 105, 120, 90, 100], dtype=float)
    dd = F.max_drawdown(eq)
    assert dd["max_drawdown"] < 0
    assert dd["peak_date"] is not None
    assert len(dd["series"]) > 0
    assert F.max_drawdown(pd.Series([], dtype=float))["max_drawdown"] == 0.0
    # no-recovery case
    dd2 = F.max_drawdown(pd.Series([100, 90, 80, 70], dtype=float))
    assert dd2["recovery_date"] is None
    assert F.drawdown_duration(eq) == 0
    assert F.calmar_ratio(0.2, -0.1) == 2.0
    assert F.calmar_ratio(0.2, 0.0) == 0.0
    assert F.omega_ratio(pd.Series([0.01, 0.02])) == float("inf")
    assert F.omega_ratio(pd.Series([], dtype=float)) == 0.0
    assert F.omega_ratio(rets) > 0
    # VaR / CVaR all branches
    assert F.value_at_risk(pd.Series([], dtype=float)) == 0.0
    assert F.value_at_risk(rets, 0.95, "historical") >= 0
    assert F.value_at_risk(rets, 0.95, "parametric") >= 0
    assert F.conditional_var(pd.Series([], dtype=float)) == 0.0
    cvar = F.conditional_var(rets)
    assert cvar >= F.value_at_risk(rets) - 1e-9
    assert isinstance(F.conditional_var(pd.Series([0.05] * 50)), float)  # constant gains branch
    s_pos = pd.Series([0.2, 0.3, 0.25, 0.4] * 25)
    assert F.conditional_var(s_pos) < 0 and F.value_at_risk(s_pos) < 0  # all-gain tail sanity


def test_benchmark_logic():
    s = pd.Series([0.01, 0.02, -0.01, 0.03] * 25, dtype=float)
    m = pd.Series([0.008, 0.015, -0.005, 0.02] * 25, dtype=float)
    b = F.beta(s, m)
    assert b > 0  # positively correlated
    assert F.beta(s, s) == 1.0 or abs(F.beta(s, s) - 1.0) < 1e-9
    assert F.beta(pd.Series([0.01]), pd.Series([0.01])) == 0.0
    assert F.beta(s, pd.Series([0.01] * 100)) == 0.0  # zero variance market
    assert isinstance(F.alpha(0.15, 1.1, 0.10), float)
    assert F.treynor_ratio(0.12, 0.0) == 0.0
    assert F.treynor_ratio(0.12, 1.0) != 0.0
    te = F.tracking_error(s, m)
    assert te >= 0
    assert F.tracking_error(pd.Series([0.01]), pd.Series([0.01])) == 0.0
    ir = F.information_ratio(s, m)
    assert isinstance(ir, float)
    assert F.information_ratio(s, s) == 0.0  # zero TE
    assert F.upside_capture(s, m) > 0
    assert F.downside_capture(s, m) > 0
    # no up days / no down days / zero bench
    flat = pd.Series([0.0] * 100)
    assert F.upside_capture(s, flat) == 0.0
    assert F.downside_capture(s, flat) == 0.0
    assert F.upside_capture(flat, flat) == 0.0


def test_portfolio_logic():
    w = np.array([0.5, 0.5])
    er = np.array([0.10, 0.20])
    cov = np.array([[0.04, 0.01], [0.01, 0.09]])
    assert abs(F.portfolio_return(w, er) - 0.15) < 1e-9
    assert F.portfolio_variance(w, cov) > 0
    assert abs(F.portfolio_volatility(w, cov) - math.sqrt(F.portfolio_variance(w, cov))) < 1e-9
    assert isinstance(F.portfolio_sharpe(w, er, cov), float)
    assert F.portfolio_sharpe(np.array([1.0]), np.array([0.05]), np.array([[0.0]])) == 0.0
    ew = F.equal_weight(4)
    assert abs(ew.sum() - 1.0) < 1e-9
    iv = F.inverse_volatility_weight(np.array([0.2, 0.4]))
    assert abs(iv.sum() - 1.0) < 1e-9
    assert iv[0] > iv[1]  # lower vol gets higher weight


def test_trading_logic():
    assert F.turnover(pd.Series([100, 200]), 1000) == 0.3
    assert F.turnover(pd.Series([100]), 0) == 0.0
    assert abs(F.expectancy(0.6, 100, 0.4, 50) - 40) < 1e-9
    assert F.profit_factor(200, 100) == 2.0
    assert F.profit_factor(200, 0) == float("inf")
    assert F.profit_factor(0, 0) == 0.0
    assert F.win_rate(6, 10) == 0.6
    assert F.win_rate(0, 0) == 0.0
    assert F.risk_reward(100, -50) == 2.0
    assert F.risk_reward(100, 0) == 0.0
    assert F.max_consecutive_losses([True, False, False, True, False, False, False]) == 3
    assert F.max_consecutive_losses([True, True]) == 0
    assert F.max_consecutive_losses([]) == 0
    assert F.position_size(100000, 0.01, 10) == 100
    assert F.position_size(100000, 0.01, 0) == 0.0
    lo, hi = F.mae_mfe(100, pd.Series([90, 110, 105], dtype=float))
    assert lo < 0 < hi


def test_regime_relationship_logic():
    a = pd.Series(np.arange(50, dtype=float))
    b = pd.Series(np.arange(50, dtype=float) * 2)
    rc = F.rolling_correlation(a, b, 10).dropna()
    assert (rc > 0.99).all()
    assert abs(F.regime_score(1, 1, 1, 0) - 0.85) < 1e-9
    stats_df = F.rolling_statistics(pd.Series(np.arange(60, dtype=float) + 100), 10)
    assert set(stats_df.columns) == {"sma", "vol", "momentum"}
    assert len(stats_df) == 60
