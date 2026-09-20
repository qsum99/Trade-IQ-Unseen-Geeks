"""
Portfolio API Routes
=====================
POST /portfolio/create
POST /portfolio/analyze
POST /portfolio/optimize
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from fastapi import APIRouter

from app.core.schemas.common import APIResponse, make_request_id
from app.core.schemas.portfolio import (
    PortfolioAnalyzeRequest,
    PortfolioAnalyticsResult,
    PortfolioOptimizeRequest,
    PortfolioResult,
)
from app.portfolio.analytics import analyse_portfolio
from app.portfolio.optimization import optimize_portfolio

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


def _synthetic_returns_df(symbols: list[str], n: int = 504) -> pd.DataFrame:
    """Synthetic multi-asset returns for development."""
    rng = np.random.default_rng(42)
    data = {}
    for sym in symbols:
        seed = hash(sym) % 2**31
        rng_sym = np.random.default_rng(seed)
        data[sym] = rng_sym.normal(0.0004, 0.015, n)
    return pd.DataFrame(data)


@router.post("/analyze", response_model=APIResponse[PortfolioAnalyticsResult])
async def portfolio_analyze(request: PortfolioAnalyzeRequest):
    """Analyse a portfolio with given weights."""
    returns_df = _synthetic_returns_df(request.symbols)
    weights = np.array(request.weights)

    result = analyse_portfolio(
        returns_df=returns_df,
        weights=weights,
        risk_free_rate=request.risk_free_rate,
    )

    return APIResponse(
        success=True,
        data=result,
        meta={"request_id": make_request_id()},
    )


@router.post("/optimize", response_model=APIResponse[PortfolioResult])
async def portfolio_optimize(request: PortfolioOptimizeRequest):
    """Optimise portfolio weights."""
    returns_df = _synthetic_returns_df(request.symbols)

    result = optimize_portfolio(
        returns_df=returns_df,
        method=request.method,
        risk_free_rate=request.risk_free_rate,
        min_weight=request.min_weight,
        max_weight=request.max_weight,
    )

    return APIResponse(
        success=True,
        data=result,
        meta={"request_id": make_request_id()},
    )
