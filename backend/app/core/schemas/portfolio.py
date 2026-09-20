"""Portfolio domain schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class PortfolioCreateRequest(BaseModel):
    symbols: list[str]
    start_date: str
    end_date: str
    weights: list[float] | None = None
    initial_capital: float = 100000.0


class PortfolioAnalyzeRequest(BaseModel):
    symbols: list[str]
    weights: list[float]
    start_date: str
    end_date: str
    benchmark_symbol: str = "^GSPC"
    risk_free_rate: float = 0.05


class PortfolioOptimizeRequest(BaseModel):
    symbols: list[str]
    start_date: str
    end_date: str
    method: str = "max_sharpe"  # equal_weight | inverse_vol | min_variance | max_sharpe | risk_parity
    risk_free_rate: float = 0.05
    max_weight: float = 1.0
    min_weight: float = 0.0
    target_return: float | None = None
    target_volatility: float | None = None


class PortfolioResult(BaseModel):
    symbols: list[str]
    weights: list[float]
    expected_return: float
    volatility: float
    sharpe_ratio: float
    correlation_matrix: list[list[float]] | None = None
    covariance_matrix: list[list[float]] | None = None
    effective_n: float | None = None
    concentration: float | None = None

    @property
    def optimal_weights(self) -> dict[str, float]:
        return {sym: float(w) for sym, w in zip(self.symbols, self.weights)}

    @property
    def expected_volatility(self) -> float:
        return self.volatility


class PortfolioAnalyticsResult(BaseModel):
    portfolio_return: float
    portfolio_volatility: float
    portfolio_sharpe: float
    correlation_matrix: list[list[float]]
    covariance_matrix: list[list[float]]
    individual_returns: dict[str, float]
    individual_volatilities: dict[str, float]
    concentration: float
    effective_n: float
    turnover: float | None = None

    @property
    def volatility(self) -> float:
        return self.portfolio_volatility

    @property
    def effective_number_of_holdings(self) -> float:
        return self.effective_n
