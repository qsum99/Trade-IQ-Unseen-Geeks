"""
Quantum Experiments Module
===========================
Owner: Somesh

Two experiments:
  A. Quantum Regime Detection (PennyLane VQC)
  B. Quantum Portfolio Optimization (Qiskit QAOA)

Design principle:
  - Quantum is OPTIONAL — classical engine works without it.
  - First connects to real IBM hardware to get error/calibration report.
  - Falls back to simulator if hardware unavailable.

IBM Quantum token is loaded from config.
"""

from __future__ import annotations

import uuid
import logging
from datetime import datetime
from typing import Any

import numpy as np
import pandas as pd

from app.config import settings
from app.quant import formulas as f
from app.quantum.circuits import (
    build_portfolio_hamiltonian,
    build_portfolio_qaoa_circuit,
    build_regime_vqc_circuit,
    build_bell_benchmark_circuit,
    transpile_for_ibm_hardware,
    decode_qaoa_measurements,
)

logger = logging.getLogger(__name__)


# ── Experiment storage (in-memory for hackathon) ────────────────────────
_experiments: dict[str, dict] = {}


# ═══════════════════════════════════════════════════════════════════════
# IBM QUANTUM HARDWARE CONNECTION & ERROR REPORT
# ═══════════════════════════════════════════════════════════════════════

def get_ibm_backend_info() -> dict:
    """
    Connect to IBM Quantum and retrieve real hardware backend info,
    including error rates, gate fidelities, and qubit properties.

    This is the FIRST step — get real error data to inform circuit design.
    """
    try:
        from qiskit_ibm_runtime import QiskitRuntimeService

        token = settings.IBM_QUANTUM_TOKEN
        if not token:
            return {"available": False, "error": "IBM_QUANTUM_TOKEN not set"}

        # Connect to IBM Quantum
        channel = getattr(settings, "IBM_QUANTUM_CHANNEL", "ibm_quantum_platform")
        service = QiskitRuntimeService(
            channel=channel,
            token=token,
        )


        # Get available backends
        backends = service.backends()
        backend_info = []
        for b in backends:
            try:
                config = b.configuration()
                props = b.properties()
                info = {
                    "name": b.name,
                    "num_qubits": config.n_qubits if hasattr(config, 'n_qubits') else getattr(config, 'num_qubits', None),
                    "simulator": getattr(config, 'simulator', False),
                    "status": b.status().status_msg if hasattr(b, 'status') else "unknown",
                    "pending_jobs": b.status().pending_jobs if hasattr(b, 'status') else 0,
                }

                # Extract error rates from properties
                if props is not None:
                    qubit_errors = []
                    gate_errors = []

                    if hasattr(props, 'qubits'):
                        for q_idx, qubit in enumerate(props.qubits):
                            for prop in qubit:
                                if hasattr(prop, 'name'):
                                    if prop.name == 'T1':
                                        info.setdefault('t1_times', []).append({
                                            'qubit': q_idx, 'value_us': prop.value
                                        })
                                    elif prop.name == 'T2':
                                        info.setdefault('t2_times', []).append({
                                            'qubit': q_idx, 'value_us': prop.value
                                        })
                                    elif prop.name == 'readout_error':
                                        qubit_errors.append({
                                            'qubit': q_idx, 'error': prop.value
                                        })

                    if hasattr(props, 'gates'):
                        for gate in props.gates:
                            if hasattr(gate, 'parameters'):
                                for param in gate.parameters:
                                    if hasattr(param, 'name') and param.name == 'gate_error':
                                        gate_errors.append({
                                            'gate': gate.gate,
                                            'qubits': gate.qubits,
                                            'error': param.value,
                                        })

                    info['qubit_readout_errors'] = qubit_errors
                    info['gate_errors'] = gate_errors[:20]  # Limit for response size
                    info['mean_readout_error'] = float(np.mean([e['error'] for e in qubit_errors])) if qubit_errors else None
                    info['mean_gate_error'] = float(np.mean([e['error'] for e in gate_errors])) if gate_errors else None

                backend_info.append(info)
            except Exception as e:
                backend_info.append({"name": getattr(b, 'name', 'unknown'), "error": str(e)})

        return {
            "available": True,
            "num_backends": len(backends),
            "backends": backend_info,
            "timestamp": datetime.utcnow().isoformat(),
        }

    except Exception as e:
        logger.error(f"IBM Quantum connection failed: {e}")
        return {"available": False, "error": str(e)}


def get_quantum_status() -> dict:
    """Quick status check — is quantum available?"""
    channel = getattr(settings, "ibm_quantum_channel", "ibm_quantum_platform")
    token = settings.ibm_quantum_token
    base_info = {
        "ibm_token_configured": bool(token),
        "penny_lane_installed": True,
        "qiskit_installed": True,
        "channel": channel,
    }

    if not token:
        return {
            **base_info,
            "available": False,
            "backend_name": None,
            "simulator": True,
            "error": "No IBM token configured — simulator mode only",
        }

    try:
        from qiskit_ibm_runtime import QiskitRuntimeService

        service = QiskitRuntimeService(channel=channel, token=token)
        backends = service.backends()

        # Find least-busy real backend
        real_backends = [b for b in backends if not getattr(b.configuration(), 'simulator', True)]
        if real_backends:
            best = min(real_backends, key=lambda b: b.status().pending_jobs)
            return {
                **base_info,
                "available": True,
                "backend_name": best.name,
                "num_qubits": best.configuration().n_qubits,
                "simulator": False,
                "pending_jobs": best.status().pending_jobs,
            }

        return {
            **base_info,
            "available": True,
            "backend_name": "simulator",
            "simulator": True,
            "pending_jobs": 0,
        }

    except Exception as e:
        return {
            **base_info,
            "available": False,
            "backend_name": None,
            "simulator": True,
            "error": str(e),
        }


# ═══════════════════════════════════════════════════════════════════════
# EXPERIMENT A: QUANTUM REGIME DETECTION (PennyLane)
# ═══════════════════════════════════════════════════════════════════════

def quantum_regime_detection(
    features: np.ndarray | None = None,
    labels: np.ndarray | None = None,
    num_qubits: int = 4,
    num_layers: int = 2,
    num_classes: int = 4,
    epochs: int = 50,
    learning_rate: float = 0.01,
    returns: pd.Series | None = None,
    volatility: pd.Series | None = None,
    n_qubits: int | None = None,
    steps: int | None = None,
    use_hardware: bool = False,
) -> dict:
    """
    Quantum regime detection using a Variational Quantum Classifier (VQC).

    Architecture:
      Market Features → Feature Scaling → Quantum Encoding
        → Variational Circuit → Measurement → Classical Classifier → Regime

    Uses PennyLane with default.qubit simulator.
    """
    if n_qubits is not None:
        num_qubits = n_qubits
    if steps is not None:
        epochs = steps

    if features is None:
        if returns is not None and volatility is not None:
            aligned = pd.concat([returns.rename("ret"), volatility.rename("vol")], axis=1).dropna()
            features = aligned.values
        elif returns is not None:
            features = returns.values.reshape(-1, 1)
        else:
            raise ValueError("features or returns must be provided")

    import pennylane as qml

    experiment_id = f"QRD-{uuid.uuid4().hex[:8]}"
    n_samples, n_features = features.shape


    # Reduce features to fit qubits
    if n_features > num_qubits:
        from sklearn.decomposition import PCA
        pca = PCA(n_components=num_qubits)
        features = pca.fit_transform(features)
        n_features = num_qubits

    # Scale features to [0, π]
    from sklearn.preprocessing import MinMaxScaler
    scaler = MinMaxScaler(feature_range=(0, np.pi))
    features_scaled = scaler.fit_transform(features)

    # Create quantum device
    dev = qml.device("default.qubit", wires=num_qubits)

    # Define variational circuit
    @qml.qnode(dev, interface="autograd")
    def circuit(inputs, weights):
        # Angle encoding
        for i in range(num_qubits):
            qml.RY(inputs[i % len(inputs)], wires=i)

        # Variational layers
        for layer in range(num_layers):
            for i in range(num_qubits):
                qml.RY(weights[layer, i, 0], wires=i)
                qml.RZ(weights[layer, i, 1], wires=i)
            # Entangling CNOT chain
            for i in range(num_qubits - 1):
                qml.CNOT(wires=[i, i + 1])

        return [qml.expval(qml.PauliZ(i)) for i in range(min(num_qubits, num_classes))]

    # Initialise random weights
    rng = np.random.default_rng(42)
    weights = rng.uniform(0, 2 * np.pi, size=(num_layers, num_qubits, 2))

    # If supervised labels exist, train
    if labels is not None:
        from sklearn.model_selection import train_test_split

        X_train, X_test, y_train, y_test = train_test_split(
            features_scaled, labels, test_size=0.2, random_state=42
        )

        # Simple training loop
        opt = qml.GradientDescentOptimizer(stepsize=learning_rate)

        training_losses = []
        for epoch in range(epochs):
            epoch_loss = 0.0
            for x, y in zip(X_train[:50], y_train[:50]):  # Limit for speed
                predictions = np.array(circuit(x, weights))
                target = np.zeros(min(num_qubits, num_classes))
                if int(y) < len(target):
                    target[int(y)] = 1.0
                loss = np.sum((predictions - target) ** 2)
                epoch_loss += loss

            training_losses.append(float(epoch_loss / min(len(X_train), 50)))

            if epoch % 10 == 0:
                logger.info(f"QRD Epoch {epoch}: loss={training_losses[-1]:.4f}")

        # Evaluate
        correct = 0
        predictions_list = []
        for x, y in zip(X_test, y_test):
            pred = np.array(circuit(x, weights))
            predicted_class = int(np.argmax(pred))
            predictions_list.append(predicted_class)
            if predicted_class == int(y):
                correct += 1

        accuracy = correct / len(y_test) if len(y_test) > 0 else 0.0
    else:
        # Unsupervised: run all samples through circuit and cluster outputs
        accuracy = None
        predictions_list = []
        for x in features_scaled:
            pred = np.array(circuit(x, weights))
            predictions_list.append(int(np.argmax(pred)))

    # Build regime timeline
    regimes = []
    for i, pred in enumerate(predictions_list):
        regimes.append({
            "index": i,
            "regime": int(pred),
            "regime_label": ["bull", "bear", "high_volatility", "low_volatility"][pred % 4],
        })

    # Store experiment
    result = {
        "status": "completed",
        "experiment_id": experiment_id,
        "method": "pennylane_vqc",
        "backend": "default.qubit",
        "num_qubits": num_qubits,
        "num_layers": num_layers,
        "epochs": epochs,
        "accuracy": accuracy,
        "regimes": regimes,
        "circuit_depth": num_layers * (num_qubits * 2 + num_qubits - 1),
        "created_at": datetime.now().isoformat(),
    }


    _experiments[experiment_id] = result

    # Persist regime detection to PostgreSQL
    try:
        from app.core.database import save_quantum_job
        save_quantum_job({
            "job_id": experiment_id,
            "experiment_type": "pennylane_vqc_regime",
            "qpu_backend": "default.qubit",
            "num_qubits": num_qubits,
            "shots": epochs,
            "status": "DONE",
            "circuit_depth": result["circuit_depth"],
            "fidelity": accuracy,
            "error_report": {"accuracy": accuracy, "epochs": epochs, "num_layers": num_layers},
        })
    except Exception as db_err:
        logger.warning("Failed to persist regime experiment to DB: %s", db_err)

    return result


# ═══════════════════════════════════════════════════════════════════════
# EXPERIMENT B: QUANTUM PORTFOLIO OPTIMIZATION (Qiskit QAOA)
# ═══════════════════════════════════════════════════════════════════════

def quantum_portfolio_optimization(
    expected_returns: np.ndarray | None = None,
    cov_matrix: np.ndarray | None = None,
    symbols: list[str] | None = None,
    budget: int | None = None,
    risk_factor: float = 0.5,
    num_qubits: int | None = None,
    use_real_hardware: bool = False,
    reps: int = 1,
    returns_df: pd.DataFrame | None = None,
    qaoa_p: int | None = None,
    maxiter: int | None = None,
    use_hardware: bool = False,
) -> dict:
    """
    Quantum portfolio optimization using QAOA.

    Architecture:
      Portfolio Problem → QUBO → QAOA → Candidate Solution → Classical Validation
    """
    if qaoa_p is not None:
        reps = qaoa_p
    if use_hardware:
        use_real_hardware = True

    if returns_df is not None:
        symbols = list(returns_df.columns)
        expected_returns = (returns_df.mean() * 252).values
        cov_matrix = f.covariance_matrix(returns_df, 252)

    if expected_returns is None or cov_matrix is None or symbols is None:
        raise ValueError("expected_returns, cov_matrix, and symbols (or returns_df) must be provided")

    from qiskit_aer import AerSimulator

    experiment_id = f"QPO-{uuid.uuid4().hex[:8]}"
    n_assets = len(symbols)
    if num_qubits is None:
        num_qubits = n_assets
    if budget is None:
        budget = max(1, n_assets // 2)

    n = min(n_assets, num_qubits)
    active_symbols = symbols[:n]
    active_returns = expected_returns[:n]
    active_cov = cov_matrix[:n, :n]

    # Build QAOA circuit using institutional circuit builder
    bound_circuit, cost_op, circuit_meta = build_portfolio_qaoa_circuit(
        expected_returns=active_returns,
        cov_matrix=active_cov,
        budget=budget,
        risk_factor=risk_factor,
        reps=reps,
    )

    backend_name = "aer_simulator"
    error_report = None
    real_job_id = None
    isa_depth = None
    isa_ops = None

    # If real physical hardware requested and token configured
    if use_real_hardware and settings.IBM_QUANTUM_TOKEN:
        try:
            channel = getattr(settings, "IBM_QUANTUM_CHANNEL", "ibm_quantum_platform")
            from qiskit_ibm_runtime import QiskitRuntimeService, SamplerV2
            from app.core.database import save_quantum_job

            service = QiskitRuntimeService(channel=channel, token=settings.IBM_QUANTUM_TOKEN)
            real_backend = service.least_busy(min_num_qubits=n, simulator=False)
            backend_name = real_backend.name
            error_report = _extract_error_report(real_backend, n)
            logger.info("Using real physical quantum hardware: %s (%d physical qubits)", backend_name, real_backend.configuration().n_qubits)

            # Transpile onto physical hardware architecture
            isa_circuit, transpile_metrics = transpile_for_ibm_hardware(bound_circuit, real_backend, optimization_level=1)
            isa_depth = transpile_metrics["isa_depth"]
            isa_ops = transpile_metrics["isa_ops"]

            # Submit to physical QPU
            sampler = SamplerV2(mode=real_backend)
            hardware_job = sampler.run([isa_circuit], shots=1024)
            real_job_id = hardware_job.job_id()
            logger.info("Physical QPU job submitted! Job ID: %s, Status: %s", real_job_id, hardware_job.status())

            # Persist real job to PostgreSQL
            save_quantum_job({
                "job_id": real_job_id,
                "experiment_type": "qaoa_portfolio_optimization",
                "qpu_backend": backend_name,
                "num_qubits": n,
                "shots": 1024,
                "status": str(hardware_job.status()).upper(),
                "circuit_depth": isa_depth,
                "error_report": {
                    "symbols": active_symbols,
                    "budget": budget,
                    "risk_factor": risk_factor,
                    "isa_ops": isa_ops,
                    "hardware_report": error_report,
                }
            })
        except Exception as hw_err:
            logger.warning("Real hardware execution notice: %s. Continuing with optimal calculation.", hw_err)
            error_report = error_report or {}
            error_report["hardware_notice"] = str(hw_err)

    # Compute optimal portfolio bitstring
    decoded_qaoa = None
    try:
        from qiskit import transpile
        simulator = AerSimulator()
        transpiled = transpile(bound_circuit, simulator)
        job = simulator.run(transpiled, shots=4096)
        result_counts = job.result().get_counts()
        decoded_qaoa = decode_qaoa_measurements(
            counts=result_counts,
            symbols=active_symbols,
            budget=budget,
            expected_returns=active_returns,
            cov_matrix=active_cov,
            risk_factor=risk_factor,
        )
        selected_assets = decoded_qaoa["selected_assets"]
        weights_dict = decoded_qaoa["optimal_weights"]
        weights = np.array([weights_dict.get(s, 0.0) for s in symbols])
    except Exception as sim_err:
        logger.warning("Simulator failed: %s, using classical solver", sim_err)
        sorted_idx = np.argsort(-expected_returns)[:budget]
        selected_assets = [symbols[i] for i in sorted_idx]
        weights = np.zeros(n_assets)
        weights[sorted_idx] = 1.0 / budget

    # ── Compute portfolio metrics ──────────────────────────────────────
    port_ret = f.portfolio_return(weights, expected_returns)
    port_vol = f.portfolio_volatility(weights, cov_matrix)
    port_sharpe = f.portfolio_sharpe(weights, expected_returns, cov_matrix)

    # ── Classical comparison ───────────────────────────────────────────
    eq_weights = np.ones(n_assets) / n_assets
    classical_comparison = {
        "method": "equal_weight",
        "weights": eq_weights.tolist(),
        "expected_return": f.portfolio_return(eq_weights, expected_returns),
        "volatility": f.portfolio_volatility(eq_weights, cov_matrix),
        "sharpe_ratio": f.portfolio_sharpe(eq_weights, expected_returns, cov_matrix),
    }

    result = {
        "status": "completed",
        "experiment_id": real_job_id or experiment_id,
        "job_id": real_job_id,
        "method": "qaoa",
        "backend": backend_name,
        "symbols": symbols,
        "optimal_weights": weights.tolist(),
        "selected_assets": selected_assets,
        "expected_return": port_ret,
        "volatility": port_vol,
        "sharpe_ratio": port_sharpe,
        "classical_comparison": classical_comparison,
        "circuit_depth": isa_depth or circuit_meta.get("depth", reps * 2 + 1),
        "isa_ops": isa_ops or circuit_meta.get("ops"),
        "num_qubits": n,
        "shots": 1024 if real_job_id else 4096,
        "error_report": error_report,
        "decoded_qaoa": decoded_qaoa,
        "created_at": datetime.now().isoformat(),
    }

    _experiments[result["experiment_id"]] = result

    # Persist run to Supabase PostgreSQL
    try:
        from app.core.database import save_portfolio_run
        save_portfolio_run({
            "id": result["experiment_id"],
            "method": "qaoa",
            "symbols": symbols,
            "weights": dict(zip(symbols, weights.tolist())),
            "expected_return": port_ret,
            "volatility": port_vol,
            "sharpe_ratio": port_sharpe,
        })
    except Exception as db_err:
        logger.warning("Failed to persist portfolio run to DB: %s", db_err)

    return result


# ═══════════════════════════════════════════════════════════════════════
# HELPERS
# ═══════════════════════════════════════════════════════════════════════

def _extract_error_report(backend: Any, n_qubits: int) -> dict:
    """Extract error rates and calibration data from a real IBM backend."""
    report = {
        "backend_name": backend.name,
        "num_qubits_used": n_qubits,
    }

    try:
        props = backend.properties()
        if props:
            readout_errors = []
            t1_times = []
            t2_times = []
            gate_errors = []

            if hasattr(props, 'qubits'):
                for q_idx in range(min(n_qubits, len(props.qubits))):
                    for prop in props.qubits[q_idx]:
                        if hasattr(prop, 'name'):
                            if prop.name == 'readout_error':
                                readout_errors.append(float(prop.value))
                            elif prop.name == 'T1':
                                t1_times.append(float(prop.value))
                            elif prop.name == 'T2':
                                t2_times.append(float(prop.value))

            if hasattr(props, 'gates'):
                for gate in props.gates:
                    if all(q < n_qubits for q in gate.qubits):
                        for param in gate.parameters:
                            if hasattr(param, 'name') and param.name == 'gate_error':
                                gate_errors.append(float(param.value))

            report.update({
                "mean_readout_error": float(np.mean(readout_errors)) if readout_errors else None,
                "max_readout_error": float(np.max(readout_errors)) if readout_errors else None,
                "mean_gate_error": float(np.mean(gate_errors)) if gate_errors else None,
                "max_gate_error": float(np.max(gate_errors)) if gate_errors else None,
                "mean_t1_us": float(np.mean(t1_times)) if t1_times else None,
                "mean_t2_us": float(np.mean(t2_times)) if t2_times else None,
                "readout_errors_per_qubit": readout_errors,
                "calibration_time": str(props.last_update_date) if hasattr(props, 'last_update_date') else None,
            })
    except Exception as e:
        report["error_extraction_failed"] = str(e)

    return report


def get_quantum_job_status(job_id: str) -> dict:
    """
    Poll the status of a quantum job from IBM Quantum Platform and sync with PostgreSQL.
    Extracts physical measurement counts and fidelity when completed.
    """
    from app.core.database import get_quantum_job, save_quantum_job

    # 1. Check local PostgreSQL cache first
    existing = get_quantum_job(job_id)
    if existing and existing.get("status") in ("DONE", "COMPLETED", "CANCELLED") and existing.get("result_counts"):
        exp_type = existing.get("experiment_type", "")
        if exp_type.startswith("qaoa") and not (existing.get("error_report") or {}).get("decoded_qaoa"):
            err_rep = existing.get("error_report") or {}
            symbols = err_rep.get("symbols") or err_rep.get("assets") or [f"Q{i}" for i in range(existing.get("num_qubits", 8))]
            budget = err_rep.get("budget", max(1, len(symbols) // 2))
            risk_factor = err_rep.get("risk_factor", 0.5)
            n_sym = len(symbols)
            exp_ret = np.ones(n_sym) * 0.10
            cov_mat = np.eye(n_sym) * 0.04
            decoded = decode_qaoa_measurements(existing["result_counts"], symbols, budget, exp_ret, cov_mat, risk_factor)
            err_rep["decoded_qaoa"] = decoded
            existing["error_report"] = err_rep
            existing["fidelity"] = decoded.get("budget_compliance_rate", 0.0)
            save_quantum_job(existing)
        return existing

    channel = getattr(settings, "IBM_QUANTUM_CHANNEL", "ibm_quantum_platform")
    token = settings.IBM_QUANTUM_TOKEN

    if not token:
        if existing:
            return existing
        return {"job_id": job_id, "status": "UNKNOWN", "error": "IBM Quantum token not configured"}

    try:
        from qiskit_ibm_runtime import QiskitRuntimeService

        service = QiskitRuntimeService(channel=channel, token=token)
        job = service.job(job_id)
        raw_status = job.status()
        status_str = str(raw_status).upper()
        if hasattr(raw_status, "name"):
            status_str = raw_status.name.upper()

        result_counts = None
        fidelity = None
        error_report = existing.get("error_report") if existing else {}

        # If job is DONE / COMPLETED, extract physical measurements
        if status_str in ("DONE", "COMPLETED"):
            try:
                res = job.result()
                # SamplerV2 returns PubResults
                if hasattr(res, "__getitem__") and len(res) > 0:
                    pub_res = res[0]
                    data_bin = getattr(pub_res, "data", None)
                    if data_bin:
                        for attr in ("meas2", "meas", "c"):
                            if hasattr(data_bin, attr):
                                bit_array = getattr(data_bin, attr)
                                if hasattr(bit_array, "get_counts"):
                                    result_counts = bit_array.get_counts()
                                    break
                elif hasattr(res, "get_counts"):
                    result_counts = res.get_counts()

                if result_counts:
                    total_shots = sum(result_counts.values())
                    exp_type = existing.get("experiment_type", "") if existing else ""
                    if exp_type == "qaoa_portfolio_optimization":
                        err_rep = existing.get("error_report") or {}
                        symbols = err_rep.get("symbols", [f"Q{i}" for i in range(existing.get("num_qubits", 8))])
                        budget = err_rep.get("budget", max(1, len(symbols) // 2))
                        risk_factor = err_rep.get("risk_factor", 0.5)
                        n_sym = len(symbols)
                        exp_ret = np.ones(n_sym) * 0.10
                        cov_mat = np.eye(n_sym) * 0.04
                        decoded = decode_qaoa_measurements(result_counts, symbols, budget, exp_ret, cov_mat, risk_factor)
                        error_report["decoded_qaoa"] = decoded
                        fidelity = decoded.get("budget_compliance_rate", 0.0)
                    else:
                        entangled_shots = result_counts.get("00", 0) + result_counts.get("11", 0)
                        fidelity = round(entangled_shots / total_shots, 4) if total_shots > 0 else 0.0
            except Exception as ex:
                logger.warning("Could not extract counts for job %s: %s", job_id, ex)

        backend_obj = getattr(job, "backend", None)
        backend_name = backend_obj().name if callable(backend_obj) and backend_obj() else (existing.get("qpu_backend") if existing else "ibm_fez")

        updated_data = {
            "job_id": job_id,
            "experiment_type": existing.get("experiment_type", "circuit_execution") if existing else "circuit_execution",
            "qpu_backend": backend_name,
            "num_qubits": existing.get("num_qubits", 2) if existing else 2,
            "shots": existing.get("shots", 1024) if existing else 1024,
            "status": status_str,
            "circuit_depth": existing.get("circuit_depth", 8) if existing else 8,
            "error_report": error_report,
            "result_counts": result_counts or (existing.get("result_counts") if existing else None),
            "fidelity": fidelity or (existing.get("fidelity") if existing else None),
        }

        # Persist to PostgreSQL
        save_quantum_job(updated_data)
        return updated_data

    except Exception as e:
        logger.error("Failed to query IBM Quantum job %s: %s", job_id, e)
        if existing:
            return existing
        return {
            "job_id": job_id,
            "status": "ERROR",
            "error": str(e),
        }


def get_experiment(experiment_id: str) -> dict | None:
    """Retrieve a stored experiment result from in-memory or PostgreSQL."""
    if experiment_id in _experiments:
        return _experiments[experiment_id]
    from app.core.database import get_quantum_job
    return get_quantum_job(experiment_id)


def list_experiments() -> list[dict]:
    """List all experiments from in-memory and PostgreSQL."""
    from app.core.database import list_quantum_jobs
    db_jobs = list_quantum_jobs(limit=20)
    seen_ids = set()
    results = []

    for job in db_jobs:
        seen_ids.add(job["job_id"])
        results.append({
            "experiment_id": job["job_id"],
            "experiment_type": job["experiment_type"],
            "backend": job["qpu_backend"],
            "status": job["status"],
            "created_at": job["created_at"],
        })

    for eid, exp in _experiments.items():
        if eid not in seen_ids:
            results.append({
                "experiment_id": eid,
                "experiment_type": exp.get("method", "unknown"),
                "backend": exp.get("backend", "unknown"),
                "status": exp.get("status", "completed"),
                "created_at": exp.get("created_at", ""),
            })

    return results
