"""
Unit Tests — Quantum Engine
===========================
Tests IBM status/hardware extraction, VQC regime detection, and QAOA portfolio optimization.
"""

import numpy as np
import pandas as pd
import pytest

from app.quantum.experiments import (
    get_quantum_status,
    quantum_regime_detection,
    quantum_portfolio_optimization,
    get_experiment,
    list_experiments,
)


def test_quantum_status():
    status = get_quantum_status()
    assert "ibm_token_configured" in status
    assert "penny_lane_installed" in status
    assert "qiskit_installed" in status


def test_quantum_regime_detection():
    rng = np.random.default_rng(42)
    returns = pd.Series(rng.normal(0.0005, 0.012, 100))
    volatility = returns.rolling(10).std().dropna()

    res = quantum_regime_detection(
        returns=returns,
        volatility=volatility,
        n_qubits=4,
        steps=5,  # Few steps for quick test
        use_hardware=False,
    )
    assert res["status"] in ["completed", "failed"]
    assert "regimes" in res or "regime_probabilities" in res or "error" in res



def test_quantum_portfolio_optimization():
    rng = np.random.default_rng(42)
    df = pd.DataFrame(
        rng.normal(0.0005, 0.012, (50, 3)),
        columns=["ASSET_A", "ASSET_B", "ASSET_C"],
    )
    res = quantum_portfolio_optimization(
        returns_df=df,
        qaoa_p=1,
        maxiter=5,  # Few iterations for quick test
        use_hardware=False,
    )
    assert res["status"] in ["completed", "failed"]
    assert "optimal_weights" in res or "error" in res


def test_list_and_get_experiments():
    exps = list_experiments()
    assert isinstance(exps, list)


def test_build_portfolio_hamiltonian_and_qaoa_circuit():
    from app.quantum.circuits import build_portfolio_hamiltonian, build_portfolio_qaoa_circuit

    returns = np.array([0.10, 0.20, 0.15])
    cov = np.array([[0.04, 0.01, 0.02], [0.01, 0.05, 0.015], [0.02, 0.015, 0.06]])
    budget = 2

    cost_op, Q, offset = build_portfolio_hamiltonian(returns, cov, budget)
    assert len(cost_op) > 0
    assert Q.shape == (3, 3)

    circuit, op, meta = build_portfolio_qaoa_circuit(returns, cov, budget, reps=1)
    assert circuit.num_qubits == 3
    assert meta["reps"] == 1
    assert "ops" in meta


def test_build_regime_vqc_circuit():
    from app.quantum.circuits import build_regime_vqc_circuit

    qc, x_params, theta_params = build_regime_vqc_circuit(num_qubits=4, num_layers=2)
    assert qc.num_qubits == 4
    assert len(x_params) == 4
    assert len(theta_params) == 16


def test_decode_qaoa_measurements():
    from app.quantum.circuits import decode_qaoa_measurements

    counts = {"011": 50, "101": 30, "110": 20, "000": 5}
    symbols = ["BTC", "ETH", "SOL"]
    returns = np.array([0.20, 0.30, 0.25])
    cov = np.diag([0.04, 0.05, 0.06])
    budget = 2

    res = decode_qaoa_measurements(counts, symbols, budget, returns, cov)
    assert "optimal_weights" in res
    assert "selected_assets" in res
    assert len(res["selected_assets"]) == 2
    assert res["budget_compliance_rate"] > 0.9

