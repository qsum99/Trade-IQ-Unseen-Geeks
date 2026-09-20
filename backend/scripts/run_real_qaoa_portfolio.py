"""
Real 8-Asset Portfolio QAOA Execution on Physical 156-Qubit IBM Quantum QPU
==========================================================================
Encodes 8 real cryptocurrencies from CoinGecko:
  BTC, ETH, SOL, XRP, ADA, DOGE, AVAX, LINK
Math:
  Markowitz Portfolio Optimization -> QUBO -> Ising Hamiltonian (8 qubits, 28 couplers)
Hardware:
  Target: ibm_fez (156 physical qubits)
  Native Transpilation: RZ, SX, CZ basis gates across 156-qubit lattice
  Sampling: SamplerV2 on real physical hardware
"""

import os
import sys
import asyncio
import json
import logging
from datetime import datetime, timezone
import numpy as np

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import settings
from app.integrations.coingecko import coingecko_client
from app.core.database import save_quantum_job, get_quantum_job

from qiskit import QuantumCircuit
from qiskit.circuit.library import QAOAAnsatz
from qiskit.quantum_info import SparsePauliOp
from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("real_qaoa")


async def main():
    print("\n" + "="*75)
    print(" REAL 8-ASSET FINANCIAL QAOA PORTFOLIO OPTIMIZATION ON 156-QUBIT QPU")
    print("="*75)

    # 1. Fetch live market data for 8 crypto assets
    symbols = [
        "bitcoin", "ethereum", "solana", "ripple",
        "cardano", "dogecoin", "avalanche-2", "chainlink"
    ]
    tickers = ["BTC", "ETH", "SOL", "XRP", "ADA", "DOGE", "AVAX", "LINK"]
    n_assets = len(symbols)
    print(f"\n1. Fetching live market data for {n_assets} assets from CoinGecko...")

    prices_data = await coingecko_client.get_simple_price(symbols, ["usd"])

    # Extract expected returns and volatilities
    expected_returns = []
    vols = []
    print("\nAsset Universe:")
    for sym, ticker in zip(symbols, tickers):
        data = prices_data.get(sym, {})
        usd = data.get("usd", 1.0)
        ret_24h = data.get("usd_24h_change", 0.0) / 100.0
        # Annualized return and vol estimation
        ann_return = float(ret_24h * 365)
        ann_vol = float(abs(ret_24h) * (365**0.5) + 0.35)  # Baseline crypto vol
        expected_returns.append(ann_return)
        vols.append(ann_vol)
        print(f"  [{ticker}] {sym.capitalize():<12} | Price: ${usd:>10,.2f} | 24h: {ret_24h*100:>+6.2f}% | Ann Ret: {ann_return*100:>+6.1f}% | Vol: {ann_vol*100:.1f}%")

    expected_returns = np.array(expected_returns)
    vols = np.array(vols)

    # Build synthetic covariance matrix based on real crypto correlation patterns
    corr_matrix = np.array([
        [1.00, 0.82, 0.75, 0.68, 0.70, 0.62, 0.73, 0.77],  # BTC
        [0.82, 1.00, 0.84, 0.72, 0.76, 0.65, 0.81, 0.83],  # ETH
        [0.75, 0.84, 1.00, 0.65, 0.71, 0.61, 0.85, 0.79],  # SOL
        [0.68, 0.72, 0.65, 1.00, 0.74, 0.58, 0.67, 0.70],  # XRP
        [0.70, 0.76, 0.71, 0.74, 1.00, 0.60, 0.75, 0.73],  # ADA
        [0.62, 0.65, 0.61, 0.58, 0.60, 1.00, 0.64, 0.62],  # DOGE
        [0.73, 0.81, 0.85, 0.67, 0.75, 0.64, 1.00, 0.80],  # AVAX
        [0.77, 0.83, 0.79, 0.70, 0.73, 0.62, 0.80, 1.00],  # LINK
    ])
    cov_matrix = np.outer(vols, vols) * corr_matrix

    # 2. Formulate QUBO and Ising Hamiltonian
    # Goal: Pick best budget K=4 assets out of 8 (256 combinations)
    budget = 4
    risk_factor = 0.5
    penalty = 4.0

    print(f"\n2. Formulating Portfolio QUBO (Budget: select {budget} out of {n_assets} assets, Risk Factor: {risk_factor})...")
    Q = np.zeros((n_assets, n_assets))
    for i in range(n_assets):
        Q[i, i] = -expected_returns[i] + risk_factor * cov_matrix[i, i] + penalty * (1 - 2 * budget)
        for j in range(i + 1, n_assets):
            Q[i, j] = risk_factor * cov_matrix[i, j] + 2 * penalty
            Q[j, i] = Q[i, j]

    # Convert to Ising Hamiltonian: H = sum_i h_i Z_i + sum_ij J_ij Z_i Z_j
    pauli_list = []
    for i in range(n_assets):
        # Single-qubit Z term
        coeff_z = Q[i, i] / 2.0
        label = ['I'] * n_assets
        label[i] = 'Z'
        pauli_list.append((''.join(label), coeff_z))

        for j in range(i + 1, n_assets):
            # Two-qubit ZZ coupling term (inter-asset covariance)
            coeff_zz = Q[i, j] / 4.0
            if abs(coeff_zz) > 1e-6:
                label_zz = ['I'] * n_assets
                label_zz[i] = 'Z'
                label_zz[j] = 'Z'
                pauli_list.append((''.join(label_zz), coeff_zz))

    cost_op = SparsePauliOp.from_list(pauli_list)
    print(f"Ising Cost Hamiltonian constructed with {len(pauli_list)} Pauli terms ({n_assets} single-qubit + {len(pauli_list) - n_assets} two-qubit covariance couplers)!")

    # 3. Build QAOA Circuit
    print("\n3. Building QAOA Circuit (reps=1, 8 qubits)...")
    qaoa = QAOAAnsatz(cost_operator=cost_op, reps=1)

    # Bind variational parameters (gamma for problem Hamiltonian, beta for mixer)
    gamma = 0.3927  # pi / 8
    beta = 0.7854   # pi / 4
    param_dict = {}
    for p in qaoa.parameters:
        if "γ" in p.name or "gamma" in p.name.lower():
            param_dict[p] = gamma
        else:
            param_dict[p] = beta

    bound_circuit = qaoa.assign_parameters(param_dict)
    bound_circuit.measure_all()
    print(f"Abstract QAOA Circuit: 8 qubits, depth={bound_circuit.depth()}, ops={dict(bound_circuit.count_ops())}")

    # 4. Connect to IBM Quantum Platform and target 156-qubit QPU
    print(f"\n4. Connecting to IBM Quantum Platform ({settings.IBM_QUANTUM_CHANNEL})...")
    service = QiskitRuntimeService(channel=settings.IBM_QUANTUM_CHANNEL, token=settings.IBM_QUANTUM_TOKEN)
    real_backend = service.backend("ibm_fez")
    qpu_qubits = real_backend.configuration().n_qubits
    print(f"Target QPU: {real_backend.name} ({qpu_qubits} physical superconducting qubits, status: {real_backend.status().status_msg})")

    # 5. Transpile onto 156-qubit physical architecture
    print(f"\n5. Transpiling 8-qubit QAOA circuit onto {real_backend.name}'s 156-qubit heavy-hex lattice...")
    pm = generate_preset_pass_manager(backend=real_backend, optimization_level=1)
    isa_circuit = pm.run(bound_circuit)
    ops_count = dict(isa_circuit.count_ops())
    print(f"Transpilation COMPLETE!")
    print(f"  - Physical Layout: Mapped across 156-qubit lattice")
    print(f"  - ISA Circuit Depth: {isa_circuit.depth()}")
    print(f"  - Physical Native Gates: {ops_count}")

    # 6. Submit to real 156-qubit physical QPU
    print(f"\n6. Submitting 8-qubit Portfolio QAOA to real physical hardware ({real_backend.name})...")
    sampler = SamplerV2(mode=real_backend)
    job = sampler.run([isa_circuit], shots=256)
    job_id = job.job_id()

    print("\n" + "="*75)
    print(" REAL QUANTUM HARDWARE SUBMISSION SUCCESSFUL!")
    print("="*75)
    print(f"  Job ID:           {job_id}")
    print(f"  Target QPU:       {real_backend.name} (156 qubits)")
    print(f"  Algorithm:        QAOA Portfolio Optimization (8 Crypto Assets)")
    print(f"  Coupling Terms:   28 Inter-Asset Covariance Gates")
    print(f"  Physical Shots:   256 shots")
    print(f"  Initial Status:   {job.status()}")
    print("="*75)

    # 7. Persist to PostgreSQL database
    job_record = {
        "job_id": job_id,
        "experiment_type": "qaoa_portfolio_8assets",
        "qpu_backend": real_backend.name,
        "num_qubits": 8,
        "shots": 256,
        "status": str(job.status()).upper(),
        "circuit_depth": isa_circuit.depth(),
        "error_report": {
            "assets": tickers,
            "budget": budget,
            "risk_factor": risk_factor,
            "isa_ops": ops_count,
        }
    }
    save_quantum_job(job_record)
    print(f"Job {job_id} successfully persisted in Supabase PostgreSQL!")
    return job_id


if __name__ == "__main__":
    asyncio.run(main())
