"""
Validation / Robustness API Routes
====================================
POST /robustness/walk-forward
POST /robustness/parameter-stress
POST /robustness/cost-stress
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.core.schemas.common import APIResponse, make_request_id
from app.validation.walk_forward import walk_forward_validation
from app.validation.robustness import cost_stress
from app.validation.reality_check import whites_reality_check
from app.validation.deflated_sharpe import deflated_sharpe_ratio
from app.quant import formulas as f

router = APIRouter(prefix="/robustness", tags=["Robustness / Validation"])


# ── Request schemas ─────────────────────────────────────────────────────

class WalkForwardRequest(BaseModel):
    symbol: str
    start_date: str
    end_date: str
    train_size: int = 252
    test_size: int = 63
    risk_free_rate: float = 0.05


class CostStressRequest(BaseModel):
    symbol: str
    start_date: str
    end_date: str
    trade_count: int = 50
    cost_levels: list[float] = Field(
        default_factory=lambda: [0.0, 0.0005, 0.001, 0.002, 0.005, 0.01]
    )


class RealityCheckRequest(BaseModel):
    symbol: str
    start_date: str
    end_date: str
    num_strategies: int = 5
    num_bootstrap: int = 1000


class DeflatedSharpeRequest(BaseModel):
    observed_sharpe: float
    num_trials: int
    num_observations: int
    skewness: float = 0.0
    kurtosis: float = 3.0


# ── Helpers ─────────────────────────────────────────────────────────────

def _synthetic_returns(symbol: str, n: int = 504) -> pd.Series:
    rng = np.random.default_rng(hash(symbol) % 2**31)
    return pd.Series(rng.normal(0.0004, 0.015, n), name=symbol)


def _simple_sma_strategy(returns: pd.Series, **kwargs) -> pd.Series:
    """Simple SMA strategy for walk-forward testing."""
    prices = (1 + returns).cumprod()
    fast = f.sma(prices, kwargs.get("fast", 20))
    slow = f.sma(prices, kwargs.get("slow", 50))
    signal = (fast > slow).astype(float).shift(1).fillna(0)
    return returns * signal


# ── Endpoints ───────────────────────────────────────────────────────────

@router.post("/walk-forward", response_model=APIResponse)
async def walk_forward_endpoint(request: WalkForwardRequest):
    """Run walk-forward validation."""
    returns = _synthetic_returns(request.symbol)

    result = walk_forward_validation(
        returns=returns,
        strategy_fn=_simple_sma_strategy,
        train_size=request.train_size,
        test_size=request.test_size,
        risk_free_rate=request.risk_free_rate,
    )

    return APIResponse(
        success=True,
        data=result.to_dict(),
        meta={"request_id": make_request_id()},
    )


@router.post("/cost-stress", response_model=APIResponse)
async def cost_stress_endpoint(request: CostStressRequest):
    """Test strategy viability under increasing costs."""
    returns = _synthetic_returns(request.symbol)

    results = cost_stress(
        base_returns=returns,
        trade_count=request.trade_count,
        total_days=len(returns),
        cost_levels=request.cost_levels,
    )

    return APIResponse(
        success=True,
        data=results,
        meta={"request_id": make_request_id()},
    )


@router.post("/reality-check", response_model=APIResponse)
async def reality_check_endpoint(request: RealityCheckRequest):
    """Run White's Reality Check for multiple-testing bias."""
    # Generate synthetic multi-strategy returns
    rng = np.random.default_rng(hash(request.symbol) % 2**31)
    strategy_returns = pd.DataFrame({
        f"strategy_{i}": rng.normal(0.0002 * (i + 1), 0.015, 504)
        for i in range(request.num_strategies)
    })

    result = whites_reality_check(
        strategy_returns=strategy_returns,
        num_bootstrap=request.num_bootstrap,
    )

    return APIResponse(
        success=True,
        data=result.to_dict(),
        meta={"request_id": make_request_id()},
    )


@router.post("/deflated-sharpe", response_model=APIResponse)
async def deflated_sharpe_endpoint(request: DeflatedSharpeRequest):
    """Compute Deflated Sharpe Ratio."""
    result = deflated_sharpe_ratio(
        observed_sharpe=request.observed_sharpe,
        num_trials=request.num_trials,
        num_observations=request.num_observations,
        skewness=request.skewness,
        kurtosis=request.kurtosis,
    )

    return APIResponse(
        success=True,
        data=result.to_dict(),
        meta={"request_id": make_request_id()},
    )
