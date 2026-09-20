"""Strategy endpoints (Samarth engine, Satish data)."""
from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from app.api.v1._samarth_bridge import (
    bars_for,
    http_status_for,
    known_strategy_ids,
    market_bars_for,
    strategies_api,
)

router = APIRouter(tags=["strategies"])


class SignalsRequest(BaseModel):
    symbol: str = "NVDA"
    strategy: str = "sma_crossover"
    parameters: dict = Field(default_factory=lambda: {"fast_period": 20, "slow_period": 50})
    start_date: str = "2024-01-01"
    end_date: str = "2025-01-01"


class RegimeAdaptiveRequest(BaseModel):
    symbol: str = "NVDA"
    regime_model: str = "kmeans"
    mapping: dict = Field(default_factory=lambda: {"bull": "momentum", "bear": "mean_reversion"})
    strategy_params: dict = Field(default_factory=dict)
    regime_timeline: list[str] | None = None
    start_date: str = "2024-01-01"
    end_date: str = "2025-01-01"


def _respond(out: dict):
    if out.get("success"):
        return out
    code = ((out.get("error") or {}).get("code")) or "INTERNAL_ERROR"
    return JSONResponse(status_code=http_status_for(code), content=out)


@router.get("/strategies")
def list_strategies():
    return strategies_api.list_strategies()


@router.post("/strategies/signals")
def strategy_signals(req: SignalsRequest):
    if req.strategy not in known_strategy_ids():
        return JSONResponse(status_code=404, content={
            "success": False, "data": None, "meta": {},
            "error": {"code": "STRATEGY_NOT_FOUND", "message": f"Unknown strategy: {req.strategy}", "details": {}}})
    bars = market_bars_for(req.symbol, req.start_date, req.end_date)
    return _respond(strategies_api.signals_for(req.strategy, bars, req.parameters))


@router.post("/strategies/regime-adaptive")
def regime_adaptive(req: RegimeAdaptiveRequest):
    bars = bars_for(req.symbol, req.start_date, req.end_date)
    if req.regime_timeline is None:
        return JSONResponse(status_code=422, content={
            "success": False, "data": None, "meta": {},
            "error": {"code": "INVALID_PARAMETER",
                      "message": "regime_timeline is required (regime detection lands with Somesh's service)",
                      "details": {"bars": len(bars)}}})
    return _respond(strategies_api.regime_adaptive(
        bars, req.regime_timeline, req.mapping, req.strategy_params, req.regime_model))
