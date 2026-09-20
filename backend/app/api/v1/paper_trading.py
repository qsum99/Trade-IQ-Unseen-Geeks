"""Paper trading & live candles endpoints (Samarth engine + yfinance live feeds)."""
from __future__ import annotations

import datetime
from typing import Any, Dict, Optional

from fastapi import APIRouter
from pydantic import BaseModel
import yfinance as yf

import app.samarth_work as _sw
import sys
sys.modules.setdefault("samarth_work", _sw)

from app.samarth_work.api_logic.backtests_api import paper_trade

router = APIRouter(tags=["paper-trading"])


class PaperTradeRequestModel(BaseModel):
    symbol: str = "BTC-USD"
    strategy: str = "sma_crossover"
    parameters: Optional[Dict[str, Any]] = None
    initial_capital: float = 100000.0
    slippage: float = 0.0005
    execution_price: str = "next_open"
    interval: Optional[str] = "1d"


@router.post("/paper-trade")
@router.post("/paper_trade")
def run_paper_trading(
    body: Optional[PaperTradeRequestModel] = None,
    symbol: Optional[str] = None,
    strategy: Optional[str] = None,
    initial_capital: Optional[float] = None,
    slippage: Optional[float] = None,
    execution_price: Optional[str] = None,
    interval: Optional[str] = None,
):
    s = (body.symbol if body and body.symbol else None) or symbol or "BTC-USD"
    strat = (body.strategy if body and body.strategy else None) or strategy or "sma_crossover"
    params = (body.parameters if body else None) or {}
    cap = (body.initial_capital if body and body.initial_capital is not None else None) or initial_capital or 100000.0
    slip = (body.slippage if body and body.slippage is not None else None) or slippage or 0.0005
    exec_p = (body.execution_price if body and body.execution_price else None) or execution_price or "next_open"
    iv = (body.interval if body and body.interval else None) or interval or "1d"

    try:
        return paper_trade(
            symbol=s,
            strategy=strat,
            parameters=params,
            initial_capital=cap,
            slippage=slip,
            execution_price=exec_p,
            interval=iv,
        )
    except Exception as exc:
        return {
            "success": False,
            "data": None,
            "meta": {"request_id": "req_paper_trade"},
            "error": {"code": "PAPER_TRADE_FAILED", "message": str(exc)},
        }


@router.get("/candles/{symbol}")
def get_candles(
    symbol: str,
    period: str = "1y",
    interval: str = "1d",
):
    """
    GET /candles/{symbol}?period=1y&interval=1d
    Returns OHLCV candle data from yfinance for charting.
    Supports Crypto (BTC-USD, ETH-USD, SOL-USD) and Equities.
    Auto-adjusts period for intraday intervals (e.g., max 60d for 15m).
    """
    effective_period = period
    if interval in ("1m", "5m", "15m", "30m") and period in ("1y", "2y", "5y", "max"):
        effective_period = "60d"
    elif interval == "1h" and period in ("2y", "5y", "max"):
        effective_period = "730d"

    def _fetch(sym: str):
        try:
            ticker = yf.Ticker(sym)
            hist = ticker.history(period=effective_period, interval=interval, timeout=20)
            return hist
        except Exception:
            return None

    hist = _fetch(symbol)
    if hist is None or hist.empty:
        if "." not in symbol and not symbol.endswith("-USD"):
            alt_sym = f"{symbol}.NS"
            hist = _fetch(alt_sym)
            if hist is not None and not hist.empty:
                symbol = alt_sym

    if hist is None or hist.empty:
        return {"success": False, "data": [], "error": f"No candle data for {symbol}"}

    candles = []
    for ts, row in hist.iterrows():
        try:
            date_str = (
                ts.strftime("%Y-%m-%d %H:%M")
                if interval in ("1m", "5m", "15m", "30m", "1h")
                else ts.strftime("%Y-%m-%d")
            )
            candles.append({
                "time": int(ts.timestamp()),
                "date": date_str,
                "open": round(float(row["Open"]), 2),
                "high": round(float(row["High"]), 2),
                "low": round(float(row["Low"]), 2),
                "close": round(float(row["Close"]), 2),
                "volume": int(float(row["Volume"])) if row.get("Volume") is not None else 0,
            })
        except Exception:
            continue

    return {
        "success": True,
        "symbol": symbol,
        "period": effective_period,
        "interval": interval,
        "count": len(candles),
        "data": candles,
    }


@router.get("/candles/{symbol}/tick")
def get_latest_tick(symbol: str, interval: str = "1d"):
    """
    GET /candles/{symbol}/tick?interval=1d
    Returns the latest single candle bar for live-streaming/updates.
    """
    def _fetch_latest(sym: str):
        try:
            ticker = yf.Ticker(sym)
            period = "1d" if interval in ("1m", "5m", "15m", "30m", "1h") else "2d"
            hist = ticker.history(period=period, interval=interval, timeout=10)
            if hist.empty:
                return None
            last = hist.iloc[-1]
            ts = hist.index[-1]
            date_str = (
                ts.strftime("%Y-%m-%d %H:%M")
                if interval in ("1m", "5m", "15m", "30m", "1h")
                else ts.strftime("%Y-%m-%d")
            )
            return {
                "time": int(ts.timestamp()),
                "date": date_str,
                "open": round(float(last["Open"]), 2),
                "high": round(float(last["High"]), 2),
                "low": round(float(last["Low"]), 2),
                "close": round(float(last["Close"]), 2),
                "volume": int(float(last["Volume"])) if last.get("Volume") is not None else 0,
                "fetched_at": datetime.datetime.now().isoformat(),
            }
        except Exception:
            return None

    tick = _fetch_latest(symbol)
    if tick is None and "." not in symbol and not symbol.endswith("-USD"):
        tick = _fetch_latest(f"{symbol}.NS")
        if tick:
            symbol = f"{symbol}.NS"

    if tick is None:
        return {"success": False, "data": None, "error": f"No tick data for {symbol}"}

    return {"success": True, "symbol": symbol, "data": tick}
