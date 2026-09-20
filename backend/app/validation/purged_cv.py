"""
Purged K-Fold Cross-Validation with Embargo
=============================================
Prevents data leakage from overlapping observations/labels.
"""

from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd

from app.quant import formulas as f


class PurgedCVResult:
    def __init__(self):
        self.folds: list[dict] = []
        self.oos_sharpes: list[float] = []
        self.oos_returns: list[float] = []

    def to_dict(self) -> dict:
        return {
            "num_folds": len(self.folds),
            "folds": self.folds,
            "mean_oos_sharpe": float(np.mean(self.oos_sharpes)) if self.oos_sharpes else 0.0,
            "std_oos_sharpe": float(np.std(self.oos_sharpes)) if self.oos_sharpes else 0.0,
            "mean_oos_return": float(np.mean(self.oos_returns)) if self.oos_returns else 0.0,
            "oos_consistency": _consistency(self.oos_sharpes),
        }


def purged_kfold_cv(
    returns: pd.Series,
    strategy_fn: Callable[[pd.Series], pd.Series],
    n_folds: int = 5,
    embargo_pct: float = 0.01,
    risk_free_rate: float = 0.05,
    trading_days: int = 252,
) -> PurgedCVResult:
    """
    Purged K-Fold cross-validation.

    Each fold uses one block as test, remaining blocks as training.
    An embargo gap is added between training and test sets to prevent leakage.

    Parameters
    ----------
    returns : pd.Series
    strategy_fn : callable
        Given returns, produces strategy returns.
    n_folds : int
    embargo_pct : float
        Fraction of total observations used as embargo gap.
    risk_free_rate : float
    trading_days : int
    """
    n = len(returns)
    embargo_size = max(1, int(n * embargo_pct))
    fold_size = n // n_folds

    result = PurgedCVResult()

    for fold_idx in range(n_folds):
        test_start = fold_idx * fold_size
        test_end = min(test_start + fold_size, n)

        # Training: everything NOT in [test_start - embargo, test_end + embargo]
        purge_start = max(0, test_start - embargo_size)
        purge_end = min(n, test_end + embargo_size)

        train_mask = np.ones(n, dtype=bool)
        train_mask[purge_start:purge_end] = False

        train_returns = returns.iloc[train_mask]
        test_returns = returns.iloc[test_start:test_end]

        if len(train_returns) < 20 or len(test_returns) < 5:
            continue

        oos_strat_returns = strategy_fn(test_returns)
        oos_sharpe = f.sharpe_ratio(oos_strat_returns, risk_free_rate, trading_days)
        oos_ret = f.annualized_return(oos_strat_returns, trading_days)

        fold_info = {
            "fold": fold_idx,
            "test_size": int(test_end - test_start),
            "train_size": int(train_mask.sum()),
            "embargo_size": embargo_size,
            "oos_sharpe": oos_sharpe,
            "oos_return": oos_ret,
        }

        result.folds.append(fold_info)
        result.oos_sharpes.append(oos_sharpe)
        result.oos_returns.append(oos_ret)

    return result


def _consistency(sharpes: list[float]) -> float:
    if not sharpes:
        return 0.0
    return float(sum(1 for s in sharpes if s > 0) / len(sharpes))


class PurgedKFold:
    """
    Purged K-Fold Cross-Validator with Embargo.
    Scikit-learn compatible splitter for financial time-series.
    """

    def __init__(self, n_splits: int = 5, pct_embargo: float = 0.01):
        self.n_splits = n_splits
        self.pct_embargo = pct_embargo

    def split(self, X, y=None, groups=None):
        n = len(X)
        embargo_size = max(1, int(n * self.pct_embargo))
        fold_size = n // self.n_splits
        indices = np.arange(n)

        for fold in range(self.n_splits):
            test_start = fold * fold_size
            test_end = min(test_start + fold_size, n)
            test_indices = indices[test_start:test_end]

            purge_start = max(0, test_start - embargo_size)
            purge_end = min(n, test_end + embargo_size)
            train_mask = np.ones(n, dtype=bool)
            train_mask[purge_start:purge_end] = False
            train_indices = indices[train_mask]

            yield train_indices, test_indices

