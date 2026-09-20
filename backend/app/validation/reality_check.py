"""
White's Reality Check (Bootstrap)
===================================
Tests whether strategy performance survives multiple-testing bias.
Uses bootstrap to build the distribution of the best strategy's
performance under the null hypothesis.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


class RealityCheckResult:
    def __init__(
        self,
        best_sharpe: float,
        p_value: float,
        num_strategies: int,
        num_bootstrap: int,
        bootstrap_distribution: list[float],
        is_significant: bool,
    ):
        self.best_sharpe = best_sharpe
        self.p_value = p_value
        self.num_strategies = num_strategies
        self.num_bootstrap = num_bootstrap
        self.bootstrap_distribution = bootstrap_distribution
        self.is_significant = is_significant

    def to_dict(self) -> dict:
        return {
            "best_sharpe": self.best_sharpe,
            "p_value": self.p_value,
            "num_strategies": self.num_strategies,
            "num_bootstrap": self.num_bootstrap,
            "is_significant": self.is_significant,
            "bootstrap_percentiles": {
                "5%": float(np.percentile(self.bootstrap_distribution, 5)),
                "50%": float(np.percentile(self.bootstrap_distribution, 50)),
                "95%": float(np.percentile(self.bootstrap_distribution, 95)),
            },
        }

    def __getitem__(self, item: str):
        return self.to_dict()[item]


def whites_reality_check(
    strategy_returns: pd.DataFrame | None = None,
    num_bootstrap: int = 1000,
    block_size: int = 5,
    significance_level: float = 0.05,
    strategy_returns_matrix: pd.DataFrame | None = None,
    benchmark_returns: pd.Series | None = None,
) -> RealityCheckResult:
    """
    White's Reality Check for data snooping.

    Tests H0: the best strategy has zero expected excess performance,
    accounting for the number of strategies tested.

    Parameters
    ----------
    strategy_returns : pd.DataFrame | None
        Columns are different strategies, rows are daily returns.
    num_bootstrap : int
        Number of bootstrap resamples.
    block_size : int
        Block length for circular block bootstrap.
    significance_level : float
    strategy_returns_matrix : pd.DataFrame | None
        Alias for strategy_returns.
    benchmark_returns : pd.Series | None
        Optional benchmark to subtract for excess returns.
    """
    if strategy_returns is None:
        if strategy_returns_matrix is not None:
            strategy_returns = strategy_returns_matrix
        else:
            raise ValueError("strategy_returns or strategy_returns_matrix must be provided.")

    if benchmark_returns is not None:
        strategy_returns = strategy_returns.sub(benchmark_returns, axis=0).dropna()

    n_obs, n_strategies = strategy_returns.shape
    rng = np.random.default_rng(seed=42)

    # Observed mean returns
    observed_means = strategy_returns.mean().values
    best_observed = np.max(observed_means)

    # Centre returns under null (mean = 0)
    centred = strategy_returns.values - observed_means

    # Circular block bootstrap
    bootstrap_max_means = []
    for _ in range(num_bootstrap):
        # Generate block-bootstrap sample indices
        num_blocks = int(np.ceil(n_obs / block_size))
        block_starts = rng.integers(0, n_obs, size=num_blocks)
        indices = np.concatenate([
            np.arange(start, start + block_size) % n_obs
            for start in block_starts
        ])[:n_obs]

        boot_sample = centred[indices]
        boot_means = boot_sample.mean(axis=0)
        bootstrap_max_means.append(float(np.max(boot_means)))

    # p-value: fraction of bootstrap samples where max mean >= observed best
    p_value = float(np.mean(np.array(bootstrap_max_means) >= best_observed))

    return RealityCheckResult(
        best_sharpe=float(best_observed),
        p_value=p_value,
        num_strategies=n_strategies,
        num_bootstrap=num_bootstrap,
        bootstrap_distribution=bootstrap_max_means,
        is_significant=p_value < significance_level,
    )
