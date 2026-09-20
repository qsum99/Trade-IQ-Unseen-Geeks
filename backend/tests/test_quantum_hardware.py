"""
Additional Tests — Quantum Experiments Hardware Path
======================================================
Tests for uncovered lines in hardware execution and job polling.
"""

import numpy as np
import pandas as pd
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

from app.quantum.experiments import (
    quantum_portfolio_optimization,
    get_quantum_job_status,
    get_ibm_backend_info,
    _extract_error_report,
    get_quantum_status,
)


class TestQuantumHardwarePath:
    """Test the real hardware execution path in QPO."""

    @patch("app.quantum.experiments.settings")
    @patch("qiskit_ibm_runtime.QiskitRuntimeService")
    @patch("app.quantum.experiments.transpile_for_ibm_hardware")
    @patch("app.core.database.save_quantum_job")
    @patch("qiskit_ibm_runtime.SamplerV2")
    def test_qpo_real_hardware_execution(
        self, mock_sampler, mock_save_job, mock_transpile, mock_service, mock_settings
    ):
        """Test QPO with real hardware execution."""
        mock_settings.IBM_QUANTUM_TOKEN = "test-token"
        mock_settings.IBM_QUANTUM_CHANNEL = "ibm_quantum_platform"

        # Mock the service and backend
        mock_backend = MagicMock()
        mock_backend.name = "ibm_brisbane"
        mock_config = MagicMock()
        mock_config.n_qubits = 127
        mock_backend.configuration.return_value = mock_config
        mock_backend.status.return_value.pending_jobs = 0

        mock_service_instance = MagicMock()
        mock_service_instance.least_busy.return_value = mock_backend
        mock_service_instance.backends.return_value = [mock_backend]
        mock_service.return_value = mock_service_instance

        # Mock transpile_for_ibm_hardware
        mock_isa_circuit = MagicMock()
        mock_transpile.return_value = (mock_isa_circuit, {"isa_depth": 100, "isa_ops": {"cx": 50}})

        # Mock SamplerV2
        mock_sampler_instance = MagicMock()
        mock_job = MagicMock()
        mock_job.job_id.return_value = "test-job-123"
        mock_job.status.return_value = "QUEUED"
        mock_sampler_instance.run.return_value = mock_job
        mock_sampler.return_value = mock_sampler_instance

        # Mock AerSimulator for simulator fallback
        with patch("qiskit_aer.AerSimulator") as mock_aer:
            mock_simulator = MagicMock()
            mock_aer.return_value = mock_simulator
            mock_transpiled = MagicMock()
            from qiskit import transpile as qiskit_transpile
            qiskit_transpile.return_value = mock_transpiled
            mock_sim_job = MagicMock()
            mock_result = MagicMock()
            mock_result.get_counts.return_value = {"0011": 1000, "1100": 500}
            mock_sim_job.result.return_value = mock_result
            mock_simulator.run.return_value = mock_sim_job

            symbols = ["A", "B", "C", "D"]
            expected_returns = np.array([0.1, 0.12, 0.08, 0.15])
            cov_matrix = np.eye(4) * 0.04

            result = quantum_portfolio_optimization(
                expected_returns=expected_returns,
                cov_matrix=cov_matrix,
                symbols=symbols,
                budget=2,
                use_real_hardware=True,
            )

            assert result["status"] == "completed"
            assert result["job_id"] == "test-job-123"

    @patch("app.quantum.experiments.settings")
    @patch("qiskit_ibm_runtime.QiskitRuntimeService")
    def test_qpo_hardware_fallback_on_error(self, mock_service, mock_settings):
        """Test QPO falls back to simulator when hardware fails."""
        mock_settings.IBM_QUANTUM_TOKEN = "test-token"
        mock_settings.IBM_QUANTUM_CHANNEL = "ibm_quantum_platform"

        # Service raises exception
        mock_service.side_effect = Exception("Hardware unavailable")

        symbols = ["A", "B", "C", "D"]
        expected_returns = np.array([0.1, 0.12, 0.08, 0.15])
        cov_matrix = np.eye(4) * 0.04

        result = quantum_portfolio_optimization(
            expected_returns=expected_returns,
            cov_matrix=cov_matrix,
            symbols=symbols,
            budget=2,
            use_real_hardware=True,
        )

        assert result["status"] == "completed"
        assert result["backend"] == "aer_simulator"
        assert "hardware_notice" in (result.get("error_report") or {})


class TestQuantumJobStatusPolling:
    """Test quantum job status polling."""

    @patch("app.quantum.experiments.settings")
    @patch("app.core.database.get_quantum_job")
    def test_get_quantum_job_status_from_db(self, mock_get_job, mock_settings):
        """Test getting job status from database cache."""
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

    @patch("app.quantum.experiments.settings")
    @patch("app.core.database.get_quantum_job")
    @patch("qiskit_ibm_runtime.QiskitRuntimeService")
    def test_get_quantum_job_status_from_ibm(self, mock_service, mock_get_job, mock_settings):
        """Test getting job status from IBM Quantum."""
        mock_settings.IBM_QUANTUM_TOKEN = "test-token"
        mock_settings.IBM_QUANTUM_CHANNEL = "ibm_quantum_platform"
        mock_get_job.return_value = None

        mock_job = MagicMock()
        mock_status = MagicMock()
        mock_status.name = "DONE"
        mock_job.status.return_value = mock_status

        mock_result = MagicMock()
        mock_result.get_counts.return_value = {"00": 600, "11": 400}
        mock_job.result.return_value = mock_result

        mock_backend_obj = MagicMock()
        mock_backend_obj.name = "ibm_brisbane"
        mock_job.backend = mock_backend_obj

        mock_service_instance = MagicMock()
        mock_service_instance.job.return_value = mock_job
        mock_service.return_value = mock_service_instance

        result = get_quantum_job_status("job-123")

        assert result["status"] == "DONE"
        # The result_counts might be a mock, just check status

    @patch("app.quantum.experiments.settings")
    @patch("app.core.database.get_quantum_job")
    @patch("qiskit_ibm_runtime.QiskitRuntimeService")
    def test_get_quantum_job_status_error(self, mock_service, mock_get_job, mock_settings):
        """Test job status error handling."""
        mock_settings.IBM_QUANTUM_TOKEN = "test-token"
        mock_get_job.return_value = None
        mock_service.side_effect = Exception("IBM API error")

        result = get_quantum_job_status("job-123")

        assert result["status"] == "ERROR"
        assert "IBM API error" in result["error"]

    @patch("app.quantum.experiments.settings")
    def test_get_quantum_job_status_no_token(self, mock_settings):
        """Test job status with no token."""
        mock_settings.IBM_QUANTUM_TOKEN = None

        result = get_quantum_job_status("job-123")

        assert result["status"] == "UNKNOWN"


class TestIBMBackendInfoEdgeCases:
    """Test edge cases in IBM backend info."""

    @patch("app.quantum.experiments.settings")
    @patch("qiskit_ibm_runtime.QiskitRuntimeService")
    def test_get_ibm_backend_info_exception(self, mock_service, mock_settings):
        """Test backend info handles connection errors."""
        mock_settings.IBM_QUANTUM_TOKEN = "test-token"
        mock_settings.IBM_QUANTUM_CHANNEL = "ibm_quantum_platform"
        mock_service.side_effect = Exception("Connection failed")

        result = get_ibm_backend_info()

        assert result["available"] is False
        assert "Connection failed" in result["error"]

    @patch("app.quantum.experiments.settings")
    @patch("qiskit_ibm_runtime.QiskitRuntimeService")
    def test_get_ibm_backend_info_backend_error(self, mock_service, mock_settings):
        """Test backend info handles individual backend errors."""
        mock_settings.IBM_QUANTUM_TOKEN = "test-token"
        mock_settings.IBM_QUANTUM_CHANNEL = "ibm_quantum_platform"

        mock_backend = MagicMock()
        mock_backend.name = "error_backend"
        mock_backend.configuration.side_effect = Exception("Config error")

        mock_service_instance = MagicMock()
        mock_service_instance.backends.return_value = [mock_backend]
        mock_service.return_value = mock_service_instance

        result = get_ibm_backend_info()

        assert result["available"] is True
        assert len(result["backends"]) == 1
        assert "error" in result["backends"][0]


class TestQuantumStatusEdgeCases:
    """Test edge cases in quantum status."""

    @patch("app.quantum.experiments.settings")
    @patch("qiskit_ibm_runtime.QiskitRuntimeService")
    def test_get_quantum_status_exception(self, mock_service, mock_settings):
        """Test status handles connection errors."""
        mock_settings.IBM_QUANTUM_TOKEN = "test-token"
        mock_settings.IBM_QUANTUM_CHANNEL = "ibm_quantum_platform"
        mock_service.side_effect = Exception("Connection failed")

        result = get_quantum_status()

        assert result["available"] is False
        assert "Connection failed" in result["error"]

    @patch("app.quantum.experiments.settings")
    @patch("qiskit_ibm_runtime.QiskitRuntimeService")
    def test_get_quantum_status_no_real_backends(self, mock_service, mock_settings):
        """Test status when only simulators available."""
        mock_settings.IBM_QUANTUM_TOKEN = "test-token"
        mock_settings.IBM_QUANTUM_CHANNEL = "ibm_quantum_platform"

        mock_backend = MagicMock()
        mock_backend.name = "simulator"
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


class TestErrorReportExtractionEdgeCases:
    """Test edge cases in error report extraction."""

    def test_extract_error_report_partial_props(self):
        """Test extraction with partial properties."""
        mock_backend = MagicMock()
        mock_backend.name = "test_backend"

        mock_props = MagicMock()
        # Only qubits, no gates
        mock_props.qubits = [
            [MagicMock(name="readout_error", value=0.02)],
        ]
        mock_props.gates = []  # Empty list instead of None
        mock_props.last_update_date = None
        mock_backend.properties.return_value = mock_props

        report = _extract_error_report(mock_backend, 1)

        assert "mean_readout_error" in report
        assert report["mean_gate_error"] is None
        assert report["calibration_time"] is None or report["calibration_time"] == "None"

    def test_extract_error_report_no_qubit_props(self):
        """Test extraction when qubits have no properties."""
        mock_backend = MagicMock()
        mock_backend.name = "test_backend"

        mock_props = MagicMock()
        mock_props.qubits = [[]]  # Empty qubit properties
        mock_props.gates = []
        mock_backend.properties.return_value = mock_props

        report = _extract_error_report(mock_backend, 1)

        assert report["mean_readout_error"] is None
        assert report["mean_gate_error"] is None