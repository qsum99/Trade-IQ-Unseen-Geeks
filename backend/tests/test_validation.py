"""
Unit Tests — Validation & Robustness
====================================
Tests Walk-Forward, Purged K-Fold CV, White's Reality Check, Deflated Sharpe, and Cost Stress.
"""

import numpy as np
import pandas as pd
import pytest

from app.validation.deflated_sharpe import deflated_sharpe_ratio
from app.validation.reality_check import whites_reality_check
from app.validation.purged_cv import PurgedKFold
from app.validation.robustness import cost_stress


@pytest.fixture
def strategy_returns():
    rng = np.random.default_rng(42)
    return pd.Series(rng.normal(0.0008, 0.015, 500))


def test_deflated_sharpe_ratio(strategy_returns):
    result = deflated_sharpe_ratio(
        strategy_returns=strategy_returns,
        num_trials=50,
        risk_free_rate=0.05,
    )
    assert 0.0 <= result["deflated_sharpe_p_value"] <= 1.0
    assert "is_significant" in result


def test_whites_reality_check(strategy_returns):
    rng = np.random.default_rng(10)
    # Benchmark returns
    benchmark = pd.Series(rng.normal(0.0003, 0.012, 500))
    # Multiple candidate strategies
    candidates = pd.DataFrame({
        "strat1": strategy_returns,
        "strat2": pd.Series(rng.normal(0.0005, 0.014, 500)),
        "strat3": pd.Series(rng.normal(0.0002, 0.016, 500)),
    })
    wrc_res = whites_reality_check(
        benchmark_returns=benchmark,
        strategy_returns_matrix=candidates,
        num_bootstrap=100,
    )
    assert 0.0 <= wrc_res["p_value"] <= 1.0


def test_purged_kfold():
    n_samples = 100
    pkf = PurgedKFold(n_splits=5, pct_embargo=0.01)
    splits = list(pkf.split(X=np.arange(n_samples)))
    assert len(splits) == 5
    for train_idx, test_idx in splits:
        assert len(train_idx) > 0
        assert len(test_idx) > 0
        # Check no overlap between train and test
        assert len(set(train_idx).intersection(set(test_idx))) == 0


def test_cost_stress():
    rng = np.random.default_rng(42)
    gross_returns = pd.Series(rng.normal(0.001, 0.01, 252))
    stress_res = cost_stress(
        returns=gross_returns,
        trade_count=40,
        cost_levels=[0.0, 0.001, 0.005],
    )
    assert len(stress_res) == 3
    # Higher costs should yield lower or equal Sharpe
    assert stress_res[0]["sharpe"] >= stress_res[-1]["sharpe"]
