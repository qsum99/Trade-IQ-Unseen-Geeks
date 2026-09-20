"""
Unit Tests — Quantum Experiments Final Coverage
=================================================
Tests for remaining uncovered lines in quantum/experiments.py.
"""

import numpy as np
import pandas as pd
import pytest
from unittest.mock import MagicMock, patch

from app.quantum.experiments import (
    quantum_regime_detection,
    quantum_portfolio_optimization,
    _extract_error_report,
    get_quantum_job_status,
)


class TestDBExceptionHandling:
    """Test database exception handling."""

    @patch("app.core.database.save_quantum_job")
    def test_qrd_db_exception_handling(self, mock_save_job):
        """Test DB exception handling in quantum regime detection."""
        mock_save_job.side_effect = Exception("DB connection failed")

        np.random.seed(42)
        returns = pd.Series(np.random.normal(0.0005, 0.02, 100))

        result = quantum_regime_detection(
            returns=returns,
            num_qubits=4,
            num_layers=1,
            epochs=3,
        )

        assert result["status"] == "completed"
        # Should not raise, just log warning

    @patch("app.core.database.save_portfolio_run")
    def test_qpo_db_exception_handling(self, mock_save_portfolio):
        """Test DB exception handling in quantum portfolio optimization."""
        from app.quantum.experiments import settings
        settings.IBM_QUANTUM_TOKEN = None

        mock_save_portfolio.side_effect = Exception("DB connection failed")

        symbols = ["A", "B", "C"]
        expected_returns = np.array([0.1, 0.12, 0.08])
        cov_matrix = np.eye(3) * 0.04

        result = quantum_portfolio_optimization(
            expected_returns=expected_returns,
            cov_matrix=cov_matrix,
            symbols=symbols,
            budget=2,
        )

        assert result["status"] == "completed"
        # Should not raise, just log warning


class TestExtractErrorReportDetails:
    """Test detailed error report extraction."""

    def test_extract_error_report_with_t1_t2(self):
        """Test extraction of T1 and T2 times."""
        mock_backend = MagicMock()
        mock_backend.name = "test_backend"

        mock_props = MagicMock()
        # Create proper mock qubit properties with name attribute
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

        report = _extract_error_report(mock_backend, 2)

        assert "mean_t1_us" in report
        assert "mean_t2_us" in report
        assert pytest.approx(report["mean_t1_us"], rel=1e-10) == 95e-6  # (100+90)/2
        assert pytest.approx(report["mean_t2_us"], rel=1e-10) == 75e-6  # (80+70)/2
        assert "mean_gate_error" in report
        assert report["max_gate_error"] == 0.001
        assert report["calibration_time"] == "2024-01-01"

    def test_extract_error_report_exception_handling(self):
        """Test extraction handles exceptions gracefully."""
        mock_backend = MagicMock()
        mock_backend.name = "test_backend"
        mock_backend.properties.side_effect = Exception("Props error")

        report = _extract_error_report(mock_backend, 2)

        assert report["backend_name"] == "test_backend"
        assert "error_extraction_failed" in report
        assert "Props error" in report["error_extraction_failed"]


class TestQuantumJobStatusDetailed:
    """Test detailed quantum job status polling paths."""

    @patch("app.quantum.experiments.settings")
    @patch("app.core.database.get_quantum_job")
    @patch("qiskit_ibm_runtime.QiskitRuntimeService")
    def test_get_quantum_job_status_pub_result_meas2(self, mock_service, mock_get_job, mock_settings):
        """Test job status with PubResult.meas2 attribute."""
        mock_settings.IBM_QUANTUM_TOKEN = "test-token"
        mock_settings.IBM_QUANTUM_CHANNEL = "ibm_quantum_platform"
        mock_get_job.return_value = None

        mock_job = MagicMock()
        mock_status = MagicMock()
        mock_status.name = "DONE"
        mock_job.status.return_value = mock_status

        mock_result = MagicMock()
        mock_pub_res = MagicMock()
        mock_data_bin = MagicMock()
        mock_meas2 = MagicMock()
        mock_meas2.get_counts.return_value = {"00": 600, "11": 400}
        mock_data_bin.meas2 = mock_meas2
        mock_pub_res.data = mock_data_bin
        mock_result.__getitem__ = MagicMock(return_value=mock_pub_res)
        mock_job.result.return_value = mock_result

        mock_backend_obj = MagicMock()
        mock_backend_obj.name = "ibm_brisbane"
        mock_job.backend = mock_backend_obj

        mock_service_instance = MagicMock()
        mock_service_instance.job.return_value = mock_job
        mock_service.return_value = mock_service_instance

        result = get_quantum_job_status("job-123")

        assert result["status"] == "DONE"

    @patch("app.quantum.experiments.settings")
    @patch("app.core.database.get_quantum_job")
    @patch("qiskit_ibm_runtime.QiskitRuntimeService")
    def test_get_quantum_job_status_pub_result_meas(self, mock_service, mock_get_job, mock_settings):
        """Test job status with PubResult.meas attribute."""
        mock_settings.IBM_QUANTUM_TOKEN = "test-token"
        mock_settings.IBM_QUANTUM_CHANNEL = "ibm_quantum_platform"
        mock_get_job.return_value = None

        mock_job = MagicMock()
        mock_status = MagicMock()
        mock_status.name = "DONE"
        mock_job.status.return_value = mock_status

        mock_result = MagicMock()
        mock_pub_res = MagicMock()
        mock_data_bin = MagicMock()
        mock_meas = MagicMock()
        mock_meas.get_counts.return_value = {"00": 600, "11": 400}
        mock_data_bin.meas = mock_meas
        mock_pub_res.data = mock_data_bin
        mock_result.__getitem__ = MagicMock(return_value=mock_pub_res)
        mock_job.result.return_value = mock_result

        mock_backend_obj = MagicMock()
        mock_backend_obj.name = "ibm_brisbane"
        mock_job.backend = mock_backend_obj

        mock_service_instance = MagicMock()
        mock_service_instance.job.return_value = mock_job
        mock_service.return_value = mock_service_instance

        result = get_quantum_job_status("job-123")

        assert result["status"] == "DONE"

    @patch("app.quantum.experiments.settings")
    @patch("app.core.database.get_quantum_job")
    @patch("qiskit_ibm_runtime.QiskitRuntimeService")
    def test_get_quantum_job_status_pub_result_c(self, mock_service, mock_get_job, mock_settings):
        """Test job status with PubResult.c attribute."""
        mock_settings.IBM_QUANTUM_TOKEN = "test-token"
        mock_settings.IBM_QUANTUM_CHANNEL = "ibm_quantum_platform"
        mock_get_job.return_value = None

        mock_job = MagicMock()
        mock_status = MagicMock()
        mock_status.name = "DONE"
        mock_job.status.return_value = mock_status

        mock_result = MagicMock()
        mock_pub_res = MagicMock()
        mock_data_bin = MagicMock()
        mock_c = MagicMock()
        mock_c.get_counts.return_value = {"00": 600, "11": 400}
        mock_data_bin.c = mock_c
        mock_pub_res.data = mock_data_bin
        mock_result.__getitem__ = MagicMock(return_value=mock_pub_res)
        mock_job.result.return_value = mock_result

        mock_backend_obj = MagicMock()
        mock_backend_obj.name = "ibm_brisbane"
        mock_job.backend = mock_backend_obj

        mock_service_instance = MagicMock()
        mock_service_instance.job.return_value = mock_job
        mock_service.return_value = mock_service_instance

        result = get_quantum_job_status("job-123")

        assert result["status"] == "DONE"

    @patch("app.quantum.experiments.settings")
    @patch("app.core.database.get_quantum_job")
    @patch("qiskit_ibm_runtime.QiskitRuntimeService")
    def test_get_quantum_job_status_result_get_counts(self, mock_service, mock_get_job, mock_settings):
        """Test job status with result.get_counts() method."""
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
        # No __getitem__

        mock_backend_obj = MagicMock()
        mock_backend_obj.name = "ibm_brisbane"
        mock_job.backend = mock_backend_obj

        mock_service_instance = MagicMock()
        mock_service_instance.job.return_value = mock_job
        mock_service.return_value = mock_service_instance

        result = get_quantum_job_status("job-123")

        assert result["status"] == "DONE"

    @patch("app.quantum.experiments.settings")
    @patch("app.core.database.get_quantum_job")
    @patch("qiskit_ibm_runtime.QiskitRuntimeService")
    def test_get_quantum_job_status_extraction_error(self, mock_service, mock_get_job, mock_settings):
        """Test job status when count extraction fails."""
        mock_settings.IBM_QUANTUM_TOKEN = "test-token"
        mock_settings.IBM_QUANTUM_CHANNEL = "ibm_quantum_platform"
        mock_get_job.return_value = None

        mock_job = MagicMock()
        mock_status = MagicMock()
        mock_status.name = "DONE"
        mock_job.status.return_value = mock_status

        mock_job.result.side_effect = Exception("Result extraction failed")

        mock_backend_obj = MagicMock()
        mock_backend_obj.name = "ibm_brisbane"
        mock_job.backend = mock_backend_obj

        mock_service_instance = MagicMock()
        mock_service_instance.job.return_value = mock_job
        mock_service.return_value = mock_service_instance

        result = get_quantum_job_status("job-123")

        assert result["status"] == "DONE"
        # Should handle extraction error gracefully

    @patch("app.quantum.experiments.settings")
    @patch("app.core.database.get_quantum_job")
    @patch("qiskit_ibm_runtime.QiskitRuntimeService")
    def test_get_quantum_job_status_bell_fidelity(self, mock_service, mock_get_job, mock_settings):
        """Test job status for Bell state experiment (non-QAOA)."""
        mock_settings.IBM_QUANTUM_TOKEN = "test-token"
        mock_settings.IBM_QUANTUM_CHANNEL = "ibm_quantum_platform"
        mock_get_job.return_value = None

        mock_job = MagicMock()
        mock_status = MagicMock()
        mock_status.name = "DONE"
        mock_job.status.return_value = mock_status

        mock_result = MagicMock()
        mock_result.get_counts.return_value = {"00": 600, "11": 400, "01": 100, "10": 100}
        mock_job.result.return_value = mock_result

        mock_backend_obj = MagicMock()
        mock_backend_obj.name = "ibm_brisbane"
        mock_job.backend = mock_backend_obj

        mock_service_instance = MagicMock()
        mock_service_instance.job.return_value = mock_job
        mock_service.return_value = mock_service_instance

        result = get_quantum_job_status("job-123")

        assert result["status"] == "DONE"
        # Bell fidelity = (00 + 11) / total
        assert "fidelity" in result

    @patch("app.quantum.experiments.settings")
    @patch("app.core.database.get_quantum_job")
    @patch("qiskit_ibm_runtime.QiskitRuntimeService")
    def test_get_quantum_job_status_general_exception(self, mock_service, mock_get_job, mock_settings):
        """Test job status with general exception."""
        mock_settings.IBM_QUANTUM_TOKEN = "test-token"
        mock_get_job.return_value = None
        mock_service.side_effect = Exception("IBM API error")

        result = get_quantum_job_status("job-123")

        assert result["status"] == "ERROR"
        assert "IBM API error" in result["error"]


class TestQuantumRegimeDetectionSupervised:
    """Test supervised regime detection paths."""

    def test_qrd_supervised_accuracy_calculation(self):
        """Test supervised accuracy calculation path."""
        np.random.seed(42)
        returns = pd.Series(np.random.normal(0.0005, 0.02, 200))
        labels = pd.Series(np.random.randint(0, 4, 200))

        result = quantum_regime_detection(
            returns=returns,
            labels=labels,
            num_qubits=4,
            num_layers=1,
            epochs=3,
        )

        assert result["status"] == "completed"
        assert result["accuracy"] is not None
        assert 0 <= result["accuracy"] <= 1


class TestQuantumPortfolioOptimizationDetails:
    """Test detailed QPO paths."""

    @patch("app.quantum.experiments.settings")
    def test_qpo_returns_df_path(self, mock_settings):
        """Test QPO with returns_df parameter."""
        mock_settings.IBM_QUANTUM_TOKEN = None

        np.random.seed(42)
        returns_df = pd.DataFrame({
            "A": np.random.normal(0.0005, 0.02, 252),
            "B": np.random.normal(0.0004, 0.018, 252),
            "C": np.random.normal(0.0006, 0.025, 252),
        })

        result = quantum_portfolio_optimization(
            returns_df=returns_df,
            budget=2,
            risk_factor=0.3,
            reps=1,
        )

        assert result["status"] == "completed"
        assert len(result["symbols"]) == 3

    @patch("app.quantum.experiments.settings")
    def test_qpo_maxiter_parameter(self, mock_settings):
        """Test QPO with maxiter parameter."""
        mock_settings.IBM_QUANTUM_TOKEN = None

        symbols = ["A", "B", "C"]
        expected_returns = np.array([0.1, 0.12, 0.08])
        cov_matrix = np.eye(3) * 0.04

        result = quantum_portfolio_optimization(
            expected_returns=expected_returns,
            cov_matrix=cov_matrix,
            symbols=symbols,
            budget=2,
            maxiter=200,
        )

        assert result["status"] == "completed"

    @patch("app.quantum.experiments.settings")
    def test_qpo_use_hardware_alias(self, mock_settings):
        """Test QPO with use_hardware parameter alias."""
        mock_settings.IBM_QUANTUM_TOKEN = None

        symbols = ["A", "B", "C"]
        expected_returns = np.array([0.1, 0.12, 0.08])
        cov_matrix = np.eye(3) * 0.04

        result = quantum_portfolio_optimization(
            expected_returns=expected_returns,
            cov_matrix=cov_matrix,
            symbols=symbols,
            budget=2,
            use_hardware=True,
        )

        assert result["backend"] == "aer_simulator"