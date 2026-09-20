"""
Institutional Quantum Circuits Module
====================================
Production-grade quantum circuit builders for financial optimization and analytics:
1. Multi-Asset Portfolio QAOA (QUBO -> Ising Hamiltonian with ZZ couplers)
2. Variational Quantum Classifier (VQC) for Regime Detection
3. Maximally Entangled Bell State Calibration Benchmark
4. IBM Quantum Hardware Transpilation & ISA Mapping (156-qubit architecture)
5. QPU Bitstring Measurement Decoding & Energy Evaluation
"""

from __future__ import annotations

import logging
from typing import Any
import numpy as np

from qiskit import QuantumCircuit
from qiskit.circuit import ParameterVector
from qiskit.circuit.library import QAOAAnsatz
from qiskit.quantum_info import SparsePauliOp
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════════════════
# 1. PORTFOLIO QAOA CIRCUIT & HAMILTONIAN BUILDERS
# ═══════════════════════════════════════════════════════════════════════

def build_portfolio_hamiltonian(
    expected_returns: np.ndarray,
    cov_matrix: np.ndarray,
    budget: int,
    risk_factor: float = 0.5,
    penalty: float = 4.0,
) -> tuple[SparsePauliOp, np.ndarray, float]:
    """
    Formulate the Markowitz Portfolio Selection problem as a QUBO and convert
    to an Ising Cost Hamiltonian:
      H_cost = sum_i h_i Z_i + sum_{i < j} J_ij Z_i Z_j + offset * I

    Parameters
    ----------
    expected_returns : np.ndarray
        Vector of annualized expected returns for N assets.
    cov_matrix : np.ndarray
        Covariance matrix (N x N) of asset returns.
    budget : int
        Number of assets to select (cardinality constraint).
    risk_factor : float
        Risk aversion parameter lambda (higher = more penalty on volatility).
    penalty : float
        Lagrange multiplier penalty A for violating budget constraint sum(x_i) == budget.

    Returns
    -------
    tuple[SparsePauliOp, np.ndarray, float]
        - SparsePauliOp: Ising cost operator for QAOA.
        - Q: QUBO matrix (N x N).
        - offset: Constant energy offset.
    """
    n_assets = len(expected_returns)
    Q = np.zeros((n_assets, n_assets))

    # Construct QUBO matrix: min x^T Q x
    # Objective: -returns + risk_factor * var + penalty * (sum x_i - budget)^2
    for i in range(n_assets):
        # Diagonal term: linear return + variance + budget penalty linear component
        Q[i, i] = -expected_returns[i] + risk_factor * cov_matrix[i, i] + penalty * (1.0 - 2.0 * budget)
        for j in range(i + 1, n_assets):
            # Off-diagonal term: covariance + budget penalty cross term
            q_ij = risk_factor * cov_matrix[i, j] + 2.0 * penalty
            Q[i, j] = q_ij
            Q[j, i] = q_ij

    # Map binary x_i in {0, 1} to spin s_i in {-1, +1} via x_i = (I - Z_i) / 2
    # x_i * x_j = (I - Z_i - Z_j + Z_i Z_j) / 4
    pauli_list = []
    offset = penalty * (budget ** 2)

    # Linear Pauli Z terms
    for i in range(n_assets):
        # Contribution from diagonal Q_ii: Q_ii * (I - Z_i)/2
        coeff_z = -Q[i, i] / 2.0
        offset += Q[i, i] / 2.0

        # Contribution from off-diagonals Q_ij: Q_ij * (I - Z_i - Z_j + Z_i Z_j)/4
        for j in range(n_assets):
            if i != j:
                coeff_z -= Q[i, j] / 4.0

        label = ['I'] * n_assets
        label[i] = 'Z'
        pauli_list.append((''.join(label), coeff_z))

    # Quadratic Pauli ZZ coupling terms (inter-asset correlation & penalty couplers)
    for i in range(n_assets):
        for j in range(i + 1, n_assets):
            coeff_zz = Q[i, j] / 2.0  # Q[i,j]/4 from (i,j) + Q[j,i]/4 from (j,i)
            offset += Q[i, j] / 2.0
            if abs(coeff_zz) > 1e-12:
                label_zz = ['I'] * n_assets
                label_zz[i] = 'Z'
                label_zz[j] = 'Z'
                pauli_list.append((''.join(label_zz), coeff_zz))

    cost_op = SparsePauliOp.from_list(pauli_list)
    logger.info(
        "Constructed Ising Hamiltonian for %d assets: %d Pauli terms (%d Z, %d ZZ couplers)",
        n_assets, len(pauli_list), n_assets, len(pauli_list) - n_assets
    )
    return cost_op, Q, offset


def build_portfolio_qaoa_circuit(
    expected_returns: np.ndarray,
    cov_matrix: np.ndarray,
    budget: int,
    risk_factor: float = 0.5,
    penalty: float = 4.0,
    reps: int = 1,
    gamma: float = 0.3927,  # pi / 8
    beta: float = 0.7854,   # pi / 4
) -> tuple[QuantumCircuit, SparsePauliOp, dict]:
    """
    Build a full QAOA quantum circuit for portfolio optimization.

    Parameters
    ----------
    expected_returns : np.ndarray
        Annualized expected returns for each asset.
    cov_matrix : np.ndarray
        Covariance matrix of returns.
    budget : int
        Number of assets to select.
    risk_factor : float
        Risk tolerance weight.
    penalty : float
        Constraint enforcement multiplier.
    reps : int
        Number of QAOA layers (p).
    gamma : float
        Variational parameter for problem cost Hamiltonian.
    beta : float
        Variational parameter for transverse mixer Hamiltonian.

    Returns
    -------
    tuple[QuantumCircuit, SparsePauliOp, dict]
        - bound_circuit: Ready-to-run QuantumCircuit with measurements.
        - cost_op: SparsePauliOp cost Hamiltonian.
        - meta: Circuit metadata (qubits, depth, gate counts).
    """
    n_assets = len(expected_returns)
    cost_op, Q, offset = build_portfolio_hamiltonian(
        expected_returns=expected_returns,
        cov_matrix=cov_matrix,
        budget=budget,
        risk_factor=risk_factor,
        penalty=penalty,
    )

    qaoa = QAOAAnsatz(cost_operator=cost_op, reps=reps)

    # Assign parameters
    param_dict = {}
    for p in qaoa.parameters:
        if "γ" in p.name or "gamma" in p.name.lower():
            param_dict[p] = gamma
        else:
            param_dict[p] = beta

    bound_circuit = qaoa.assign_parameters(param_dict)
    bound_circuit.measure_all()

    meta = {
        "num_qubits": n_assets,
        "reps": reps,
        "gamma": gamma,
        "beta": beta,
        "depth": bound_circuit.depth(),
        "ops": dict(bound_circuit.count_ops()),
        "num_terms": len(cost_op),
        "offset": offset,
    }
    return bound_circuit, cost_op, meta


# ═══════════════════════════════════════════════════════════════════════
# 2. VARIATIONAL QUANTUM CLASSIFIER (VQC) CIRCUIT BUILDER
# ═══════════════════════════════════════════════════════════════════════

def build_regime_vqc_circuit(
    num_qubits: int = 4,
    num_layers: int = 2,
) -> tuple[QuantumCircuit, ParameterVector, ParameterVector]:
    """
    Build a parameterized Variational Quantum Classifier (VQC) circuit for
    market regime detection.

    Architecture:
      - Feature map: Angle encoding via R_Y(x_i)
      - Variational layers: R_Y(theta) + R_Z(theta) + circular CNOT entanglement
      - Measurement: Pauli Z expectations on all qubits
    """
    qc = QuantumCircuit(num_qubits)
    x_params = ParameterVector('x', num_qubits)
    theta_params = ParameterVector('θ', num_layers * num_qubits * 2)

    # Feature encoding
    for i in range(num_qubits):
        qc.ry(x_params[i], i)

    # Variational layers
    idx = 0
    for _ in range(num_layers):
        for i in range(num_qubits):
            qc.ry(theta_params[idx], i)
            qc.rz(theta_params[idx + 1], i)
            idx += 2

        # Entanglement chain
        for i in range(num_qubits - 1):
            qc.cx(i, i + 1)
        if num_qubits > 2:
            qc.cx(num_qubits - 1, 0)

    qc.measure_all()
    return qc, x_params, theta_params


# ═══════════════════════════════════════════════════════════════════════
# 3. BELL BENCHMARK CALIBRATION CIRCUIT
# ═══════════════════════════════════════════════════════════════════════

def build_bell_benchmark_circuit() -> QuantumCircuit:
    """
    Build a 2-qubit maximally entangled Bell state (|00> + |11>) / sqrt(2)
    to benchmark physical QPU calibration and gate fidelity.
    """
    qc = QuantumCircuit(2, name="bell_benchmark")
    qc.h(0)
    qc.cx(0, 1)
    qc.measure_all()
    return qc


# ═══════════════════════════════════════════════════════════════════════
# 4. HARDWARE TRANSPILATION TO IBM 156-QUBIT HEAVY-HEX ARCHITECTURE
# ═══════════════════════════════════════════════════════════════════════

def transpile_for_ibm_hardware(
    circuit: QuantumCircuit,
    backend: Any,
    optimization_level: int = 1,
) -> tuple[QuantumCircuit, dict]:
    """
    Transpile a virtual quantum circuit onto the physical IBM Quantum architecture
    (e.g., ibm_fez with 156 qubits), converting to native ISA basis gates (rz, sx, x, cz).

    Parameters
    ----------
    circuit : QuantumCircuit
        Virtual quantum circuit with measurements.
    backend : Any
        IBM Quantum backend object (e.g. from QiskitRuntimeService).
    optimization_level : int
        Pass manager optimization level (0=none, 1=light, 2=heavy, 3=maximum).

    Returns
    -------
    tuple[QuantumCircuit, dict]
        - isa_circuit: Native Instruction Set Architecture circuit.
        - metrics: Transpilation metrics (depth, native op counts, physical qubits).
    """
    pm = generate_preset_pass_manager(backend=backend, optimization_level=optimization_level)
    isa_circuit = pm.run(circuit)

    metrics = {
        "isa_depth": isa_circuit.depth(),
        "isa_ops": dict(isa_circuit.count_ops()),
        "physical_qubits_allocated": isa_circuit.num_qubits,
        "backend_name": getattr(backend, "name", "unknown"),
        "optimization_level": optimization_level,
    }
    logger.info(
        "Transpiled circuit for %s: ISA Depth=%d, Ops=%s",
        metrics["backend_name"], metrics["isa_depth"], metrics["isa_ops"]
    )
    return isa_circuit, metrics


# ═══════════════════════════════════════════════════════════════════════
# 5. QPU MEASUREMENT DECODING & PORTFOLIO EVALUATION
# ═══════════════════════════════════════════════════════════════════════

def decode_qaoa_measurements(
    counts: dict[str, int],
    symbols: list[str],
    budget: int,
    expected_returns: np.ndarray,
    cov_matrix: np.ndarray,
    risk_factor: float = 0.5,
) -> dict:
    """
    Decode physical QPU measurement counts into candidate portfolio allocations.

    Evaluates:
      - Best feasible bitstring (satisfying cardinality constraint sum(x) == budget)
      - Objective energy value (return - risk_factor * variance)
      - Cardinality compliance rate across all shots
      - Optimal portfolio asset weights
    """
    n_assets = len(symbols)
    total_shots = sum(counts.values())

    scored_candidates = []
    budget_compliant_shots = 0

    for bitstring, count in counts.items():
        # Clean bitstring: remove spaces or prefixes if any
        clean_bits = bitstring.replace(" ", "")
        # Qiskit orders qubits from right to left (q_0 is rightmost)
        # We align: asset 0 -> bit 0
        bits = [int(b) for b in reversed(clean_bits)][:n_assets]
        selected_indices = [i for i, b in enumerate(bits) if b == 1]
        k = len(selected_indices)

        is_compliant = (k == budget)
        if is_compliant:
            budget_compliant_shots += count

        # Compute objective energy: x^T (-mu + lambda * Sigma) x
        x = np.array(bits, dtype=float)
        ret = float(np.dot(expected_returns, x))
        var = float(x @ cov_matrix @ x)
        energy = -ret + risk_factor * var

        scored_candidates.append({
            "bitstring": clean_bits,
            "bits": bits,
            "selected_assets": [symbols[i] for i in selected_indices],
            "count": count,
            "probability": count / total_shots if total_shots > 0 else 0.0,
            "num_selected": k,
            "is_budget_compliant": is_compliant,
            "expected_return": ret,
            "variance": var,
            "energy": energy,
        })

    # Sort candidates by:
    # 1. Budget compliance (True first)
    # 2. Energy (lowest first)
    # 3. Probability (highest first)
    compliant_candidates = [c for c in scored_candidates if c["is_budget_compliant"]]
    if compliant_candidates:
        best_candidate = min(compliant_candidates, key=lambda c: c["energy"])
    else:
        # Fallback to closest candidate or highest frequency
        best_candidate = max(scored_candidates, key=lambda c: c["count"])

    # Compute optimal portfolio weights for selected assets
    selected_idx = [i for i, b in enumerate(best_candidate["bits"]) if b == 1]
    if not selected_idx:
        selected_idx = list(range(min(budget, n_assets)))

    weights = np.zeros(n_assets)
    weights[selected_idx] = 1.0 / len(selected_idx)

    port_ret = float(np.dot(weights, expected_returns))
    port_vol = float(np.sqrt(weights @ cov_matrix @ weights))
    port_sharpe = float(port_ret / port_vol) if port_vol > 1e-6 else 0.0

    top_candidates = sorted(scored_candidates, key=lambda c: c["count"], reverse=True)[:5]

    return {
        "best_bitstring": best_candidate["bitstring"],
        "selected_assets": [symbols[i] for i in selected_idx],
        "optimal_weights": dict(zip(symbols, weights.tolist())),
        "expected_return": port_ret,
        "volatility": port_vol,
        "sharpe_ratio": port_sharpe,
        "total_shots": total_shots,
        "budget_compliance_rate": float(budget_compliant_shots / total_shots) if total_shots > 0 else 0.0,
        "top_candidates": top_candidates,
    }
