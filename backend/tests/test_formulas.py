import pandas as pd

from app.data import normalization as N
from app.quant import formulas as F


def test_sma_ema():
    s = pd.Series([1, 2, 3, 4, 5], dtype=float)
    assert F.sma(s, 3).iloc[-1] == 4.0
    assert F.ema(s, 3).iloc[-1] > 0


def test_returns_sharpe_drawdown():
    prices = pd.Series([100, 101, 102, 101, 105, 107], dtype=float)
    rets = F.simple_return(prices)
    assert abs(F.cumulative_return(rets) - 0.07) < 1e-9
    assert isinstance(F.sharpe_ratio(rets), float)
    dd = F.max_drawdown(prices)
    assert dd["max_drawdown"] <= 0


def test_var_cvar_beta():
    rets = pd.Series([0.01, -0.02, 0.015, -0.03, 0.02, -0.01] * 20)
    assert F.value_at_risk(rets, 0.95) >= 0
    assert F.conditional_var(rets, 0.95) >= F.value_at_risk(rets, 0.95)
    assert isinstance(F.beta(rets, rets), float)


def test_normalization():
    import pandas as pd
    df = pd.DataFrame([
        {"timestamp": "2024-01-01", "symbol": "NVDA", "open": 1, "high": 2, "low": 0.5, "close": 1.5, "volume": 100},
        {"timestamp": "2024-01-01", "symbol": "NVDA", "open": 1, "high": 2, "low": 0.5, "close": 1.5, "volume": 100},
        {"timestamp": "2024-01-02", "symbol": "NVDA", "open": 1, "high": 0.5, "low": 2, "close": -1, "volume": 100},
    ])
    clean = N.normalize(df)
    assert len(clean) == 1  # dupe removed, invalid removed
