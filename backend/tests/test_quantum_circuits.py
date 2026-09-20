"""
Unit Tests — Quantum Circuits (Somesh's module)
=================================================
Tests for quantum circuit building and hardware transpilation.
"""

import pytest
from unittest.mock import MagicMock, patch

from app.quantum.circuits import (
    build_portfolio_hamiltonian,
    build_portfolio_qaoa_circuit,
    build_regime_vqc_circuit,
    build_bell_benchmark_circuit,
    transpile_for_ibm_hardware,
    decode_qaoa_measurements,
)


class TestBuildBellBenchmarkCircuit:
    """Test Bell state benchmark circuit."""

    def test_build_bell_benchmark_circuit(self):
        qc = build_bell_benchmark_circuit()
        assert qc.num_qubits == 2
        assert qc.name == "bell_benchmark"
        # Check it has H, CX, and measurements
        ops = qc.count_ops()
        assert "h" in ops
        assert "cx" in ops
        assert "measure" in ops


class TestTranspileForIBMHardware:
    """Test hardware transpilation."""

    @patch("app.quantum.circuits.generate_preset_pass_manager")
    def test_transpile_for_ibm_hardware(self, mock_pass_manager):
        mock_backend = MagicMock()
        mock_backend.name = "ibm_fez"

        mock_pm = MagicMock()
        mock_isa_circuit = MagicMock()
        mock_isa_circuit.depth.return_value = 50
        mock_isa_circuit.count_ops.return_value = {"rz": 20, "sx": 15, "cx": 10}
        mock_isa_circuit.num_qubits = 4
        mock_pm.run.return_value = mock_isa_circuit
        mock_pass_manager.return_value = mock_pm

        circuit = MagicMock()
        isa_circuit, metrics = transpile_for_ibm_hardware(circuit, mock_backend, optimization_level=2)

        assert isa_circuit == mock_isa_circuit
        assert metrics["isa_depth"] == 50
        assert metrics["isa_ops"] == {"rz": 20, "sx": 15, "cx": 10}
        assert metrics["physical_qubits_allocated"] == 4
        assert metrics["backend_name"] == "ibm_fez"
        assert metrics["optimization_level"] == 2

    @patch("app.quantum.circuits.generate_preset_pass_manager")
    def test_transpile_for_ibm_hardware_default_optimization(self, mock_pass_manager):
        """Test with default optimization level."""
        mock_backend = MagicMock()
        mock_backend.name = "ibm_brisbane"

        mock_pm = MagicMock()
        mock_isa_circuit = MagicMock()
        mock_isa_circuit.depth.return_value = 30
        mock_isa_circuit.count_ops.return_value = {"rz": 10, "sx": 5}
        mock_isa_circuit.num_qubits = 2
        mock_pm.run.return_value = mock_isa_circuit
        mock_pass_manager.return_value = mock_pm

        circuit = MagicMock()
        isa_circuit, metrics = transpile_for_ibm_hardware(circuit, mock_backend)

        assert metrics["optimization_level"] == 1


class TestDecodeQAOAMeasurements:
    """Test QAOA measurement decoding."""

    def test_decode_qaoa_measurements_basic(self):
        counts = {"0011": 100, "1100": 50, "0101": 30, "1010": 20}
        symbols = ["A", "B", "C", "D"]
        budget = 2
        expected_returns = np.array([0.1, 0.12, 0.08, 0.15])
        cov_matrix = np.eye(4) * 0.04
        risk_factor = 0.5

        result = decode_qaoa_measurements(
            counts=counts,
            symbols=symbols,
            budget=budget,
            expected_returns=expected_returns,
            cov_matrix=cov_matrix,
            risk_factor=risk_factor,
        )

        assert "selected_assets" in result
        assert "optimal_weights" in result
        assert "budget_compliance_rate" in result
        assert "best_bitstring" in result

    def test_decode_qaoa_measurements_empty_counts(self):
        """Test with empty counts."""
        result = decode_qaoa_measurements(
            counts={"00": 10, "11": 5},
            symbols=["A", "B"],
            budget=1,
            expected_returns=np.array([0.1, 0.12]),
            cov_matrix=np.eye(2) * 0.04,
            risk_factor=0.5,
        )

        assert "selected_assets" in result
        assert "optimal_weights" in result


# Need to import numpy
import numpy as np