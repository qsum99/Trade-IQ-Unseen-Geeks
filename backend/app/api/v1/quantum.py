"""
Quantum API Routes
===================
GET  /quantum/status
GET  /quantum/hardware-report
POST /quantum/regime
POST /quantum/portfolio-optimize
GET  /quantum/experiments/{id}
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.core.schemas.common import APIResponse, make_request_id
from app.core.schemas.quantum import (
    QuantumPortfolioRequest,
    QuantumRegimeRequest,
)
from app.quantum.experiments import (
    get_ibm_backend_info,
    get_quantum_status,
    quantum_regime_detection,
    quantum_portfolio_optimization,
    get_experiment,
    list_experiments,
)
from app.quant import formulas as f

router = APIRouter(prefix="/quantum", tags=["Quantum"])


@router.get("/status", response_model=APIResponse)
async def quantum_status():
    """Check quantum computing availability."""
    status = get_quantum_status()
    return APIResponse(
        success=True,
        data=status,
        meta={"request_id": make_request_id()},
    )


@router.get("/hardware-report", response_model=APIResponse)
async def hardware_report():
    """
    Get detailed IBM Quantum hardware report including error rates,
    gate fidelities, T1/T2 times, and qubit calibration data.
    This is the FIRST thing to check — real hardware error data
    informs circuit design decisions.
    """
    report = get_ibm_backend_info()
    return APIResponse(
        success=True,
        data=report,
        meta={"request_id": make_request_id()},
    )


@router.post("/regime", response_model=APIResponse)
async def quantum_regime(request: QuantumRegimeRequest):
    """Run quantum regime detection experiment (PennyLane VQC)."""
    # Generate synthetic market features
    rng = np.random.default_rng(hash(request.symbol) % 2**31)
    n_samples = 200
    features = rng.normal(0, 1, size=(n_samples, 4))

    # Generate labels from classical K-Means for supervised training
    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler

    scaler = StandardScaler()
    features_scaled = scaler.fit_transform(features)
    kmeans = KMeans(n_clusters=4, random_state=42, n_init=10)
    labels = kmeans.fit_predict(features_scaled)

    result = quantum_regime_detection(
        features=features_scaled,
        labels=labels,
        num_qubits=request.num_qubits,
        num_layers=request.num_layers,
    )
    result["symbol"] = request.symbol

    return APIResponse(
        success=True,
        data=result,
        meta={"request_id": make_request_id()},
    )


@router.post("/portfolio-optimize", response_model=APIResponse)
async def quantum_portfolio(request: QuantumPortfolioRequest):
    """Run quantum portfolio optimization experiment (QAOA)."""
    n = len(request.symbols)

    # Generate synthetic returns and compute expected returns + cov
    rng = np.random.default_rng(42)
    returns_data = {}
    for sym in request.symbols:
        seed = hash(sym) % 2**31
        rng_sym = np.random.default_rng(seed)
        returns_data[sym] = rng_sym.normal(0.0004, 0.015, 504)

    returns_df = pd.DataFrame(returns_data)
    expected_returns = (returns_df.mean() * 252).values
    cov_matrix = f.covariance_matrix(returns_df)

    result = quantum_portfolio_optimization(
        expected_returns=expected_returns,
        cov_matrix=cov_matrix,
        symbols=request.symbols,
        budget=request.budget,
        use_real_hardware=request.use_real_hardware,
        num_qubits=request.num_qubits,
    )

    return APIResponse(
        success=True,
        data=result,
        meta={"request_id": make_request_id()},
    )


@router.get("/experiments/{experiment_id}", response_model=APIResponse)
async def get_experiment_endpoint(experiment_id: str):
    """Retrieve a quantum experiment result."""
    exp = get_experiment(experiment_id)
    if exp is None:
        raise HTTPException(status_code=404, detail="Experiment not found")

    return APIResponse(
        success=True,
        data=exp,
        meta={"request_id": make_request_id()},
    )


@router.get("/experiments", response_model=APIResponse)
async def list_experiments_endpoint():
    """List all quantum experiments."""
    exps = list_experiments()
    return APIResponse(
        success=True,
        data=exps,
        meta={"request_id": make_request_id()},
    )


@router.get("/jobs/{job_id}", response_model=APIResponse)
async def get_quantum_job_endpoint(job_id: str):
    """
    Poll the status of a quantum job from IBM Quantum Platform and PostgreSQL.
    Retrieves physical measurement counts, fidelity, and error reports.
    """
    from app.quantum.experiments import get_quantum_job_status
    job = get_quantum_job_status(job_id)
    if not job or job.get("status") == "ERROR":
        raise HTTPException(status_code=404, detail=job.get("error", "Quantum job not found"))

    return APIResponse(
        success=True,
        data=job,
        meta={"request_id": make_request_id()},
    )
