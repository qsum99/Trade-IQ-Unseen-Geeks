"""
Weight Allocation Strategies
==============================
Simple allocation schemes used before or instead of optimisation.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from app.quant import formulas as f


def equal_weight_allocation(n_assets: int) -> np.ndarray:
    """1/N allocation."""
    return f.equal_weight(n_assets)


def inverse_volatility_allocation(
    returns_df: pd.DataFrame,
    trading_days: int = 252,
) -> np.ndarray:
    """Weights inversely proportional to volatility."""
    vols = np.array([
        returns_df[col].std() * np.sqrt(trading_days)
        for col in returns_df.columns
    ])
    return f.inverse_volatility_weight(vols)


def market_cap_weight(market_caps: np.ndarray) -> np.ndarray:
    """Market-cap weighted allocation."""
    total = market_caps.sum()
    if total == 0:
        return np.ones(len(market_caps)) / len(market_caps)
    return market_caps / total


def allocate_weights(
    returns_df: pd.DataFrame,
    strategy: str = "equal_weight",
    trading_days: int = 252,
) -> dict[str, float]:
    """Allocate portfolio weights across assets using chosen heuristic."""
    symbols = list(returns_df.columns)
    n = len(symbols)
    if n == 0:
        return {}
    if strategy == "equal_weight":
        raw = equal_weight_allocation(n)
    elif strategy == "inverse_volatility":
        raw = inverse_volatility_allocation(returns_df, trading_days=trading_days)
    else:
        raw = equal_weight_allocation(n)
    return {sym: float(w) for sym, w in zip(symbols, raw)}

