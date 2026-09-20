"""Indicator computations over canonical data. Owned by Satish."""
from __future__ import annotations

import pandas as pd

from app.data import service as data_service
from app.quant import formulas as F


def _prices(symbol: str, start: str, end: str) -> pd.DataFrame:
    _, clean = data_service.get_clean_history(symbol, start, end)
    return clean


def _as_points(index, values) -> list[dict]:
    return [{"date": str(d)[:10], "value": None if pd.isna(v) else round(float(v), 4)} for d, v in zip(index.astype(str), values)]


def sma_points(symbol: str, start: str, end: str, period: int) -> dict:
    df = _prices(symbol, start, end)
    vals = F.sma(df["close"], period)
    return {"symbol": symbol, "indicator": "SMA", "period": period, "values": _as_points(df["timestamp"], vals)}


def ema_points(symbol: str, start: str, end: str, period: int) -> dict:
    df = _prices(symbol, start, end)
    vals = F.ema(df["close"], period)
    return {"symbol": symbol, "indicator": "EMA", "period": period, "values": _as_points(df["timestamp"], vals)}


def returns_summary(symbol: str, start: str, end: str, method: str = "simple") -> dict:
    df = _prices(symbol, start, end)
    rets = F.log_return(df["close"]) if method == "log" else F.simple_return(df["close"])
    return {
        "symbol": symbol,
        "daily_returns": _as_points(df["timestamp"], rets)[-60:],
        "cumulative_return": round(F.cumulative_return(rets), 4),
        "annualized_return": round(F.annualized_return(rets), 4),
    }


def volatility_summary(symbol: str, start: str, end: str, window: int = 20, annualization: int = 252) -> dict:
    df = _prices(symbol, start, end)
    rets = F.simple_return(df["close"])
    roll = F.volatility(rets, window, annualization)
    return {
        "symbol": symbol, "window": window,
        "annualized_volatility": round(float(roll.dropna().iloc[-1]) if roll.dropna().size else 0.0, 4),
        "rolling": _as_points(df["timestamp"], roll),
    }


def sharpe_summary(symbol: str, start: str, end: str, risk_free_rate: float = 0.05, annualization: int = 252) -> dict:
    df = _prices(symbol, start, end)
    rets = F.simple_return(df["close"])
    return {"symbol": symbol, "sharpe_ratio": round(F.sharpe_ratio(rets, risk_free_rate, annualization), 4), "risk_free_rate": risk_free_rate}


def drawdown_summary(symbol: str, start: str, end: str) -> dict:
    df = _prices(symbol, start, end)
    dd = F.max_drawdown(df["close"])
    dd["max_drawdown"] = round(dd["max_drawdown"], 4)
    return dd
