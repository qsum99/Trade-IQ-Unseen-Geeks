"""
Unit Tests — Walk-Forward Validation (Somesh's module)
======================================================
Tests for rolling train/test window validation engine.
"""

import numpy as np
import pandas as pd
import pytest

from app.validation.walk_forward import (
    walk_forward_validation,
    WalkForwardResult,
    _performance_decay,
    _consistency_ratio,
)


class TestWalkForwardResult:
    """Test the WalkForwardResult container class."""

    def test_walk_forward_result_init(self):
        result = WalkForwardResult()
        assert result.windows == []
        assert result.oos_returns == []
        assert result.oos_sharpes == []
        assert result.is_sharpes == []

    def test_walk_forward_result_to_dict_empty(self):
        result = WalkForwardResult()
        d = result.to_dict()
        assert d["num_windows"] == 0
        assert d["windows"] == []
        assert d["oos_mean_return"] == 0.0
        assert d["oos_mean_sharpe"] == 0.0
        assert d["is_mean_sharpe"] == 0.0
        assert d["performance_decay"] == 0.0
        assert d["oos_consistency"] == 0.0

    def test_walk_forward_result_to_dict_with_data(self):
        result = WalkForwardResult()
        result.windows = [
            {"window_id": 0, "is_sharpe": 1.5, "oos_sharpe": 1.0, "oos_return": 0.12},
            {"window_id": 1, "is_sharpe": 1.4, "oos_sharpe": 0.9, "oos_return": 0.10},
        ]
        result.oos_returns = [0.12, 0.10]
        result.oos_sharpes = [1.0, 0.9]
        result.is_sharpes = [1.5, 1.4]

        d = result.to_dict()
        assert d["num_windows"] == 2
        assert d["oos_mean_return"] == 0.11
        assert d["oos_mean_sharpe"] == 0.95
        assert d["is_mean_sharpe"] == 1.45
        # performance_decay = 1 - (0.95 / 1.45) = 1 - 0.655 = 0.345
        assert abs(d["performance_decay"] - 0.345) < 0.01
        # consistency = 2/2 = 1.0 (both positive)
        assert d["oos_consistency"] == 1.0


class TestPerformanceDecay:
    """Test the _performance_decay helper."""

    def test_performance_decay_normal(self):
        is_sharpes = [1.5, 1.4, 1.6]
        oos_sharpes = [1.0, 0.9, 1.1]
        decay = _performance_decay(is_sharpes, oos_sharpes)
        # is_mean = 1.5, oos_mean = 1.0, decay = 1 - 1.0/1.5 = 0.333
        assert abs(decay - 0.333) < 0.01

    def test_performance_decay_zero_is_mean(self):
        is_sharpes = [0.0, 0.0]
        oos_sharpes = [0.5, 0.6]
        decay = _performance_decay(is_sharpes, oos_sharpes)
        assert decay == 0.0

    def test_performance_decay_empty(self):
        decay = _performance_decay([], [])
        assert decay == 0.0

    def test_performance_decay_negative_is(self):
        is_sharpes = [-1.0, -1.2]
        oos_sharpes = [-0.5, -0.6]
        decay = _performance_decay(is_sharpes, oos_sharpes)
        # is_mean = -1.1, oos_mean = -0.55, decay = 1 - (-0.55/-1.1) = 1 - 0.5 = 0.5
        assert abs(decay - 0.5) < 0.01


class TestConsistencyRatio:
    """Test the _consistency_ratio helper."""

    def test_consistency_ratio_all_positive(self):
        oos_sharpes = [1.0, 1.5, 0.8, 2.0]
        ratio = _consistency_ratio(oos_sharpes)
        assert ratio == 1.0

    def test_consistency_ratio_mixed(self):
        oos_sharpes = [1.0, -0.5, 0.8, -0.2]
        ratio = _consistency_ratio(oos_sharpes)
        assert ratio == 0.5  # 2 positive out of 4

    def test_consistency_ratio_all_negative(self):
        oos_sharpes = [-1.0, -0.5, -0.8]
        ratio = _consistency_ratio(oos_sharpes)
        assert ratio == 0.0

    def test_consistency_ratio_empty(self):
        ratio = _consistency_ratio([])
        assert ratio == 0.0


class TestWalkForwardValidation:
    """Test the main walk_forward_validation function."""

    @pytest.fixture
    def sample_returns(self):
        np.random.seed(42)
        return pd.Series(np.random.normal(0.0005, 0.02, 500), index=pd.date_range("2020-01-01", periods=500, freq="D"))

    @pytest.fixture
    def simple_strategy(self):
        """Simple momentum strategy for testing."""
        def strategy(returns: pd.Series) -> pd.Series:
            # Long when return > 0, short when return < 0
            signal = np.sign(returns.shift(1).fillna(0))
            return returns * signal
        return strategy

    def test_walk_forward_basic(self, sample_returns, simple_strategy):
        result = walk_forward_validation(
            returns=sample_returns,
            strategy_fn=simple_strategy,
            train_size=100,
            test_size=50,
            step_size=50,
        )

        assert isinstance(result, WalkForwardResult)
        assert result.windows
        assert len(result.windows) > 0
        assert len(result.oos_returns) == len(result.windows)
        assert len(result.oos_sharpes) == len(result.windows)
        assert len(result.is_sharpes) == len(result.windows)

    def test_walk_forward_default_step_size(self, sample_returns, simple_strategy):
        result = walk_forward_validation(
            returns=sample_returns,
            strategy_fn=simple_strategy,
            train_size=100,
            test_size=50,
        )
        # step_size should default to test_size
        assert len(result.windows) > 0

    def test_walk_forward_window_details(self, sample_returns, simple_strategy):
        result = walk_forward_validation(
            returns=sample_returns,
            strategy_fn=simple_strategy,
            train_size=100,
            test_size=50,
            step_size=50,
        )

        window = result.windows[0]
        assert "window_id" in window
        assert "train_start" in window
        assert "train_end" in window
        assert "test_start" in window
        assert "test_end" in window
        assert "is_sharpe" in window
        assert "oos_sharpe" in window
        assert "oos_return" in window

    def test_walk_forward_to_dict(self, sample_returns, simple_strategy):
        result = walk_forward_validation(
            returns=sample_returns,
            strategy_fn=simple_strategy,
            train_size=100,
            test_size=50,
            step_size=50,
        )

        d = result.to_dict()
        assert "num_windows" in d
        assert "windows" in d
        assert "oos_mean_return" in d
        assert "oos_mean_sharpe" in d
        assert "is_mean_sharpe" in d
        assert "performance_decay" in d
        assert "oos_consistency" in d

    def test_walk_forward_insufficient_data(self):
        """Test with insufficient data for even one window."""
        short_returns = pd.Series([0.01, -0.01, 0.02])
        def dummy_strategy(r): return r

        result = walk_forward_validation(
            returns=short_returns,
            strategy_fn=dummy_strategy,
            train_size=100,
            test_size=50,
        )
        # Should return empty result
        assert result.windows == []

    def test_walk_forward_with_risk_free_rate(self, sample_returns, simple_strategy):
        result = walk_forward_validation(
            returns=sample_returns,
            strategy_fn=simple_strategy,
            train_size=100,
            test_size=50,
            risk_free_rate=0.03,
            trading_days=252,
        )
        assert len(result.windows) > 0

    def test_walk_forward_non_datetime_index(self, simple_strategy):
        """Test with integer index."""
        returns = pd.Series(np.random.normal(0.0005, 0.02, 300))
        result = walk_forward_validation(
            returns=returns,
            strategy_fn=simple_strategy,
            train_size=50,
            test_size=25,
        )
        assert len(result.windows) > 0
        # Check that window indices are integers
        assert isinstance(result.windows[0]["train_start"], int)

    def test_walk_forward_different_step_size(self, sample_returns, simple_strategy):
        """Test with step_size different from test_size."""
        result1 = walk_forward_validation(
            returns=sample_returns,
            strategy_fn=simple_strategy,
            train_size=100,
            test_size=50,
            step_size=25,  # Overlapping windows
        )
        result2 = walk_forward_validation(
            returns=sample_returns,
            strategy_fn=simple_strategy,
            train_size=100,
            test_size=50,
            step_size=50,  # Non-overlapping
        )
        # Overlapping should produce more windows
        assert len(result1.windows) > len(result2.windows)