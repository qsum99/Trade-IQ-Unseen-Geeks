"""
Unit Tests — Additional Quant Formulas Coverage
================================================
Tests to cover uncovered lines in app/quant/formulas.py.
"""

import numpy as np
import pandas as pd
import pytest

from app.quant import formulas as f


class TestReturns:
    """Tests for return calculations."""

    def test_log_return(self):
        prices = pd.Series([100.0, 102.0, 101.0, 105.0])
        ret = f.log_return(prices)
        assert len(ret) == 3
        assert pytest.approx(ret.iloc[0], rel=1e-3) == np.log(102/100)

    def test_cumulative_return(self):
        returns = pd.Series([0.02, -0.01, 0.04])
        cum = f.cumulative_return(returns)
        assert len(cum) == 3
        assert pytest.approx(cum.iloc[-1], rel=1e-3) == (1.02 * 0.99 * 1.04 - 1)

    def test_total_return(self):
        prices = pd.Series([100.0, 110.0, 121.0])
        total = f.total_return(prices)
        assert pytest.approx(total, rel=1e-3) == 0.21

    def test_cagr(self):
        prices = pd.Series([100.0] + [100.0 * 1.1 ** (i/252) for i in range(252)])
        cagr_val = f.cagr(prices, trading_days=252)
        assert pytest.approx(cagr_val, rel=0.05) == 0.10

    def test_cagr_edge_cases(self):
        # Single price
        prices = pd.Series([100.0])
        assert f.cagr(prices) == 0.0

        # Two prices
        prices = pd.Series([100.0, 110.0])
        cagr_val = f.cagr(prices, trading_days=1)
        assert cagr_val > 0


class TestIndicators:
    """Tests for technical indicators."""

    def test_sma(self):
        prices = pd.Series(range(1, 11))
        sma = f.sma(prices, period=3)
        assert sma.iloc[2] == 2.0  # (1+2+3)/3
        assert sma.iloc[9] == 9.0  # (8+9+10)/3

    def test_ema(self):
        prices = pd.Series([10.0] * 10)
        ema = f.ema(prices, period=3)
        assert all(ema == 10.0)

    def test_momentum(self):
        prices = pd.Series([100.0, 102.0, 104.0, 108.0])
        mom = f.momentum(prices, period=2)
        assert pytest.approx(mom.iloc[2], rel=1e-3) == 104/100 - 1  # 0.04

    def test_z_score(self):
        series = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        z = f.z_score(series, window=3)
        # At index 2: mean of [1,2,3] = 2, std = 1, z = (3-2)/1 = 1
        assert pytest.approx(z.iloc[2], rel=1e-3) == 1.0

    def test_percentile_rank(self):
        series = pd.Series([1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
        pr = f.percentile_rank(series, window=5)
        # At index 4: values [1,2,3,4,5], 5 is at 100th percentile
        assert pytest.approx(pr.iloc[4], rel=1e-2) == 1.0


class TestRiskPerformance:
    """Tests for risk/performance metrics."""

    def test_downside_deviation(self):
        returns = pd.Series([0.02, -0.01, 0.03, -0.02, 0.01])
        dd = f.downside_deviation(returns, mar=0.0, trading_days=252)
        assert dd > 0

    def test_downside_deviation_no_negative(self):
        returns = pd.Series([0.01, 0.02, 0.03])
        dd = f.downside_deviation(returns, mar=0.0)
        assert dd == 0.0

    def test_calmar_ratio(self):
        returns = pd.Series([0.001] * 252)
        prices = (1 + returns).cumprod()
        calmar = f.calmar_ratio(returns, prices)
        assert isinstance(calmar, float)

    def test_calmar_ratio_zero_mdd(self):
        returns = pd.Series([0.001] * 100)
        calmar = f.calmar_ratio(returns)
        assert calmar == 0.0

    def test_omega_ratio(self):
        returns = pd.Series([0.02, -0.01, 0.03, -0.02, 0.01])
        omega = f.omega_ratio(returns, threshold=0.0)
        assert isinstance(omega, float)

    def test_omega_ratio_all_above(self):
        returns = pd.Series([0.01, 0.02, 0.03])
        omega = f.omega_ratio(returns, threshold=0.0)
        assert omega == float("inf")

    def test_drawdown_series(self):
        prices = pd.Series([100, 110, 105, 115, 110])
        dd = f.drawdown_series(prices)
        assert len(dd) == 5
        assert dd.iloc[0] == 0.0  # First value
        assert dd.iloc[2] < 0  # Drawdown at 105 from peak 110

    def test_drawdown_duration(self):
        prices = pd.Series([100, 110, 105, 100, 95, 100, 110])
        dur = f.drawdown_duration(prices)
        # Longest drawdown: 110 -> 95 = 4 days
        assert dur == 4

    def test_drawdown_duration_no_drawdown(self):
        prices = pd.Series([100, 110, 120, 130])
        dur = f.drawdown_duration(prices)
        assert dur == 0

    def test_var_parametric(self):
        returns = pd.Series(np.random.normal(0.001, 0.02, 1000))
        var = f.value_at_risk(returns, confidence=0.95, method="parametric")
        assert isinstance(var, float)
        assert var < 0  # Loss

    def test_var_cornish_fisher(self):
        returns = pd.Series(np.random.normal(0.001, 0.02, 1000))
        var = f.value_at_risk(returns, confidence=0.95, method="cornish_fisher")
        assert isinstance(var, float)

    def test_var_invalid_method(self):
        returns = pd.Series([0.01, -0.01, 0.02])
        # Invalid method falls back to historical
        var = f.value_at_risk(returns, method="invalid")
        assert isinstance(var, float)

    def test_conditional_var(self):
        returns = pd.Series(np.random.normal(0.001, 0.02, 1000))
        cvar = f.conditional_var(returns, confidence=0.95)
        var = f.value_at_risk(returns, confidence=0.95)
        assert cvar <= var  # CVaR is more negative (worse)


class TestBenchmarkAnalytics:
    """Tests for benchmark-relative metrics."""

    def test_beta(self):
        returns = pd.Series([0.02, -0.01, 0.03, -0.02, 0.01] * 20)
        benchmark = pd.Series([0.01, -0.005, 0.015, -0.01, 0.005] * 20)
        beta = f.beta(returns, benchmark)
        assert isinstance(beta, float)

    def test_beta_short_series(self):
        returns = pd.Series([0.01])
        benchmark = pd.Series([0.01])
        beta = f.beta(returns, benchmark)
        assert beta == 0.0

    def test_beta_zero_benchmark_var(self):
        returns = pd.Series([0.01, -0.01, 0.02])
        benchmark = pd.Series([0.0, 0.0, 0.0])
        beta = f.beta(returns, benchmark)
        assert beta == 0.0

    def test_alpha(self):
        returns = pd.Series([0.001] * 252)
        benchmark = pd.Series([0.0005] * 252)
        alpha = f.alpha(returns, benchmark)
        assert isinstance(alpha, float)

    def test_treynor_ratio(self):
        returns = pd.Series([0.001] * 252)
        benchmark = pd.Series([0.0005] * 252)
        treynor = f.treynor_ratio(returns, benchmark)
        assert isinstance(treynor, float)

    def test_treynor_ratio_zero_beta(self):
        returns = pd.Series([0.001] * 252)
        benchmark = pd.Series([0.0] * 252)
        treynor = f.treynor_ratio(returns, benchmark)
        assert treynor == 0.0

    def test_tracking_error(self):
        returns = pd.Series([0.001] * 252)
        benchmark = pd.Series([0.0005] * 252)
        te = f.tracking_error(returns, benchmark)
        assert isinstance(te, float)

    def test_information_ratio(self):
        returns = pd.Series([0.001] * 252)
        benchmark = pd.Series([0.0005] * 252)
        ir = f.information_ratio(returns, benchmark)
        assert isinstance(ir, float)

    def test_information_ratio_zero_te(self):
        returns = pd.Series([0.001] * 252)
        benchmark = pd.Series([0.001] * 252)
        ir = f.information_ratio(returns, benchmark)
        assert ir == 0.0

    def test_upside_capture(self):
        returns = pd.Series([0.02, -0.01, 0.03, -0.02])
        benchmark = pd.Series([0.01, -0.005, 0.015, -0.01])
        uc = f.upside_capture(returns, benchmark)
        assert isinstance(uc, float)

    def test_upside_capture_no_up_days(self):
        returns = pd.Series([-0.01, -0.02])
        benchmark = pd.Series([-0.01, -0.02])
        uc = f.upside_capture(returns, benchmark)
        assert uc == 0.0

    def test_downside_capture(self):
        returns = pd.Series([0.02, -0.01, 0.03, -0.02])
        benchmark = pd.Series([0.01, -0.005, 0.015, -0.01])
        dc = f.downside_capture(returns, benchmark)
        assert isinstance(dc, float)

    def test_downside_capture_no_down_days(self):
        returns = pd.Series([0.01, 0.02])
        benchmark = pd.Series([0.01, 0.02])
        dc = f.downside_capture(returns, benchmark)
        assert dc == 0.0


class TestPortfolioMath:
    """Tests for portfolio mathematics."""

    def test_equal_weight(self):
        weights = f.equal_weight(5)
        assert np.allclose(weights, 0.2)

    def test_inverse_volatility_weight(self):
        vols = np.array([0.1, 0.2, 0.3])
        weights = f.inverse_volatility_weight(vols)
        # Inverse: [10, 5, 3.33], normalized
        assert abs(weights.sum() - 1.0) < 1e-10
        assert weights[0] > weights[1] > weights[2]


class TestTradingAnalytics:
    """Tests for trading analytics."""

    def test_turnover(self):
        old = np.array([0.3, 0.3, 0.4])
        new = np.array([0.4, 0.2, 0.4])
        # |0.4-0.3| + |0.2-0.3| + |0.4-0.4| = 0.2, /2 = 0.1
        turn = f.turnover(old, new)
        assert pytest.approx(turn, rel=1e-3) == 0.1

    def test_expectancy(self):
        wins = pd.Series([0.05, 0.03, 0.04])
        losses = pd.Series([-0.02, -0.01])
        exp = f.expectancy(wins, losses)
        # p_win = 3/5 = 0.6, avg_win = 0.04
        # p_loss = 2/5 = 0.4, avg_loss = 0.015
        # exp = 0.6*0.04 - 0.4*0.015 = 0.024 - 0.006 = 0.018
        assert pytest.approx(exp, rel=1e-3) == 0.018

    def test_expectancy_empty(self):
        exp = f.expectancy(pd.Series([]), pd.Series([]))
        assert exp == 0.0

    def test_profit_factor(self):
        wins = pd.Series([0.05, 0.03])
        losses = pd.Series([-0.02, -0.01])
        pf = f.profit_factor(wins, losses)
        # 0.08 / 0.03 = 2.666...
        assert pytest.approx(pf, rel=1e-3) == 2.666

    def test_profit_factor_zero_loss(self):
        wins = pd.Series([0.05])
        losses = pd.Series([])
        pf = f.profit_factor(wins, losses)
        assert pf == float("inf")

    def test_win_rate(self):
        assert f.win_rate(3, 5) == 0.6
        assert f.win_rate(0, 0) == 0.0

    def test_risk_reward(self):
        assert f.risk_reward(0.05, -0.02) == 2.5
        assert f.risk_reward(0.05, 0.0) == float("inf")

    def test_max_consecutive_losses(self):
        pnl = pd.Series([0.01, -0.02, -0.01, 0.03, -0.02, -0.01, -0.01])
        mcl = f.max_consecutive_losses(pnl)
        assert mcl == 3

    def test_max_consecutive_losses_none(self):
        pnl = pd.Series([0.01, 0.02, 0.03])
        mcl = f.max_consecutive_losses(pnl)
        assert mcl == 0

    def test_position_size(self):
        size = f.position_size(10000, 0.02, 100, 95)
        # risk_amount = 200, per_share_risk = 5, size = 40
        assert size == 40.0

    def test_position_size_zero_risk(self):
        size = f.position_size(10000, 0.02, 100, 100)
        assert size == 0.0


class TestRegimeStatistics:
    """Tests for regime/statistics functions."""

    def test_regime_score(self):
        returns = pd.Series([0.01, -0.01, 0.02])
        vol = pd.Series([0.02, 0.015, 0.025])
        momentum = pd.Series([0.05, -0.02, 0.08])

        df = f.regime_score(returns, vol, momentum)
        assert isinstance(df, pd.DataFrame)
        assert list(df.columns) == ["returns", "volatility", "momentum"]
        assert len(df) == 3

    def test_rolling_statistics(self):
        series = pd.Series(np.random.randn(100))
        stats = f.rolling_statistics(series, window=20)
        assert isinstance(stats, pd.DataFrame)
        assert list(stats.columns) == ["mean", "std", "skew", "kurtosis"]
        # rolling(window).mean() drops first window-1 NaN values, so 100 - 19 = 81
        assert len(stats) == 81

    def test_covariance_matrix(self):
        returns_df = pd.DataFrame({
            "A": np.random.normal(0.001, 0.02, 100),
            "B": np.random.normal(0.001, 0.015, 100),
        })
        cov = f.covariance_matrix(returns_df)
        assert cov.shape == (2, 2)
        assert np.allclose(cov, cov.T)  # Symmetric

    def test_correlation_matrix(self):
        returns_df = pd.DataFrame({
            "A": np.random.normal(0.001, 0.02, 100),
            "B": np.random.normal(0.001, 0.015, 100),
        })
        corr = f.correlation_matrix(returns_df)
        assert corr.shape == (2, 2)
        assert corr[0, 0] == 1.0
        assert corr[1, 1] == 1.0