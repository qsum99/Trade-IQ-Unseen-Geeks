"""
Risk API Routes
================
POST /risk/metrics
POST /risk/var
POST /risk/cvar
POST /risk/monte-carlo
POST /risk/tail
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.core.schemas.common import APIResponse, make_request_id
from app.core.schemas.risk import (
    MonteCarloRequest,
    MonteCarloResult,
    RiskMetricsRequest,
    RiskMetricsResult,
    TailRiskRequest,
    TailRiskResult,
    VaRRequest,
    VaRResult,
)
from app.risk.metrics import compute_risk_metrics
from app.risk.var import compute_var
from app.risk.monte_carlo import run_monte_carlo
from app.risk.tail import compute_tail_risk

router = APIRouter(prefix="/risk", tags=["Risk"])


def _generate_synthetic_returns(symbol: str, n: int = 504) -> pd.Series:
    """Synthetic returns for development/demo. Replace with real data."""
    rng = np.random.default_rng(hash(symbol) % 2**31)
    return pd.Series(rng.normal(0.0004, 0.015, n), name=symbol)


@router.post("/metrics", response_model=APIResponse[RiskMetricsResult])
async def risk_metrics(request: RiskMetricsRequest):
    """Compute comprehensive risk metrics for an asset."""
    returns = _generate_synthetic_returns(request.symbol)
    benchmark = _generate_synthetic_returns(request.benchmark_symbol)

    result = compute_risk_metrics(
        returns=returns,
        benchmark_returns=benchmark,
        risk_free_rate=request.risk_free_rate,
        confidence_levels=request.confidence_levels,
    )
    result.symbol = request.symbol

    return APIResponse(
        success=True,
        data=result,
        meta={"request_id": make_request_id()},
    )


@router.post("/var", response_model=APIResponse[VaRResult])
async def var_endpoint(request: VaRRequest):
    """Compute Value-at-Risk and Conditional VaR."""
    returns = _generate_synthetic_returns(request.symbol)

    result = compute_var(
        returns=returns,
        confidence_level=request.confidence_level,
        method=request.method,
        holding_period=request.holding_period,
    )
    result.symbol = request.symbol

    return APIResponse(
        success=True,
        data=result,
        meta={"request_id": make_request_id()},
    )


@router.post("/cvar", response_model=APIResponse[VaRResult])
async def cvar_endpoint(request: VaRRequest):
    """Compute Conditional VaR (Expected Shortfall)."""
    returns = _generate_synthetic_returns(request.symbol)

    result = compute_var(
        returns=returns,
        confidence_level=request.confidence_level,
        method=request.method,
        holding_period=request.holding_period,
    )
    result.symbol = request.symbol

    return APIResponse(
        success=True,
        data=result,
        meta={"request_id": make_request_id()},
    )


@router.post("/monte-carlo", response_model=APIResponse[MonteCarloResult])
async def monte_carlo_endpoint(request: MonteCarloRequest):
    """Run Monte Carlo risk simulation."""
    returns = _generate_synthetic_returns(request.symbol)

    result = run_monte_carlo(
        returns=returns,
        num_simulations=request.num_simulations,
        num_days=request.num_days,
        initial_value=request.initial_value,
        confidence_level=request.confidence_level,
    )
    result.symbol = request.symbol

    return APIResponse(
        success=True,
        data=result,
        meta={"request_id": make_request_id()},
    )


@router.post("/tail", response_model=APIResponse[TailRiskResult])
async def tail_risk_endpoint(request: TailRiskRequest):
    """Compute tail-risk analysis."""
    returns = _generate_synthetic_returns(request.symbol)
    benchmark = _generate_synthetic_returns(request.benchmark_symbol)

    result = compute_tail_risk(
        returns=returns,
        benchmark_returns=benchmark,
        tail_percentile=request.tail_percentile,
    )
    result.symbol = request.symbol

    return APIResponse(
        success=True,
        data=result,
        meta={"request_id": make_request_id()},
    )
