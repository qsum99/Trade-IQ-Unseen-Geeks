"""
Unit Tests — Portfolio Allocation (Somesh's module)
====================================================
Tests for weight allocation strategies.
"""

import numpy as np
import pandas as pd
import pytest

from app.portfolio.allocation import (
    equal_weight_allocation,
    inverse_volatility_allocation,
    market_cap_weight,
    allocate_weights,
)


class TestEqualWeightAllocation:
    """Test equal weight allocation."""

    def test_equal_weight_basic(self):
        weights = equal_weight_allocation(4)
        assert len(weights) == 4
        assert np.allclose(weights, 0.25)

    def test_equal_weight_n_assets(self):
        for n in [1, 2, 3, 5, 10, 100]:
            weights = equal_weight_allocation(n)
            assert len(weights) == n
            assert np.allclose(weights, 1.0 / n)

    def test_equal_weight_sum(self):
        weights = equal_weight_allocation(7)
        assert abs(weights.sum() - 1.0) < 1e-10


class TestInverseVolatilityAllocation:
    """Test inverse volatility allocation."""

    def test_inverse_volatility_basic(self):
        returns_df = pd.DataFrame({
            "A": np.random.normal(0.001, 0.01, 100),   # Low vol
            "B": np.random.normal(0.001, 0.02, 100),   # Medium vol
            "C": np.random.normal(0.001, 0.04, 100),   # High vol
        })

        weights = inverse_volatility_allocation(returns_df)

        assert len(weights) == 3
        assert abs(weights.sum() - 1.0) < 1e-10
        # Lower vol should get higher weight
        assert weights[0] > weights[1] > weights[2]

    def test_inverse_volatility_custom_trading_days(self):
        returns_df = pd.DataFrame({
            "A": np.random.normal(0.001, 0.01, 100),
            "B": np.random.normal(0.001, 0.02, 100),
        })

        weights_252 = inverse_volatility_allocation(returns_df, trading_days=252)
        weights_365 = inverse_volatility_allocation(returns_df, trading_days=365)

        # Should be same since trading_days cancels out in relative weights
        assert np.allclose(weights_252, weights_365)


class TestMarketCapWeight:
    """Test market cap weight allocation."""

    def test_market_cap_basic(self):
        caps = np.array([100.0, 200.0, 300.0])
        weights = market_cap_weight(caps)
        assert np.allclose(weights, [1/6, 2/6, 3/6])

    def test_market_cap_zero_total(self):
        caps = np.array([0.0, 0.0, 0.0])
        weights = market_cap_weight(caps)
        assert np.allclose(weights, [1/3, 1/3, 1/3])

    def test_market_cap_single_asset(self):
        caps = np.array([100.0])
        weights = market_cap_weight(caps)
        assert weights[0] == 1.0

    def test_market_cap_sum(self):
        caps = np.array([10.0, 20.0, 30.0, 40.0])
        weights = market_cap_weight(caps)
        assert abs(weights.sum() - 1.0) < 1e-10


class TestAllocateWeights:
    """Test the main allocate_weights function."""

    @pytest.fixture
    def returns_df(self):
        np.random.seed(42)
        return pd.DataFrame({
            "A": np.random.normal(0.001, 0.01, 100),
            "B": np.random.normal(0.001, 0.02, 100),
            "C": np.random.normal(0.001, 0.04, 100),
        })

    def test_allocate_equal_weight(self, returns_df):
        weights = allocate_weights(returns_df, strategy="equal_weight")

        assert isinstance(weights, dict)
        assert set(weights.keys()) == {"A", "B", "C"}
        for w in weights.values():
            assert abs(w - 1/3) < 0.001

    def test_allocate_inverse_volatility(self, returns_df):
        weights = allocate_weights(returns_df, strategy="inverse_volatility")

        assert isinstance(weights, dict)
        assert set(weights.keys()) == {"A", "B", "C"}
        # A (lowest vol) should have highest weight
        assert weights["A"] > weights["B"] > weights["C"]

    def test_allocate_unknown_strategy_fallback(self, returns_df):
        """Unknown strategy should fall back to equal weight."""
        weights = allocate_weights(returns_df, strategy="unknown_strategy")

        for w in weights.values():
            assert abs(w - 1/3) < 0.001

    def test_allocate_empty_dataframe(self):
        empty_df = pd.DataFrame()
        weights = allocate_weights(empty_df)
        assert weights == {}

    def test_allocate_custom_trading_days(self, returns_df):
        weights_252 = allocate_weights(returns_df, strategy="inverse_volatility", trading_days=252)
        weights_365 = allocate_weights(returns_df, strategy="inverse_volatility", trading_days=365)

        # Should be essentially the same since trading_days cancels out in relative weights
        for k in weights_252:
            assert pytest.approx(weights_252[k], rel=1e-10) == weights_365[k]