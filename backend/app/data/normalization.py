"""Canonical normalization + data-quality checks. Owned by Satish."""
from __future__ import annotations

import pandas as pd

from app.core.schemas.market import DataQualityReport

REQUIRED_COLS = ["timestamp", "symbol", "open", "high", "low", "close"]


def normalize(df: pd.DataFrame) -> pd.DataFrame:
    """Sort, dedupe, coerce types, drop invalid OHLC rows into canonical form."""
    if df.empty:
        return df
    df = df.copy()
    df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
    for c in ["open", "high", "low", "close"]:
        df[c] = pd.to_numeric(df[c], errors="coerce")
    if "volume" in df.columns:
        df["volume"] = pd.to_numeric(df["volume"], errors="coerce")
    # Invalid OHLC: high < low, negative prices, NaN close
    valid = (
        df["close"].notna() & (df["close"] > 0)
        & (df["high"] >= df["low"])
        & (df["high"] >= df["close"]) & (df["low"] <= df["close"])
    )
    df = df[valid]
    df = df.drop_duplicates(subset=["timestamp", "symbol"], keep="last")
    df = df.sort_values("timestamp").reset_index(drop=True)
    return df


def quality_report(df_raw: pd.DataFrame, df_clean: pd.DataFrame, symbol: str) -> DataQualityReport:
    records = len(df_clean)
    missing = int(df_raw.isna().sum().sum()) if not df_raw.empty else 0
    dupes = int(df_raw.duplicated(subset=["timestamp", "symbol"]).sum()) if not df_raw.empty and "timestamp" in df_raw else 0
    invalid = len(df_raw) - len(df_clean) if len(df_raw) >= len(df_clean) else 0
    gaps = 0
    if records > 1:
        diffs = pd.to_datetime(df_clean["timestamp"]).diff().dt.days.fillna(1)
        gaps = int((diffs > 5).sum())  # weekly+ gap flag for daily data
    score = 100.0
    if len(df_raw) > 0:
        score = max(0.0, round(100 * (1 - (missing + dupes + max(invalid, 0)) / max(len(df_raw), 1)), 2))
    return DataQualityReport(
        symbol=symbol, records=records, missing_values=missing,
        duplicate_records=dupes, invalid_prices=max(invalid, 0),
        date_gaps=gaps, quality_score=score,
    )
