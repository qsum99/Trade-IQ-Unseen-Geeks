"""Data service: provider -> normalize -> canonical. Owned by Satish."""
from __future__ import annotations

import pandas as pd

from app.data import normalization
from app.integrations import market_api


def get_clean_history(symbol: str, start_date: str, end_date: str, interval: str = "1d") -> tuple[pd.DataFrame, pd.DataFrame]:
    raw = market_api.client.get_history(symbol, start_date, end_date, interval)
    clean = normalization.normalize(raw)
    return raw, clean


def get_quality(symbol: str, start_date: str, end_date: str, provider: str = "yahoo") -> dict:
    raw, clean = get_clean_history(symbol, start_date, end_date)
    report = normalization.quality_report(raw, clean, symbol)
    return report.model_dump()
