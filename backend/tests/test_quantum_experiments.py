"""
Unit Tests — Quantum Experiments (Somesh's module)
====================================================
Tests for PennyLane VQC regime detection and Qiskit QAOA portfolio optimization.
"""

import numpy as np
import pandas as pd
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from app.quantum.experiments import (
    get_ibm_backend_info,
    get_quantum_status,
    quantum_regime_detection,
    quantum_portfolio_optimization,
    _extract_error_report,
    get_quantum_job_status,
    get_experiment,
    list_experiments,
)


class TestQuantumStatus:
    """Test quantum availability and status checks."""

    @patch("app.quantum.experiments.settings")
    def test_get_quantum_status_no_token(self, mock_settings):
        mock_settings.IBM_QUANTUM_TOKEN = None
        mock_settings.IBM_QUANTUM_CHANNEL = "ibm_quantum_platform"
        result = get_quantum_status()
        assert result["available"] is False
        assert result["simulator"] is True
        assert "No IBM token" in result["error"]

    @patch("app.quantum.experiments.settings")
    @patch("qiskit_ibm_runtime.QiskitRuntimeService")
    def test_get_quantum_status_with_token(self, mock_service, mock_settings):
        mock_settings.IBM_QUANTUM_TOKEN = "test-token"
        mock_settings.IBM_QUANTUM_CHANNEL = "ibm_quantum_platform"

        mock_backend = MagicMock()
        mock_backend.name = "ibm_fez"
        mock_config = MagicMock()
        mock_config.simulator = False
        mock_config.n_qubits = 127
        mock_backend.configuration.return_value = mock_config
        mock_backend.status.return_value.pending_jobs = 5

        mock_service_instance = MagicMock()
        mock_service_instance.backends.return_value = [mock_backend]
        mock_service.return_value = mock_service_instance

        result = get_quantum_status()
        assert result["available"] is True
        assert result["backend_name"] == "ibm_fez"
        assert result["simulator"] is False
        assert result["num_qubits"] == 127
        assert result["pending_jobs"] == 5

    @patch("app.quantum.experiments.settings")
    @patch("qiskit_ibm_runtime.QiskitRuntimeService")
    def test_get_quantum_status_simulator_only(self, mock_service, mock_settings):
        mock_settings.IBM_QUANTUM_TOKEN = "test-token"
        mock_settings.IBM_QUANTUM_CHANNEL = "ibm_quantum_platform"

        mock_backend = MagicMock()
        mock_backend.name = "ibmq_qasm_simulator"
        mock_config = MagicMock()
        mock_config.simulator = True
        mock_backend.configuration.return_value = mock_config

        mock_service_instance = MagicMock()
        mock_service_instance.backends.return_value = [mock_backend]
        mock_service.return_value = mock_service_instance

        result = get_quantum_status()
        assert result["available"] is True
        assert result["backend_name"] == "simulator"
        assert result["simulator"] is True


class TestIBMBackendInfo:
    """Test IBM backend info retrieval."""

    @patch("app.quantum.experiments.settings")
    def test_get_ibm_backend_info_no_token(self, mock_settings):
        mock_settings.IBM_QUANTUM_TOKEN = None
        result = get_ibm_backend_info()
        assert result["available"] is False
        assert "not set" in result["error"]

    @patch("app.quantum.experiments.settings")
    @patch("qiskit_ibm_runtime.QiskitRuntimeService")
    def test_get_ibm_backend_info_with_props(self, mock_service, mock_settings):
        mock_settings.IBM_QUANTUM_TOKEN = "test-token"
        mock_settings.IBM_QUANTUM_CHANNEL = "ibm_quantum_platform"

        mock_backend = MagicMock()
        mock_backend.name = "ibm_brisbane"
        mock_config = MagicMock()
        mock_config.n_qubits = 127
        mock_config.simulator = False
        mock_backend.configuration.return_value = mock_config
        mock_backend.status.return_value.status_msg = "active"
        mock_backend.status.return_value.pending_jobs = 3

        mock_props = MagicMock()
        # Create qubit properties with proper name attribute
        q0_prop1 = MagicMock()
        q0_prop1.name = "T1"
        q0_prop1.value = 100e-6
        q0_prop2 = MagicMock()
        q0_prop2.name = "T2"
        q0_prop2.value = 80e-6
        q0_prop3 = MagicMock()
        q0_prop3.name = "readout_error"
        q0_prop3.value = 0.02

        q1_prop1 = MagicMock()
        q1_prop1.name = "T1"
        q1_prop1.value = 90e-6
        q1_prop2 = MagicMock()
        q1_prop2.name = "T2"
        q1_prop2.value = 70e-6
        q1_prop3 = MagicMock()
        q1_prop3.name = "readout_error"
        q1_prop3.value = 0.015

        mock_props.qubits = [
            [q0_prop1, q0_prop2, q0_prop3],
            [q1_prop1, q1_prop2, q1_prop3],
        ]

        mock_gate = MagicMock()
        mock_gate.gate = "sx"
        mock_gate.qubits = [0]
        mock_param = MagicMock()
        mock_param.name = "gate_error"
        mock_param.value = 0.001
        mock_gate.parameters = [mock_param]
        mock_props.gates = [mock_gate]
        mock_props.last_update_date = "2024-01-01"
        mock_backend.properties.return_value = mock_props

        mock_service_instance = MagicMock()
        mock_service_instance.backends.return_value = [mock_backend]
        mock_service.return_value = mock_service_instance

        result = get_ibm_backend_info()
        assert result["available"] is True
        assert len(result["backends"]) == 1
        backend_info = result["backends"][0]
        assert "mean_readout_error" in backend_info
        assert "mean_gate_error" in backend_info
        assert "t1_times" in backend_info
        assert "t2_times" in backend_info


class TestQuantumRegimeDetection:
    """Test PennyLane VQC regime detection."""

    def test_quantum_regime_detection_unsupervised(self):
        np.random.seed(42)
        returns = pd.Series(np.random.normal(0.0005, 0.02, 200))
        volatility = pd.Series(np.abs(np.random.normal(0.015, 0.005, 200)))

        result = quantum_regime_detection(
            returns=returns,
            volatility=volatility,
            num_qubits=4,
            num_layers=1,
            epochs=5,
            learning_rate=0.01,
        )

        assert result["status"] == "completed"
        assert result["method"] == "pennylane_vqc"
        assert result["backend"] == "default.qubit"
        assert result["num_qubits"] == 4
        assert result["epochs"] == 5
        assert result["accuracy"] is None  # Unsupervised
        assert "regimes" in result
        assert len(result["regimes"]) == len(returns)

    def test_quantum_regime_detection_supervised(self):
        np.random.seed(42)
        returns = pd.Series(np.random.normal(0.0005, 0.02, 200))
        labels = pd.Series(np.random.randint(0, 4, 200))

        result = quantum_regime_detection(
            features=returns.values.reshape(-1, 1),
            labels=labels.values,
            num_qubits=4,
            num_layers=1,
            epochs=5,
        )

        assert result["status"] == "completed"
        assert result["accuracy"] is not None
        assert 0 <= result["accuracy"] <= 1

    def test_quantum_regime_detection_with_features(self):
        np.random.seed(42)
        features = np.random.randn(100, 8)
        result = quantum_regime_detection(
            features=features,
            num_qubits=4,
            num_layers=1,
            epochs=3,
        )
        assert result["status"] == "completed"
        assert result["num_qubits"] == 4

    def test_quantum_regime_detection_invalid_input(self):
        with pytest.raises(ValueError, match="features or returns must be provided"):
            quantum_regime_detection(num_qubits=4, epochs=3)


class TestQuantumPortfolioOptimization:
    """Test Qiskit QAOA portfolio optimization."""

    def test_quantum_portfolio_optimization_basic(self):
        symbols = ["BTC", "ETH", "SOL", "ADA"]
        expected_returns = np.array([0.15, 0.12, 0.18, 0.10])
        cov_matrix = np.array([
            [0.04, 0.01, 0.02, 0.005],
            [0.01, 0.03, 0.015, 0.003],
            [0.02, 0.015, 0.05, 0.01],
            [0.005, 0.003, 0.01, 0.02],
        ])

        result = quantum_portfolio_optimization(
            expected_returns=expected_returns,
            cov_matrix=cov_matrix,
            symbols=symbols,
            budget=2,
            risk_factor=0.5,
            reps=1,
            use_real_hardware=False,
        )

        assert result["status"] == "completed"
        assert result["method"] == "qaoa"
        assert result["backend"] == "aer_simulator"
        assert len(result["optimal_weights"]) == len(symbols)
        assert abs(sum(result["optimal_weights"]) - 1.0) < 0.01
        assert len(result["selected_assets"]) == 2
        assert "classical_comparison" in result
        assert "decoded_qaoa" in result

    def test_quantum_portfolio_optimization_with_returns_df(self):
        np.random.seed(42)
        returns_df = pd.DataFrame({
            "BTC": np.random.normal(0.0005, 0.02, 252),
            "ETH": np.random.normal(0.0004, 0.018, 252),
            "SOL": np.random.normal(0.0006, 0.025, 252),
        })

        result = quantum_portfolio_optimization(
            returns_df=returns_df,
            budget=2,
            risk_factor=0.5,
            reps=1,
        )

        assert result["status"] == "completed"
        assert len(result["symbols"]) == 3
        assert "optimal_weights" in result

    def test_quantum_portfolio_optimization_missing_inputs(self):
        with pytest.raises(ValueError, match="must be provided"):
            quantum_portfolio_optimization(
                expected_returns=np.array([0.1, 0.2]),
                cov_matrix=np.eye(2),
                symbols=None,
            )

    @patch("app.quantum.experiments.settings")
    def test_quantum_portfolio_optimization_parameters(self, mock_settings):
        mock_settings.IBM_QUANTUM_TOKEN = None  # Force simulator mode
        symbols = ["A", "B", "C", "D"]
        expected_returns = np.array([0.1, 0.12, 0.08, 0.15])
        cov_matrix = np.eye(4) * 0.04

        # Test with qaoa_p parameter
        result1 = quantum_portfolio_optimization(
            expected_returns=expected_returns,
            cov_matrix=cov_matrix,
            symbols=symbols,
            qaoa_p=2,
        )
        assert result1["circuit_depth"] >= 2

        # Test with use_hardware parameter (should fallback to simulator since no token)
        result2 = quantum_portfolio_optimization(
            expected_returns=expected_returns,
            cov_matrix=cov_matrix,
            symbols=symbols,
            use_hardware=True,
        )
        assert result2["backend"] == "aer_simulator"


class TestErrorReportExtraction:
    """Test error report extraction from IBM backends."""

    def test_extract_error_report_with_props(self):
        mock_backend = MagicMock()
        mock_backend.name = "test_backend"

        mock_props = MagicMock()
        mock_props.qubits = [
            [MagicMock(name="readout_error", value=0.02), MagicMock(name="T1", value=100e-6), MagicMock(name="T2", value=80e-6)],
            [MagicMock(name="readout_error", value=0.015), MagicMock(name="T1", value=90e-6), MagicMock(name="T2", value=70e-6)],
        ]
        mock_gate = MagicMock()
        mock_gate.gate = "cx"
        mock_gate.qubits = [0, 1]
        mock_param = MagicMock(name="gate_error", value=0.005)
        mock_gate.parameters = [mock_param]
        mock_props.gates = [mock_gate]
        mock_props.last_update_date = "2024-01-01"
        mock_backend.properties.return_value = mock_props

        report = _extract_error_report(mock_backend, 2)

        assert report["backend_name"] == "test_backend"
        assert report["num_qubits_used"] == 2
        assert "mean_readout_error" in report
        assert "mean_gate_error" in report
        assert "mean_t1_us" in report
        assert "mean_t2_us" in report
        assert report["calibration_time"] == "2024-01-01"

    def test_extract_error_report_no_props(self):
        mock_backend = MagicMock()
        mock_backend.name = "test_backend"
        mock_backend.properties.return_value = None

        report = _extract_error_report(mock_backend, 2)

        assert report["backend_name"] == "test_backend"
        assert "mean_readout_error" not in report


class TestJobStatus:
    """Test quantum job status polling."""

    @patch("app.quantum.experiments.settings")
    def test_get_quantum_job_status_no_token(self, mock_settings):
        mock_settings.IBM_QUANTUM_TOKEN = None
        result = get_quantum_job_status("job-123")
        assert result["job_id"] == "job-123"
        assert result["status"] == "UNKNOWN"

    @patch("app.quantum.experiments.settings")
    @patch("app.core.database.get_quantum_job")
    def test_get_quantum_job_status_from_cache(self, mock_get_job, mock_settings):
        mock_settings.IBM_QUANTUM_TOKEN = "test-token"
        mock_get_job.return_value = {
            "job_id": "job-123",
            "status": "DONE",
            "result_counts": {"00": 500, "11": 500},
            "experiment_type": "qaoa_portfolio_optimization",
            "error_report": {"symbols": ["A", "B"], "budget": 1, "risk_factor": 0.5},
            "num_qubits": 2,
        }

        result = get_quantum_job_status("job-123")
        assert result["status"] == "DONE"
        assert "decoded_qaoa" in result["error_report"]


class TestExperimentStorage:
    """Test experiment storage and retrieval."""

    def test_get_experiment_from_memory(self):
        from app.quantum.experiments import _experiments
        _experiments.clear()
        test_exp = {"experiment_id": "TEST-123", "status": "completed"}
        _experiments["TEST-123"] = test_exp

        result = get_experiment("TEST-123")
        assert result == test_exp

    def test_get_experiment_not_found(self):
        from app.quantum.experiments import _experiments
        _experiments.clear()
        result = get_experiment("NONEXISTENT")
        assert result is None

    @patch("app.core.database.list_quantum_jobs")
    def test_list_experiments(self, mock_list_jobs):
        from app.quantum.experiments import _experiments
        _experiments.clear()

        mock_list_jobs.return_value = [
            {"job_id": "DB-1", "experiment_type": "qaoa", "qpu_backend": "ibm_fez", "status": "DONE", "created_at": "2024-01-01"},
        ]

        result = list_experiments()
        assert len(result) == 1
        assert result[0]["experiment_id"] == "DB-1"