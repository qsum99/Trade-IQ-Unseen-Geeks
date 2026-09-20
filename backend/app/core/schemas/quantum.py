"""Quantum domain schemas."""

from __future__ import annotations

from pydantic import BaseModel, Field


class QuantumStatusResponse(BaseModel):
    available: bool
    backend_name: str | None = None
    num_qubits: int | None = None
    simulator: bool = True
    pending_jobs: int = 0
    error: str | None = None


class QuantumRegimeRequest(BaseModel):
    symbol: str
    start_date: str
    end_date: str
    features: list[str] = Field(default_factory=lambda: ["return", "volatility", "momentum"])
    model: str = "vqc"
    backend: str = "default.qubit"
    num_qubits: int = 4
    num_layers: int = 2
    use_real_hardware: bool = False


class QuantumRegimeResult(BaseModel):
    experiment_id: str
    symbol: str
    method: str  # "pennylane_vqc"
    backend: str
    regimes: list[dict]
    accuracy: float | None = None
    classical_comparison: dict | None = None
    circuit_depth: int | None = None
    num_qubits: int
    error_report: dict | None = None


class QuantumPortfolioRequest(BaseModel):
    symbols: list[str]
    start_date: str
    end_date: str
    num_assets: int | None = None
    budget: int | None = None
    use_real_hardware: bool = False
    num_qubits: int | None = None


class QuantumPortfolioResult(BaseModel):
    experiment_id: str
    symbols: list[str]
    method: str  # "qaoa"
    backend: str
    optimal_weights: list[float]
    expected_return: float
    volatility: float
    sharpe_ratio: float
    classical_comparison: dict | None = None
    circuit_depth: int | None = None
    num_qubits: int
    error_report: dict | None = None


class QuantumExperimentResult(BaseModel):
    experiment_id: str
    experiment_type: str
    status: str
    backend: str
    created_at: str
    result: dict | None = None
    error_report: dict | None = None
