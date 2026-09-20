"""
Additional Unit Tests — Quantum Experiments Edge Cases
========================================================
Tests for uncovered lines in quantum/experiments.py.
"""

import numpy as np
import pandas as pd
import pytest
from unittest.mock import MagicMock, patch

from app.quantum.experiments import (
    quantum_regime_detection,
    quantum_portfolio_optimization,
    _extract_error_report,
    get_experiment,
    list_experiments,
)


class TestQuantumRegimeDetectionEdgeCases:
    """Test edge cases in quantum regime detection."""

    def test_qrd_with_returns_and_volatility(self):
        """Test QRD with both returns and volatility provided."""
        np.random.seed(42)
        returns = pd.Series(np.random.normal(0.0005, 0.02, 200))
        volatility = pd.Series(np.abs(np.random.normal(0.015, 0.005, 200)))

        result = quantum_regime_detection(
            returns=returns,
            volatility=volatility,
            num_qubits=4,
            num_layers=1,
            epochs=3,
        )

        assert result["status"] == "completed"
        assert result["regimes"] is not None

    def test_qrd_with_features_array(self):
        """Test QRD with features array directly."""
        np.random.seed(42)
        features = np.random.randn(100, 8)

        result = quantum_regime_detection(
            features=features,
            num_qubits=4,
            num_layers=1,
            epochs=3,
        )

        assert result["status"] == "completed"

    def test_qrd_n_qubits_override(self):
        """Test n_qubits parameter overrides num_qubits."""
        np.random.seed(42)
        features = np.random.randn(50, 6)

        result = quantum_regime_detection(
            features=features,
            num_qubits=8,  # This should be overridden
            n_qubits=3,    # This takes precedence
            num_layers=1,
            epochs=3,
        )

        assert result["num_qubits"] == 3

    def test_qrd_steps_override(self):
        """Test steps parameter overrides epochs."""
        np.random.seed(42)
        features = np.random.randn(50, 4)

        result = quantum_regime_detection(
            features=features,
            num_qubits=4,
            num_layers=1,
            epochs=10,     # Should be overridden
            steps=3,       # This takes precedence
        )

        assert result["epochs"] == 3

    def test_qrd_supervised_with_labels(self):
        """Test QRD with supervised labels."""
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

    def test_qrd_feature_reduction(self):
        """Test PCA feature reduction when features > qubits."""
        np.random.seed(42)
        features = np.random.randn(50, 10)  # 10 features, 4 qubits

        result = quantum_regime_detection(
            features=features,
            num_qubits=4,
            num_layers=1,
            epochs=3,
        )

        assert result["status"] == "completed"
        assert result["num_qubits"] == 4


class TestQuantumPortfolioOptimizationEdgeCases:
    """Test edge cases in quantum portfolio optimization."""

    @patch("app.quantum.experiments.settings")
    def test_qpo_with_qaoa_p_parameter(self, mock_settings):
        """Test qaoa_p parameter."""
        mock_settings.IBM_QUANTUM_TOKEN = None

        symbols = ["A", "B", "C", "D"]
        expected_returns = np.array([0.1, 0.12, 0.08, 0.15])
        cov_matrix = np.eye(4) * 0.04

        result = quantum_portfolio_optimization(
            expected_returns=expected_returns,
            cov_matrix=cov_matrix,
            symbols=symbols,
            budget=2,
            qaoa_p=3,  # Test reps parameter
        )

        # Circuit depth depends on reps and qubits
        assert result["status"] == "completed"
        assert "circuit_depth" in result

    @patch("app.quantum.experiments.settings")
    def test_qpo_with_use_hardware_parameter(self, mock_settings):
        """Test use_hardware parameter (alias for use_real_hardware)."""
        mock_settings.IBM_QUANTUM_TOKEN = None

        symbols = ["A", "B", "C", "D"]
        expected_returns = np.array([0.1, 0.12, 0.08, 0.15])
        cov_matrix = np.eye(4) * 0.04

        result = quantum_portfolio_optimization(
            expected_returns=expected_returns,
            cov_matrix=cov_matrix,
            symbols=symbols,
            budget=2,
            use_hardware=True,
        )

        # Should fallback to simulator when no token
        assert result["backend"] == "aer_simulator"

    @patch("app.quantum.experiments.settings")
    def test_qpo_returns_df_with_budget(self, mock_settings):
        """Test with returns_df and budget."""
        mock_settings.IBM_QUANTUM_TOKEN = None

        np.random.seed(42)
        returns_df = pd.DataFrame({
            "A": np.random.normal(0.0005, 0.02, 252),
            "B": np.random.normal(0.0004, 0.018, 252),
            "C": np.random.normal(0.0006, 0.025, 252),
            "D": np.random.normal(0.0003, 0.015, 252),
        })

        result = quantum_portfolio_optimization(
            returns_df=returns_df,
            budget=2,
            risk_factor=0.3,
            reps=1,
        )

        assert result["status"] == "completed"
        assert len(result["selected_assets"]) == 2

    @patch("app.quantum.experiments.settings")
    def test_qpo_with_maxiter(self, mock_settings):
        """Test with maxiter parameter."""
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


class TestExtractErrorReportEdgeCases:
    """Test edge cases in error report extraction."""

    def test_extract_error_report_no_props(self):
        """Test extraction when backend has no properties."""
        mock_backend = MagicMock()
        mock_backend.name = "test_backend"
        mock_backend.properties.return_value = None

        report = _extract_error_report(mock_backend, 2)

        assert report["backend_name"] == "test_backend"
        assert report["num_qubits_used"] == 2
        assert "mean_readout_error" not in report

    def test_extract_error_report_empty_gates(self):
        """Test extraction with empty gates list."""
        mock_backend = MagicMock()
        mock_backend.name = "test_backend"

        mock_props = MagicMock()
        mock_props.qubits = [
            [MagicMock(name="readout_error", value=0.02)],
        ]
        mock_props.gates = []
        mock_props.last_update_date = "2024-01-01"
        mock_backend.properties.return_value = mock_props

        report = _extract_error_report(mock_backend, 1)

        assert report["mean_gate_error"] is None
        assert report["calibration_time"] == "2024-01-01"

    def test_extract_error_report_exception_handling(self):
        """Test extraction handles exceptions gracefully."""
        mock_backend = MagicMock()
        mock_backend.name = "test_backend"
        mock_backend.properties.side_effect = Exception("Props error")

        report = _extract_error_report(mock_backend, 2)

        assert report["backend_name"] == "test_backend"
        assert "error_extraction_failed" in report


class TestExperimentStorage:
    """Test experiment storage functions."""

    def test_get_experiment_not_in_memory(self):
        """Test getting experiment not in memory."""
        from app.quantum.experiments import _experiments
        _experiments.clear()

        result = get_experiment("NONEXISTENT")
        assert result is None

    @patch("app.core.database.get_quantum_job")
    @patch("app.core.database.list_quantum_jobs")
    def test_list_experiments_from_db(self, mock_list_jobs, mock_get_job):
        """Test listing experiments from database."""
        from app.quantum.experiments import _experiments
        _experiments.clear()

        mock_list_jobs.return_value = [
            {"job_id": "DB-1", "experiment_type": "qaoa", "qpu_backend": "ibm_fez", "status": "DONE", "created_at": "2024-01-01"},
            {"job_id": "DB-2", "experiment_type": "vqc", "qpu_backend": "simulator", "status": "COMPLETED", "created_at": "2024-01-02"},
        ]

        result = list_experiments()
        assert len(result) == 2
        assert result[0]["experiment_id"] == "DB-1"
        assert result[1]["experiment_id"] == "DB-2"

    @patch("app.core.database.list_quantum_jobs")
    @patch("app.core.database.get_quantum_job")
    def test_list_experiments_with_memory(self, mock_get_job, mock_list_jobs):
        """Test listing experiments with both memory and DB."""
        from app.quantum.experiments import _experiments
        _experiments.clear()
        _experiments["MEM-1"] = {"method": "test", "backend": "simulator", "status": "completed", "created_at": "2024-01-01"}

        mock_list_jobs.return_value = [
            {"job_id": "DB-1", "experiment_type": "qaoa", "qpu_backend": "ibm_fez", "status": "DONE", "created_at": "2024-01-01"},
        ]

        result = list_experiments()
        assert len(result) == 2
        # Memory experiment should be included
        exp_ids = [r["experiment_id"] for r in result]
        assert "MEM-1" in exp_ids
        assert "DB-1" in exp_ids