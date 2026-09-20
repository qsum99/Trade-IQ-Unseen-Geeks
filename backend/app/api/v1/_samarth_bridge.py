"""Bridge to Samarth's engine (strategies/, backtesting/, api_logic/).

Samarth's modules use top-level `samarth_work.*` imports (his tests put
backend/app on sys.path). Under `app.*` we alias the package so his lazy
imports resolve to the SAME module objects — no duplicate copies.
His files are never modified here; ownership stays with Samarth.
"""
from __future__ import annotations

import sys

import app.samarth_work as _sw

sys.modules.setdefault("samarth_work", _sw)

from app.data import service as data_service
from app.samarth_work.api_logic import backtests_api, strategies_api
from app.samarth_work.core_schemas.schemas import MarketBar


def bars_for(symbol: str, start_date: str, end_date: str) -> list[dict]:
    """Canonical MarketData (Satish) -> plain-dict bars (Samarth)."""
    _, clean = data_service.get_clean_history(symbol, start_date, end_date)
    bars = []
    for _, row in clean.iterrows():
        ts = row["timestamp"]
        bars.append({
            "timestamp": ts.isoformat() if hasattr(ts, "isoformat") else str(ts),
            "symbol": symbol,
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"]),
            "adjusted_close": float(row["close"]) if row.get("adjusted_close") is None else float(row["adjusted_close"]),
            "volume": float(row["volume"]) if row.get("volume") is not None else None,
        })
    return bars


def market_bars_for(symbol: str, start_date: str, end_date: str) -> list[MarketBar]:
    """Canonical MarketData (Satish) -> MarketBar objects (Samarth strategies)."""
    return [MarketBar(timestamp=b["timestamp"], symbol=b["symbol"], open=b["open"],
                      high=b["high"], low=b["low"], close=b["close"],
                      adjusted_close=b["adjusted_close"], volume=b["volume"])
            for b in bars_for(symbol, start_date, end_date)]


def known_strategy_ids() -> set[str]:
    try:
        return {s["id"] for s in strategies_api.list_strategies().get("data", [])}
    except (ValueError, AttributeError, TypeError):
        return set()


def http_status_for(code: str) -> int:
    return {"NOT_FOUND": 404, "STRATEGY_NOT_FOUND": 404}.get(code, 0) or (
        422 if code in {"INVALID_PARAMETER", "STRATEGY_FAILED"} else 500
    )


__all__ = ["backtests_api", "bars_for", "http_status_for", "known_strategy_ids", "market_bars_for", "strategies_api"]
