"""Backtest endpoints (Samarth engine + store, Satish data)."""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.api.v1._samarth_bridge import backtests_api, bars_for, http_status_for

router = APIRouter(tags=["backtests"])


def _respond(out: dict):
    if out.get("success"):
        return out
    code = ((out.get("error") or {}).get("code")) or "INTERNAL_ERROR"
    return JSONResponse(status_code=http_status_for(code), content=out)


@router.post("/backtests")
def run_backtest(body: dict):
    symbol = body.get("symbol", "NVDA")
    period = body.get("period", {}) or {}
    bars = bars_for(symbol, period.get("start_date", "2023-01-01"), period.get("end_date", "2025-01-01"))
    return _respond(backtests_api.run_backtest(body, bars))


@router.get("/backtests")
def list_backtests():
    return backtests_api.list_backtests()


@router.get("/backtests/{backtest_id}")
def get_backtest(backtest_id: str):
    return _respond(backtests_api.get_backtest(backtest_id))


@router.get("/backtests/{backtest_id}/equity")
def get_equity(backtest_id: str):
    return _respond(backtests_api.get_equity(backtest_id))


@router.get("/backtests/{backtest_id}/trades")
def get_trades(backtest_id: str):
    return _respond(backtests_api.get_trades(backtest_id))


@router.get("/backtests/{backtest_id}/metrics")
def get_metrics(backtest_id: str):
    return _respond(backtests_api.get_metrics(backtest_id))


@router.get("/backtests/{backtest_id}/benchmark")
def get_benchmark(backtest_id: str):
    return _respond(backtests_api.get_benchmark(backtest_id))


@router.get("/backtests/{backtest_id}/trust-report")
def trust_report(backtest_id: str):
    return backtests_api.trust_report(backtest_id)
