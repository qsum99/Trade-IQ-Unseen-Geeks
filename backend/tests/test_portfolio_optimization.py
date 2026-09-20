"""
Unit Tests — Portfolio Optimization (Somesh's module)
=====================================================
Tests for classical portfolio optimization methods.
"""

import numpy as np
import pandas as pd
import pytest

from app.portfolio.optimization import (
    optimize_portfolio,
    _scipy_optimize,
    _risk_parity,
)


class TestOptimizePortfolio:
    """Test the main optimize_portfolio function."""

    @pytest.fixture
    def returns_df(self):
        np.random.seed(42)
        return pd.DataFrame({
            "A": np.random.normal(0.001, 0.02, 252),
            "B": np.random.normal(0.0008, 0.015, 252),
            "C": np.random.normal(0.0012, 0.025, 252),
            "D": np.random.normal(0.0005, 0.018, 252),
        })

    def test_optimize_equal_weight(self, returns_df):
        result = optimize_portfolio(
            returns_df=returns_df,
            method="equal_weight",
        )

        assert result.symbols == ["A", "B", "C", "D"]
        assert len(result.weights) == 4
        # Equal weight should be 0.25 each
        for w in result.weights:
            assert abs(w - 0.25) < 0.001
        assert result.sharpe_ratio is not None

    def test_optimize_inverse_volatility(self, returns_df):
        result = optimize_portfolio(
            returns_df=returns_df,
            method="inverse_volatility",
        )

        assert len(result.weights) == 4
        # Higher volatility assets should have lower weights
        vols = returns_df.std() * np.sqrt(252)
        # Asset C has highest vol, should have lowest weight
        c_idx = result.symbols.index("C")
        assert result.weights[c_idx] == min(result.weights)

    def test_optimize_inverse_vol_alias(self, returns_df):
        """Test that inverse_vol is alias for inverse_volatility."""
        result1 = optimize_portfolio(returns_df, method="inverse_vol")
        result2 = optimize_portfolio(returns_df, method="inverse_volatility")
        assert np.allclose(result1.weights, result2.weights)

    def test_optimize_min_variance(self, returns_df):
        result = optimize_portfolio(
            returns_df=returns_df,
            method="min_variance",
        )

        assert len(result.weights) == 4
        assert abs(sum(result.weights) - 1.0) < 1e-6
        # All weights should be non-negative (default min_weight=0)
        for w in result.weights:
            assert w >= -1e-6

    def test_optimize_max_sharpe(self, returns_df):
        result = optimize_portfolio(
            returns_df=returns_df,
            method="max_sharpe",
        )

        assert len(result.weights) == 4
        assert abs(sum(result.weights) - 1.0) < 1e-6

    def test_optimize_risk_parity(self, returns_df):
        result = optimize_portfolio(
            returns_df=returns_df,
            method="risk_parity",
        )

        assert len(result.weights) == 4
        assert abs(sum(result.weights) - 1.0) < 1e-6

    def test_optimize_with_constraints(self, returns_df):
        """Test with min/max weight constraints."""
        result = optimize_portfolio(
            returns_df=returns_df,
            method="max_sharpe",
            min_weight=0.1,
            max_weight=0.5,
        )

        assert len(result.weights) == 4
        for w in result.weights:
            assert w >= 0.1 - 1e-6
            assert w <= 0.5 + 1e-6

    def test_optimize_objective_alias(self, returns_df):
        """Test that objective parameter works as alias for method."""
        result1 = optimize_portfolio(returns_df, method="max_sharpe")
        result2 = optimize_portfolio(returns_df, objective="max_sharpe")
        assert np.allclose(result1.weights, result2.weights)

    def test_optimize_invalid_method(self, returns_df):
        with pytest.raises(ValueError, match="Unknown method"):
            optimize_portfolio(returns_df, method="invalid_method")

    def test_optimize_result_fields(self, returns_df):
        result = optimize_portfolio(returns_df, method="max_sharpe")

        assert hasattr(result, "symbols")
        assert hasattr(result, "weights")
        assert hasattr(result, "expected_return")
        assert hasattr(result, "volatility")
        assert hasattr(result, "sharpe_ratio")
        assert hasattr(result, "correlation_matrix")
        assert hasattr(result, "covariance_matrix")
        assert hasattr(result, "effective_n")
        assert hasattr(result, "concentration")

    def test_optimize_effective_n(self, returns_df):
        result = optimize_portfolio(returns_df, method="equal_weight")
        # Equal weight should have effective_n = n
        assert abs(result.effective_n - 4) < 0.1

        result2 = optimize_portfolio(returns_df, method="max_sharpe")
        # Max Sharpe should have lower effective_n (more concentrated)
        assert result2.effective_n < 4


class TestScipyOptimize:
    """Test the internal _scipy_optimize function."""

    def test_scipy_optimize_min_variance(self):
        n = 4
        expected_returns = np.array([0.10, 0.12, 0.08, 0.15])
        cov = np.array([
            [0.04, 0.01, 0.005, 0.002],
            [0.01, 0.03, 0.008, 0.001],
            [0.005, 0.008, 0.05, 0.003],
            [0.002, 0.001, 0.003, 0.02],
        ])

        weights = _scipy_optimize(
            n=n,
            expected_returns=expected_returns,
            cov=cov,
            objective="min_variance",
            risk_free_rate=0.05,
            min_w=0.0,
            max_w=1.0,
        )

        assert len(weights) == 4
        assert abs(sum(weights) - 1.0) < 1e-6
        assert all(w >= -1e-6 for w in weights)

    def test_scipy_optimize_max_sharpe(self):
        n = 4
        expected_returns = np.array([0.10, 0.12, 0.08, 0.15])
        cov = np.eye(4) * 0.04

        weights = _scipy_optimize(
            n=n,
            expected_returns=expected_returns,
            cov=cov,
            objective="max_sharpe",
            risk_free_rate=0.05,
            min_w=0.0,
            max_w=1.0,
        )

        assert len(weights) == 4
        assert abs(sum(weights) - 1.0) < 1e-6

    def test_scipy_optimize_with_bounds(self):
        n = 4
        expected_returns = np.array([0.10, 0.12, 0.08, 0.15])
        cov = np.eye(4) * 0.04

        weights = _scipy_optimize(
            n=n,
            expected_returns=expected_returns,
            cov=cov,
            objective="max_sharpe",
            risk_free_rate=0.05,
            min_w=0.1,
            max_w=0.4,
        )

        assert all(w >= 0.1 - 1e-6 for w in weights)
        assert all(w <= 0.4 + 1e-6 for w in weights)

    def test_scipy_optimize_invalid_objective(self):
        with pytest.raises(ValueError):
            _scipy_optimize(
                n=4,
                expected_returns=np.ones(4) * 0.1,
                cov=np.eye(4) * 0.04,
                objective="invalid",
                risk_free_rate=0.05,
                min_w=0.0,
                max_w=1.0,
            )


class TestRiskParity:
    """Test the internal _risk_parity function."""

    def test_risk_parity_basic(self):
        n = 4
        cov = np.eye(4) * 0.04

        weights = _risk_parity(n=n, cov=cov, min_w=0.0, max_w=1.0)

        assert len(weights) == 4
        assert abs(sum(weights) - 1.0) < 1e-6
        assert all(w >= -1e-6 for w in weights)

    def test_risk_parity_equal_cov(self):
        """With equal covariance, should be equal weight."""
        n = 4
        cov = np.eye(4) * 0.04

        weights = _risk_parity(n=n, cov=cov, min_w=0.0, max_w=1.0)

        for w in weights:
            assert abs(w - 0.25) < 0.01

    def test_risk_parity_with_bounds(self):
        n = 4
        cov = np.eye(4) * 0.04

        weights = _risk_parity(n=n, cov=cov, min_w=0.1, max_w=0.5)

        assert all(w >= 0.1 - 1e-6 for w in weights)
        assert all(w <= 0.5 + 1e-6 for w in weights)

    def test_risk_parity_different_vols(self):
        """With different volatilities, lower vol should get higher weight."""
        n = 3
        cov = np.diag([0.01, 0.04, 0.09])  # Different variances

        weights = _risk_parity(n=n, cov=cov, min_w=0.0, max_w=1.0)

        # Asset 0 (lowest vol) should have highest weight
        assert weights[0] > weights[1] > weights[2]