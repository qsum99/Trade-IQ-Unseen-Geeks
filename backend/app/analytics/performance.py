"""Combined performance summary. Owned by Satish."""
from __future__ import annotations

from app.analytics import indicators as I


def summary(symbol: str, start: str, end: str, cfg: dict) -> dict:
    sma_periods = (cfg.get("sma") or [20]) if isinstance(cfg.get("sma"), list) else [20]
    ema_periods = (cfg.get("ema") or [20]) if isinstance(cfg.get("ema"), list) else [20]
    out: dict = {"symbol": symbol}
    out["sma"] = {str(p): I.sma_points(symbol, start, end, int(p)) for p in sma_periods}
    out["ema"] = {str(p): I.ema_points(symbol, start, end, int(p)) for p in ema_periods}
    if cfg.get("returns", True):
        out["returns"] = I.returns_summary(symbol, start, end)
    if cfg.get("volatility", True):
        out["volatility"] = I.volatility_summary(symbol, start, end)
    if cfg.get("sharpe", True):
        out["sharpe"] = I.sharpe_summary(symbol, start, end)
    if cfg.get("drawdown", True):
        out["drawdown"] = I.drawdown_summary(symbol, start, end)
    return out
