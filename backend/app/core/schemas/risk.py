"""Risk domain schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RiskMetricsRequest(BaseModel):
    symbol: str
    start_date: str
    end_date: str
    benchmark_symbol: str = "^GSPC"
    risk_free_rate: float = 0.05
    confidence_levels: list[float] = Field(default_factory=lambda: [0.95, 0.99])


class RiskMetricsResult(BaseModel):
    symbol: str
    volatility: float
    annualized_volatility: float
    sharpe_ratio: float
    sortino_ratio: float
    calmar_ratio: float
    omega_ratio: float
    max_drawdown: float
    max_drawdown_duration_days: int | None = None
    beta: float | None = None
    alpha: float | None = None
    treynor_ratio: float | None = None
    information_ratio: float | None = None
    tracking_error: float | None = None
    downside_deviation: float
    var_95: float
    var_99: float
    cvar_95: float
    cvar_99: float


class VaRRequest(BaseModel):
    symbol: str
    start_date: str
    end_date: str
    confidence_level: float = 0.95
    method: str = "historical"  # historical | parametric | cornish_fisher
    holding_period: int = 1


class VaRResult(BaseModel):
    symbol: str
    confidence_level: float
    method: str
    var: float
    cvar: float
    holding_period: int


class MonteCarloRequest(BaseModel):
    symbol: str
    start_date: str
    end_date: str
    num_simulations: int = 10000
    num_days: int = 252
    initial_value: float = 100000.0
    confidence_level: float = 0.95


class MonteCarloResult(BaseModel):
    symbol: str
    num_simulations: int
    num_days: int
    initial_value: float
    mean_final_value: float
    median_final_value: float
    std_final_value: float
    var: float
    cvar: float
    probability_of_loss: float
    percentile_5: float
    percentile_25: float
    percentile_75: float
    percentile_95: float
    max_drawdown_mean: float
    max_drawdown_95: float
    sample_paths: list[list[float]] = Field(
        default_factory=list,
        description="A few sample simulated paths for visualisation",
    )


class TailRiskRequest(BaseModel):
    symbol: str
    start_date: str
    end_date: str
    benchmark_symbol: str = "^GSPC"
    tail_percentile: float = 0.05


class TailRiskResult(BaseModel):
    symbol: str
    worst_days_pct: float
    benchmark_worst_return: float
    strategy_return_during_worst: float
    tail_correlation: float
    downside_beta: float
    maximum_loss: float
    cvar: float
