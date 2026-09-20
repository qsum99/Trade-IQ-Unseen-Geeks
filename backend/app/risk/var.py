"""
Value-at-Risk & Conditional VaR Engine
=======================================
Supports historical, parametric, and Cornish-Fisher methods.
"""

from __future__ import annotations

import pandas as pd

from app.quant import formulas as f
from app.core.schemas.risk import VaRRequest, VaRResult


def compute_var(
    returns: pd.Series,
    confidence_level: float = 0.95,
    method: str = "historical",
    holding_period: int = 1,
) -> VaRResult:
    """
    Compute VaR and CVaR.

    Parameters
    ----------
    returns : pd.Series
        Daily return series.
    confidence_level : float
        E.g. 0.95 or 0.99.
    method : str
        "historical" | "parametric" | "cornish_fisher"
    holding_period : int
        Holding period in days (scales by √t).
    """
    import numpy as np

    # Scale returns for multi-day holding period
    if holding_period > 1:
        hp_returns = returns.rolling(holding_period).sum().dropna()
    else:
        hp_returns = returns

    var = f.value_at_risk(hp_returns, confidence_level, method)
    cvar = f.conditional_var(hp_returns, confidence_level, method)

    return VaRResult(
        symbol="",
        confidence_level=confidence_level,
        method=method,
        var=var,
        cvar=cvar,
        holding_period=holding_period,
    )
