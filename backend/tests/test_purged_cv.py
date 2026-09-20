"""
Unit Tests — Purged K-Fold Cross-Validation (Somesh's module)
=============================================================
Tests for purged CV with embargo to prevent data leakage.
"""

import numpy as np
import pandas as pd
import pytest

from app.validation.purged_cv import (
    purged_kfold_cv,
    PurgedCVResult,
    PurgedKFold,
    _consistency,
)


class TestPurgedCVResult:
    """Test the PurgedCVResult container class."""

    def test_purged_cv_result_init(self):
        result = PurgedCVResult()
        assert result.folds == []
        assert result.oos_sharpes == []
        assert result.oos_returns == []

    def test_purged_cv_result_to_dict_empty(self):
        result = PurgedCVResult()
        d = result.to_dict()
        assert d["num_folds"] == 0
        assert d["folds"] == []
        assert d["mean_oos_sharpe"] == 0.0
        assert d["std_oos_sharpe"] == 0.0
        assert d["mean_oos_return"] == 0.0
        assert d["oos_consistency"] == 0.0

    def test_purged_cv_result_to_dict_with_data(self):
        result = PurgedCVResult()
        result.folds = [
            {"fold": 0, "oos_sharpe": 1.0, "oos_return": 0.12},
            {"fold": 1, "oos_sharpe": 1.5, "oos_return": 0.15},
        ]
        result.oos_sharpes = [1.0, 1.5]
        result.oos_returns = [0.12, 0.15]

        d = result.to_dict()
        assert d["num_folds"] == 2
        assert d["mean_oos_sharpe"] == 1.25
        assert d["std_oos_sharpe"] > 0
        assert d["mean_oos_return"] == 0.135
        assert d["oos_consistency"] == 1.0


class TestConsistency:
    """Test the _consistency helper."""

    def test_consistency_all_positive(self):
        sharpes = [1.0, 1.5, 0.8]
        assert _consistency(sharpes) == 1.0

    def test_consistency_mixed(self):
        sharpes = [1.0, -0.5, 0.8, -0.2]
        assert _consistency(sharpes) == 0.5

    def test_consistency_all_negative(self):
        sharpes = [-1.0, -0.5, -0.8]
        assert _consistency(sharpes) == 0.0

    def test_consistency_empty(self):
        assert _consistency([]) == 0.0


class TestPurgedKFoldCV:
    """Test the main purged_kfold_cv function."""

    @pytest.fixture
    def sample_returns(self):
        np.random.seed(42)
        return pd.Series(np.random.normal(0.0005, 0.02, 500))

    @pytest.fixture
    def simple_strategy(self):
        def strategy(returns: pd.Series) -> pd.Series:
            signal = np.sign(returns.shift(1).fillna(0))
            return returns * signal
        return strategy

    def test_purged_kfold_basic(self, sample_returns, simple_strategy):
        result = purged_kfold_cv(
            returns=sample_returns,
            strategy_fn=simple_strategy,
            n_folds=5,
            embargo_pct=0.01,
        )

        assert isinstance(result, PurgedCVResult)
        assert len(result.folds) == 5
        assert len(result.oos_sharpes) == 5
        assert len(result.oos_returns) == 5

    def test_purged_kfold_fold_details(self, sample_returns, simple_strategy):
        result = purged_kfold_cv(
            returns=sample_returns,
            strategy_fn=simple_strategy,
            n_folds=5,
            embargo_pct=0.01,
        )

        fold = result.folds[0]
        assert "fold" in fold
        assert "test_size" in fold
        assert "train_size" in fold
        assert "embargo_size" in fold
        assert "oos_sharpe" in fold
        assert "oos_return" in fold

    def test_purged_kfold_embargo_effect(self, sample_returns, simple_strategy):
        """Test that embargo reduces training set size."""
        result_no_embargo = purged_kfold_cv(
            returns=sample_returns,
            strategy_fn=simple_strategy,
            n_folds=5,
            embargo_pct=0.0,
        )
        result_with_embargo = purged_kfold_cv(
            returns=sample_returns,
            strategy_fn=simple_strategy,
            n_folds=5,
            embargo_pct=0.05,
        )

        # With embargo, training size should be smaller
        for f1, f2 in zip(result_no_embargo.folds, result_with_embargo.folds):
            assert f1["train_size"] >= f2["train_size"]

    def test_purged_kfold_to_dict(self, sample_returns, simple_strategy):
        result = purged_kfold_cv(
            returns=sample_returns,
            strategy_fn=simple_strategy,
            n_folds=5,
            embargo_pct=0.01,
        )

        d = result.to_dict()
        assert "num_folds" in d
        assert "folds" in d
        assert "mean_oos_sharpe" in d
        assert "std_oos_sharpe" in d
        assert "mean_oos_return" in d
        assert "oos_consistency" in d

    def test_purged_kfold_custom_risk_free(self, sample_returns, simple_strategy):
        result = purged_kfold_cv(
            returns=sample_returns,
            strategy_fn=simple_strategy,
            n_folds=5,
            embargo_pct=0.01,
            risk_free_rate=0.03,
            trading_days=252,
        )
        assert len(result.folds) == 5

    def test_purged_kfold_insufficient_data(self):
        """Test with data too small for folds."""
        short_returns = pd.Series(np.random.normal(0.0005, 0.02, 30))
        def dummy_strategy(r): return r

        result = purged_kfold_cv(
            returns=short_returns,
            strategy_fn=dummy_strategy,
            n_folds=5,
            embargo_pct=0.01,
        )
        # Some folds may be skipped due to size constraints
        assert len(result.folds) <= 5


class TestPurgedKFoldClass:
    """Test the scikit-learn compatible PurgedKFold class."""

    def test_purged_kfold_init(self):
        pkf = PurgedKFold(n_splits=5, pct_embargo=0.01)
        assert pkf.n_splits == 5
        assert pkf.pct_embargo == 0.01

    def test_purged_kfold_split(self):
        n_samples = 100
        pkf = PurgedKFold(n_splits=5, pct_embargo=0.01)
        X = np.arange(n_samples)

        splits = list(pkf.split(X))
        assert len(splits) == 5

        for train_idx, test_idx in splits:
            assert len(train_idx) > 0
            assert len(test_idx) > 0
            # No overlap
            assert len(set(train_idx).intersection(set(test_idx))) == 0
            # Test indices should be contiguous
            assert np.array_equal(test_idx, np.arange(test_idx[0], test_idx[-1] + 1))

    def test_purged_kfold_embargo_gap(self):
        """Test that embargo creates gap between train and test."""
        n_samples = 100
        pkf = PurgedKFold(n_splits=5, pct_embargo=0.1)  # 10% embargo
        X = np.arange(n_samples)

        splits = list(pkf.split(X))

        for fold, (train_idx, test_idx) in enumerate(splits):
            test_start = test_idx[0]
            test_end = test_idx[-1]
            # Verify no overlap between train and test (core purged CV property)
            assert len(set(train_idx).intersection(set(test_idx))) == 0

            # Verify embargo gap exists - train should not include indices
            # within embargo_size of test boundaries
            embargo_size = 10  # 10% of 100
            for idx in train_idx:
                # Should not be in [test_start - embargo, test_end + embargo]
                assert idx < test_start - embargo_size or idx > test_end + embargo_size

    def test_purged_kfold_split_with_y(self):
        """Test split works with y parameter (ignored)."""
        n_samples = 100
        pkf = PurgedKFold(n_splits=5, pct_embargo=0.01)
        X = np.arange(n_samples)
        y = np.random.randn(n_samples)

        splits = list(pkf.split(X, y))
        assert len(splits) == 5

    def test_purged_kfold_different_n_splits(self):
        n_samples = 100
        for n_splits in [3, 5, 10]:
            pkf = PurgedKFold(n_splits=n_splits, pct_embargo=0.01)
            splits = list(pkf.split(np.arange(n_samples)))
            assert len(splits) == n_splits