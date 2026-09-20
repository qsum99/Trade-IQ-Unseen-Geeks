"""
Quantum Analytics & Optimization Package
=======================================
Provides:
  - Multi-Asset QAOA circuits for portfolio optimization (QUBO -> Ising)
  - Variational Quantum Classifier (VQC) for regime detection
  - Native IBM 156-qubit heavy-hex transpilation & SamplerV2 execution
  - Physical measurement decoding and error calibration
"""

from app.quantum.circuits import (
    build_portfolio_hamiltonian,
    build_portfolio_qaoa_circuit,
    build_regime_vqc_circuit,
    build_bell_benchmark_circuit,
    transpile_for_ibm_hardware,
    decode_qaoa_measurements,
)
from app.quantum.experiments import (
    get_ibm_backend_info,
    get_quantum_status,
    quantum_regime_detection,
    quantum_portfolio_optimization,
    get_quantum_job_status,
    get_experiment,
    list_experiments,
)

__all__ = [
    "build_portfolio_hamiltonian",
    "build_portfolio_qaoa_circuit",
    "build_regime_vqc_circuit",
    "build_bell_benchmark_circuit",
    "transpile_for_ibm_hardware",
    "decode_qaoa_measurements",
    "get_ibm_backend_info",
    "get_quantum_status",
    "quantum_regime_detection",
    "quantum_portfolio_optimization",
    "get_quantum_job_status",
    "get_experiment",
    "list_experiments",
]
