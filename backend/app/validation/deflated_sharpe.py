"""
Deflated Sharpe Ratio
======================
Adjusts the Sharpe ratio for multiple testing and non-normality.
Based on Bailey & López de Prado (2014).
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats as sp_stats


class DeflatedSharpeResult:
    def __init__(
        self,
        observed_sharpe: float,
        deflated_sharpe: float,
        p_value: float,
        expected_max_sharpe: float,
        num_trials: int,
        skewness: float,
        kurtosis: float,
        is_significant: bool,
    ):
        self.observed_sharpe = observed_sharpe
        self.deflated_sharpe = deflated_sharpe
        self.p_value = p_value
        self.expected_max_sharpe = expected_max_sharpe
        self.num_trials = num_trials
        self.skewness = skewness
        self.kurtosis = kurtosis
        self.is_significant = is_significant

    def to_dict(self) -> dict:
        return {
            "observed_sharpe": self.observed_sharpe,
            "deflated_sharpe": self.deflated_sharpe,
            "p_value": self.p_value,
            "deflated_sharpe_p_value": self.p_value,
            "expected_max_sharpe_under_null": self.expected_max_sharpe,
            "num_trials": self.num_trials,
            "skewness": self.skewness,
            "excess_kurtosis": self.kurtosis,
            "is_significant": self.is_significant,
        }

    def __getitem__(self, item: str):
        return self.to_dict()[item]

    def __contains__(self, item: str):
        return item in self.to_dict()



def deflated_sharpe_ratio(
    observed_sharpe: float | None = None,
    num_trials: int = 1,
    num_observations: int | None = None,
    skewness: float = 0.0,
    kurtosis: float = 3.0,
    significance_level: float = 0.05,
    strategy_returns: pd.Series | None = None,
    risk_free_rate: float = 0.05,
    trading_days: int = 252,
) -> DeflatedSharpeResult:
    """
    Compute the Deflated Sharpe Ratio.

    Adjusts for:
      1. Number of strategies tried (multiple testing)
      2. Non-normality of returns (skewness & kurtosis)
    """
    if strategy_returns is not None:
        from app.quant import formulas as f
        num_observations = len(strategy_returns)
        observed_sharpe = f.sharpe_ratio(strategy_returns, risk_free_rate, trading_days)
        skewness = float(sp_stats.skew(strategy_returns))
        kurtosis = float(sp_stats.kurtosis(strategy_returns, fisher=False))
    elif observed_sharpe is None:
        raise ValueError("Either observed_sharpe or strategy_returns must be provided.")
    elif num_observations is None:
        num_observations = trading_days

    # Expected maximum Sharpe under the null (Euler-Mascheroni)
    e_max_sr = _expected_max_sharpe(num_trials)

    # Standard error of Sharpe (accounting for non-normality)
    se_sharpe = np.sqrt(
        (1.0
         - skewness * observed_sharpe
         + (kurtosis - 1) / 4.0 * observed_sharpe ** 2)
        / num_observations
    )

    if se_sharpe == 0:
        return DeflatedSharpeResult(
            observed_sharpe=observed_sharpe,
            deflated_sharpe=observed_sharpe,
            p_value=0.0,
            expected_max_sharpe=e_max_sr,
            num_trials=num_trials,
            skewness=skewness,
            kurtosis=kurtosis,
            is_significant=True,
        )

    # Deflated Sharpe = (SR_observed - E[max SR]) / SE(SR)
    dsr_statistic = (observed_sharpe - e_max_sr) / se_sharpe

    # p-value from standard normal
    p_value = 1.0 - sp_stats.norm.cdf(dsr_statistic)

    return DeflatedSharpeResult(
        observed_sharpe=observed_sharpe,
        deflated_sharpe=float(dsr_statistic),
        p_value=float(p_value),
        expected_max_sharpe=e_max_sr,
        num_trials=num_trials,
        skewness=skewness,
        kurtosis=kurtosis,
        is_significant=p_value < significance_level,
    )


def _expected_max_sharpe(num_trials: int) -> float:
    """
    Expected maximum Sharpe ratio under the null hypothesis.
    E[max(Z_1,...,Z_N)] approx sqrt(2 ln N) - (ln pi + ln ln N + 0.5772) / (2 sqrt(2 ln N))
    """
    if num_trials <= 1:
        return 0.0
    ln_n = np.log(num_trials)
    z = np.sqrt(2 * ln_n)
    euler = 0.5772156649
    correction = (np.log(np.pi) + np.log(ln_n) + euler) / (2 * z)
    return float(z - correction)
