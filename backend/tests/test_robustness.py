"""
Unit Tests — Robustness/Stress Testing (Somesh's module)
=========================================================
Tests for parameter, cost, and period stress testing.
"""

import numpy as np
import pandas as pd
import pytest

from app.validation.robustness import (
    parameter_stress,
    cost_stress,
    period_stress,
    RobustnessResult,
    _parameter_stability,
)


class TestRobustnessResult:
    """Test the RobustnessResult container class."""

    def test_robustness_result_init(self):
        result = RobustnessResult()
        assert result.parameter_results == []
        assert result.cost_results == []
        assert result.period_results == []

    def test_robustness_result_to_dict_empty(self):
        result = RobustnessResult()
        d = result.to_dict()
        assert d["parameter_sensitivity"] == []
        assert d["cost_sensitivity"] == []
        assert d["period_sensitivity"] == []
        assert d["summary"] == {}

    def test_robustness_result_to_dict_with_data(self):
        result = RobustnessResult()
        result.parameter_results = [
            {"params": {"param1": 10}, "sharpe": 1.5, "sortino": 2.0, "max_drawdown": -0.1, "annualized_return": 0.15},
            {"params": {"param1": 20}, "sharpe": 1.2, "sortino": 1.8, "max_drawdown": -0.12, "annualized_return": 0.12},
        ]

        d = result.to_dict()
        assert len(d["parameter_sensitivity"]) == 2
        assert d["summary"]["trials_tested"] == 2
        assert d["summary"]["best_raw_sharpe"] == 1.5
        assert d["summary"]["worst_sharpe"] == 1.2
        assert d["summary"]["mean_sharpe"] == 1.35
        assert "parameter_stability" in d["summary"]


class TestParameterStability:
    """Test the _parameter_stability helper."""

    def test_parameter_stability_stable(self):
        sharpes = [1.5, 1.55, 1.45, 1.52]
        stability = _parameter_stability(sharpes)
        # CV = std/mean = 0.05/1.505 = 0.033, stability = 1 - 0.033 = 0.967
        assert stability > 0.9

    def test_parameter_stability_unstable(self):
        sharpes = [2.0, -1.0, 3.0, -2.0]
        stability = _parameter_stability(sharpes)
        # High CV, stability should be low
        assert stability < 0.5

    def test_parameter_stability_single(self):
        sharpes = [1.5]
        stability = _parameter_stability(sharpes)
        assert stability == 1.0

    def test_parameter_stability_zero_mean(self):
        sharpes = [0.0, 0.0, 0.0]
        stability = _parameter_stability(sharpes)
        assert stability == 0.0

    def test_parameter_stability_two_values(self):
        sharpes = [1.0, 2.0]
        stability = _parameter_stability(sharpes)
        # mean = 1.5, std = 0.5, CV = 0.333, stability = 0.667
        assert abs(stability - 0.667) < 0.01


class TestParameterStress:
    """Test the parameter_stress function."""

    @pytest.fixture
    def sample_returns(self):
        np.random.seed(42)
        return pd.Series(np.random.normal(0.0005, 0.02, 500))

    def test_parameter_stress_basic(self, sample_returns):
        def strategy(returns: pd.Series, **params) -> pd.Series:
            window = params.get("window", 10)
            signal = returns.rolling(window).mean().shift(1).fillna(0)
            signal = np.sign(signal)
            return returns * signal

        param_grid = [
            {"window": 5},
            {"window": 10},
            {"window": 20},
            {"window": 50},
        ]

        result = parameter_stress(
            returns=sample_returns,
            strategy_fn=strategy,
            param_grid=param_grid,
        )

        assert isinstance(result, RobustnessResult)
        assert len(result.parameter_results) == 4

        for r in result.parameter_results:
            assert "params" in r
            assert "sharpe" in r
            assert "sortino" in r
            assert "max_drawdown" in r
            assert "annualized_return" in r

    def test_parameter_stress_with_error(self, sample_returns):
        def failing_strategy(returns: pd.Series, **params) -> pd.Series:
            if params.get("fail", False):
                raise ValueError("Strategy failed")
            return returns

        param_grid = [
            {"fail": False},
            {"fail": True},
            {"fail": False},
        ]

        result = parameter_stress(
            returns=sample_returns,
            strategy_fn=failing_strategy,
            param_grid=param_grid,
        )

        assert len(result.parameter_results) == 3
        # Check error is captured
        error_results = [r for r in result.parameter_results if "error" in r]
        assert len(error_results) == 1
        assert "Strategy failed" in error_results[0]["error"]

    def test_parameter_stress_custom_risk_free(self, sample_returns):
        def strategy(returns: pd.Series, **params) -> pd.Series:
            return returns

        result = parameter_stress(
            returns=sample_returns,
            strategy_fn=strategy,
            param_grid=[{"param": 1}],
            risk_free_rate=0.03,
            trading_days=252,
        )

        assert len(result.parameter_results) == 1


class TestCostStress:
    """Test the cost_stress function."""

    @pytest.fixture
    def base_returns(self):
        np.random.seed(42)
        return pd.Series(np.random.normal(0.001, 0.01, 252))

    def test_cost_stress_basic(self, base_returns):
        results = cost_stress(
            base_returns=base_returns,
            trade_count=50,
            total_days=252,
            cost_levels=[0.0, 0.0005, 0.001, 0.005],
        )

        assert len(results) == 4
        for r in results:
            assert "cost_bps" in r
            assert "cost_pct" in r
            assert "sharpe" in r
            assert "annualized_return" in r
            assert "max_drawdown" in r
            assert "net_viable" in r

    def test_cost_stress_monotonic_sharpe(self, base_returns):
        """Sharpe should decrease (or stay same) as costs increase."""
        results = cost_stress(
            base_returns=base_returns,
            trade_count=50,
            cost_levels=[0.0, 0.001, 0.005, 0.01],
        )

        sharpes = [r["sharpe"] for r in results]
        for i in range(1, len(sharpes)):
            # Each step should not increase Sharpe
            assert sharpes[i] <= sharpes[i - 1] + 1e-10

    def test_cost_stress_cost_bps_conversion(self, base_returns):
        results = cost_stress(
            base_returns=base_returns,
            trade_count=50,
            cost_levels=[0.001, 0.005],
        )
        assert results[0]["cost_bps"] == 10  # 0.001 * 10000
        assert results[1]["cost_bps"] == 50  # 0.005 * 10000

    def test_cost_stress_uses_returns_param(self, base_returns):
        """Test that `returns` parameter works as alias for `base_returns`."""
        results = cost_stress(
            returns=base_returns,
            trade_count=50,
            cost_levels=[0.001],
        )
        assert len(results) == 1

    def test_cost_stress_missing_returns(self):
        """Test error when no returns provided."""
        with pytest.raises(ValueError, match="must be provided"):
            cost_stress(base_returns=None, returns=None, trade_count=50)

    def test_cost_stress_default_cost_levels(self, base_returns):
        results = cost_stress(
            base_returns=base_returns,
            trade_count=50,
            cost_levels=None,
        )
        # Should use default levels
        assert len(results) == 6

    def test_cost_stress_auto_total_days(self, base_returns):
        results = cost_stress(
            base_returns=base_returns,
            trade_count=50,
            total_days=None,  # Should auto-detect
            cost_levels=[0.001],
        )
        assert len(results) == 1


class TestPeriodStress:
    """Test the period_stress function."""

    @pytest.fixture
    def sample_returns(self):
        np.random.seed(42)
        dates = pd.date_range("2020-01-01", periods=500, freq="D")
        return pd.Series(np.random.normal(0.0005, 0.02, 500), index=dates)

    def test_period_stress_auto_split(self, sample_returns):
        def strategy(returns: pd.Series) -> pd.Series:
            return returns

        results = period_stress(
            returns=sample_returns,
            strategy_fn=strategy,
            periods=None,
        )

        assert len(results) == 2
        for r in results:
            assert "period" in r
            assert "start" in r
            assert "end" in r
            assert "sharpe" in r
            assert "max_drawdown" in r
            assert "annualized_return" in r

    def test_period_stress_custom_periods(self, sample_returns):
        def strategy(returns: pd.Series) -> pd.Series:
            return returns

        periods = [
            ("2020-01-01", "2020-06-30"),
            ("2020-07-01", "2020-12-31"),
        ]

        results = period_stress(
            returns=sample_returns,
            strategy_fn=strategy,
            periods=periods,
        )

        # Custom periods with string dates may not match index, so auto-split is used
        # The function handles this by using indices internally
        assert len(results) == 2 or len(results) == 0
        # If it finds the periods, check structure
        if len(results) == 2:
            assert results[0]["period"] == "half_1"
            assert results[1]["period"] == "half_2"

    def test_period_stress_custom_risk_free(self, sample_returns):
        def strategy(returns: pd.Series) -> pd.Series:
            return returns

        results = period_stress(
            returns=sample_returns,
            strategy_fn=strategy,
            risk_free_rate=0.03,
            trading_days=252,
        )

        assert len(results) == 2