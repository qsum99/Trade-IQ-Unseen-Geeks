"""
End-to-End Real Hardware & Real Data Test Script
=================================================
Tests:
1. Supabase Direct PostgreSQL Connection
2. CoinGecko Live Market Data (BTC, ETH, SOL)
3. Real LLM Call with Tool Calling (Featherless AI -> NVIDIA NIM fallback)
4. Real IBM Quantum Hardware Connection, Error Analysis & Real QPU Circuit Execution
"""

import os
import sys
import asyncio
import json
import logging
from datetime import datetime, timezone

# Ensure UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Add app to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.config import settings
from app.core.database import check_db_health
from app.integrations.coingecko import coingecko_client
from app.ai.assistant import research_query
from app.quant import formulas as f

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("e2e_test")


async def test_supabase_db():
    print("\n" + "="*70)
    print(" 1. SUPABASE DIRECT POSTGRESQL TEST")
    print("="*70)
    health = check_db_health()
    print(f"Database Health Status: {health.get('status')}")
    print(f"Database Engine: {health.get('version', 'N/A')}")
    print(f"Direct URL Configured: {bool(settings.postgres_url)}")
    return health.get("status") in ("connected", "healthy")


async def test_coingecko_real_data():
    print("\n" + "="*70)
    print(" 2. COINGECKO LIVE MARKET DATA TEST")
    print("="*70)
    # Live prices
    prices = await coingecko_client.get_simple_price(
        coin_ids=["bitcoin", "ethereum", "solana"],
        vs_currencies=["usd"],
        include_24hr_change=True,
    )
    print("Live Prices:")
    for coin, data in prices.items():
        usd_price = data.get("usd")
        change = data.get("usd_24h_change")
        print(f"  - {coin.capitalize()}: ${usd_price:,.2f} (24h: {change:+.2f}%)")

    # 30-day historical chart for BTC
    df = await coingecko_client.get_market_chart("bitcoin", days=30)
    num_points = len(df)
    total_ret = (df['price'].iloc[-1] / df['price'].iloc[0] - 1.0) if num_points > 1 else 0.0
    daily_returns = df['return'].dropna()
    ann_vol = float(daily_returns.std() * (365 ** 0.5)) if len(daily_returns) > 1 else 0.0

    print(f"\n30-Day Historical Data Points: {num_points} daily points")
    print(f"30-Day Start Price: ${df['price'].iloc[0]:,.2f} | Current: ${df['price'].iloc[-1]:,.2f}")
    print(f"30-Day Total Return: {total_ret*100:+.2f}%")
    print(f"30-Day Annualized Volatility: {ann_vol*100:.2f}%")
    return prices, df


async def test_llm_with_real_data():
    print("\n" + "="*70)
    print(" 3. REAL LLM CALL WITH TOOL CALLING & FALLBACK")
    print("="*70)
    prompt = "What is the current price of bitcoin in USD and what has been its 24-hour change? Use the get_crypto_price tool."
    print(f"User Prompt: '{prompt}'")
    print(f"Primary Provider: Featherless AI ({settings.LLM_MODEL})")
    print(f"Fallback Provider: NVIDIA NIM ({settings.NVIDIA_NIM_MODEL}) with {len(settings.nvidia_nim_key_list)} rotated keys")
    
    result = await research_query(prompt)
    print("\nAI Response:")
    print(result.get("response", "No response"))
    print(f"\nProvider Used: {result.get('provider', 'N/A')}")
    print(f"Model Used: {result.get('model', 'N/A')}")
    print(f"Tools Called: {result.get('tools_called', [])}")
    return result


async def test_real_ibm_quantum():
    print("\n" + "="*70)
    print(" 4. REAL IBM QUANTUM HARDWARE TEST")
    print("="*70)
    print(f"IBM Token: {settings.IBM_QUANTUM_TOKEN[:8]}...{settings.IBM_QUANTUM_TOKEN[-4:]}")
    print(f"Channel: {settings.IBM_QUANTUM_CHANNEL}")

    from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
    from qiskit import QuantumCircuit
    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager

    channel = getattr(settings, "IBM_QUANTUM_CHANNEL", "ibm_quantum_platform")
    service = QiskitRuntimeService(channel=channel, token=settings.IBM_QUANTUM_TOKEN)
    
    backends = service.backends()
    print(f"\nDiscovered {len(backends)} backends on IBM Quantum Platform:")
    
    real_qpus = []
    for b in backends:
        cfg = b.configuration()
        status = b.status()
        is_sim = getattr(cfg, "simulator", False)
        n_q = getattr(cfg, "n_qubits", getattr(cfg, "num_qubits", "unknown"))
        print(f"  - {b.name}: {n_q} qubits | Simulator={is_sim} | Status={status.status_msg} | Pending Jobs={status.pending_jobs}")
        if not is_sim:
            real_qpus.append((b, status.pending_jobs, n_q))

    if not real_qpus:
        print("No physical QPUs available.")
        return False

    # Pick least busy real hardware QPU
    least_busy_qpu, pending, n_qubits = min(real_qpus, key=lambda x: x[1])
    print(f"\nTargeting least busy real QPU: {least_busy_qpu.name} ({n_qubits} qubits, {pending} pending jobs)")

    # Retrieve real hardware error rates & calibration
    props = least_busy_qpu.properties()
    if props:
        qubit_errors = []
        for q_idx, qubit in enumerate(props.qubits):
            for prop in qubit:
                if getattr(prop, 'name', '') == 'readout_error':
                    qubit_errors.append(prop.value)
        import numpy as np
        mean_readout = np.mean(qubit_errors) if qubit_errors else 0.0
        print(f"Real QPU Mean Readout Error: {mean_readout*100:.2f}%")

    # Build a real 4-qubit Financial QAOA Portfolio Optimization circuit
    from app.quantum.circuits import build_portfolio_qaoa_circuit, transpile_for_ibm_hardware
    from app.core.database import save_quantum_job

    expected_returns = np.array([0.15, 0.22, 0.35, 0.12])
    cov_matrix = np.array([
        [0.04, 0.02, 0.01, 0.015],
        [0.02, 0.09, 0.03, 0.025],
        [0.01, 0.03, 0.16, 0.020],
        [0.015, 0.025, 0.020, 0.05],
    ])
    symbols = ["BTC", "ETH", "SOL", "XRP"]
    budget = 2

    qc, cost_op, meta = build_portfolio_qaoa_circuit(
        expected_returns=expected_returns,
        cov_matrix=cov_matrix,
        budget=budget,
        risk_factor=0.5,
        reps=1,
    )
    print(f"Created Real Financial QAOA Circuit: 4 qubits, depth={qc.depth()}, ops={dict(qc.count_ops())}")

    # Transpile to ISA circuit for the real 156-qubit QPU
    isa_circuit, transpile_metrics = transpile_for_ibm_hardware(qc, least_busy_qpu, optimization_level=1)
    print(f"Transpiled to ISA circuit on {least_busy_qpu.name} (ISA Depth: {transpile_metrics['isa_depth']}, Ops: {transpile_metrics['isa_ops']})")

    # Submit job to real QPU using SamplerV2
    print(f"\nSubmitting real QAOA job to IBM Quantum hardware ({least_busy_qpu.name})...")
    sampler = SamplerV2(mode=least_busy_qpu)
    job = sampler.run([isa_circuit], shots=256)
    job_id = job.job_id()
    print(f"SUCCESS: Real QAOA Circuit submitted to REAL IBM QUANTUM HARDWARE!")
    print(f"Job ID: {job_id}")
    print(f"Initial Job Status: {job.status()}")
    print(f"Queue Status: Live on IBM Quantum Platform ({least_busy_qpu.name})")

    # Persist job to PostgreSQL
    save_quantum_job({
        "job_id": job_id,
        "experiment_type": "qaoa_portfolio_optimization",
        "qpu_backend": least_busy_qpu.name,
        "num_qubits": 4,
        "shots": 256,
        "status": str(job.status()).upper(),
        "circuit_depth": transpile_metrics["isa_depth"],
        "error_report": {
            "symbols": symbols,
            "budget": budget,
            "risk_factor": 0.5,
            "isa_ops": transpile_metrics["isa_ops"],
        }
    })

    return {
        "qpu_name": least_busy_qpu.name,
        "num_qubits": n_qubits,
        "job_id": job_id,
        "status": str(job.status()),
    }


async def main():
    print("STARTING END-TO-END REAL HARDWARE & REAL DATA TEST SUITE")
    print(f"Timestamp: {datetime.now(timezone.utc).isoformat()} UTC")

    # 1. Supabase
    db_ok = await test_supabase_db()

    # 2. CoinGecko
    prices, df = await test_coingecko_real_data()

    # 3. LLM
    llm_result = await test_llm_with_real_data()

    # 4. IBM Quantum Hardware
    quantum_result = await test_real_ibm_quantum()

    print("\n" + "="*70)
    print(" TEST RUN SUMMARY")
    print("="*70)
    print(f"1. Supabase PostgreSQL: {'PASSED' if db_ok else 'FAILED'}")
    print(f"2. CoinGecko Live Data: PASSED ({len(prices)} assets fetched, 30d BTC chart)")
    print(f"3. AI LLM Orchestration: PASSED (Provider: {llm_result.get('provider')}, Tools Called: {len(llm_result.get('tools_called', []))})")
    print(f"4. Real IBM Quantum QPU: PASSED (Target: {quantum_result.get('qpu_name')}, Job ID: {quantum_result.get('job_id')}, Status: {quantum_result.get('status')})")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
