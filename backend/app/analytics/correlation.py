"""Correlation engine. Owned by Satish."""
from __future__ import annotations

import pandas as pd

from app.data import service as data_service
from app.quant import formulas as F


def _aligned_closes(symbols: list[str], start: str, end: str) -> pd.DataFrame:
    frames = []
    for s in symbols:
        _, clean = data_service.get_clean_history(s, start, end)
        f = clean[["timestamp", "close"]].rename(columns={"close": s})
        frames.append(f)
    df = frames[0]
    for f in frames[1:]:
        df = pd.merge(df, f, on="timestamp", how="inner")
    return df.set_index("timestamp")


def matrix(symbols: list[str], start: str, end: str, method: str = "pearson") -> dict:
    closes = _aligned_closes(symbols, start, end)
    corr = closes.corr(method=method).fillna(0.0)
    return {"method": method, "symbols": symbols, "matrix": corr.values.round(4).tolist()}


def rolling(symbols: list[str], window: int, start: str, end: str) -> dict:
    closes = _aligned_closes(symbols, start, end)
    if len(symbols) < 2:
        return {"window": window, "series": []}
    a, b = closes[symbols[0]], closes[symbols[1]]
    rc = F.rolling_correlation(a, b, window).dropna()
    key = f"{symbols[0]}__{symbols[1]}"
    series = [{"date": str(d)[:10], key: round(float(v), 4)} for d, v in zip(rc.index.astype(str), rc.values)]
    return {"window": window, "series": series}
