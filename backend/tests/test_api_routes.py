"""
Unit Tests — API Routes (Somesh's module)
==========================================
Tests for FastAPI routes: risk, portfolio, validation, quantum, AI.
"""

import numpy as np
import pandas as pd
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health(self):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


class TestRiskEndpoints:
    """Test risk analysis endpoints."""

    def test_risk_metrics_endpoint(self):
        with patch("app.api.v1.risk.compute_risk_metrics") as mock_compute:
            from app.core.schemas.risk import RiskMetricsResponse
            mock_compute.return_value = RiskMetricsResponse(
                annualized_volatility=0.15,
                annualized_return=0.12,
                sharpe_ratio=0.8,
                sortino_ratio=1.0,
                calmar_ratio=0.6,
                max_drawdown=-0.2,
                var_95=-0.03,
                cvar_95=-0.04,
                var_99=-0.05,
                cvar_99=-0.06,
                skewness=0.1,
                kurtosis=3.2,
                beta=1.1,
                alpha=0.02,
                treynor_ratio=0.07,
                tracking_error=0.05,
                information_ratio=0.4,
                upside_capture=1.2,
                downside_capture=1.1,
                tail_ratio=0.9,
                worst_days_pct=0.05,
                worst_day=-0.08,
                maximum_loss=-0.25,
                cvar=-0.04,
                avg_drawdown=-0.05,
                drawdown_duration=15,
                recovery_factor=0.6,
            )

            response = client.post(
                "/api/v1/risk/metrics",
                json={
                    "returns": [0.001] * 252,
                    "benchmark_returns": [0.0005] * 252,
                    "risk_free_rate": 0.05,
                },
            )
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
            assert "data" in data

    def test_var_endpoint(self):
        with patch("app.api.v1.risk.compute_var") as mock_var:
            from app.core.schemas.risk import VaRResponse
            mock_var.return_value = VaRResponse(
                confidence_level=0.95,
                var=-0.03,
                cvar=-0.04,
                method="historical",
            )

            response = client.post(
                "/api/v1/risk/var",
                json={
                    "returns": [0.001] * 252,
                    "confidence_level": 0.95,
                    "method": "historical",
                },
            )
            assert response.status_code == 200

    def test_monte_carlo_endpoint(self):
        with patch("app.api.v1.risk.run_monte_carlo") as mock_mc:
            from app.core.schemas.risk import MonteCarloResponse
            mock_mc.return_value = MonteCarloResponse(
                num_simulations=100,
                num_days=30,
                initial_value=100.0,
                final_values=[95.0, 100.0, 105.0],
                mean_final=100.0,
                std_final=5.0,
                percentile_5=90.0,
                percentile_25=97.0,
                percentile_50=100.0,
                percentile_75=103.0,
                percentile_95=110.0,
                prob_loss=0.3,
                prob_gain=0.7,
            )

            response = client.post(
                "/api/v1/risk/monte-carlo",
                json={
                    "returns": [0.001] * 252,
                    "initial_value": 100.0,
                    "num_days": 30,
                    "num_simulations": 100,
                },
            )
            assert response.status_code == 200

    def test_tail_risk_endpoint(self):
        with patch("app.api.v1.risk.compute_tail_risk") as mock_tail:
            from app.core.schemas.risk import TailRiskResponse
            mock_tail.return_value = TailRiskResponse(
                worst_days_pct=0.05,
                worst_day=-0.08,
                maximum_loss=-0.25,
                cvar=-0.04,
                avg_drawdown=-0.05,
                drawdown_duration=15,
                recovery_factor=0.6,
            )

            response = client.post(
                "/api/v1/risk/tail",
                json={
                    "returns": [0.001] * 252,
                    "benchmark_returns": [0.0005] * 252,
                },
            )
            assert response.status_code == 200


class TestPortfolioEndpoints:
    """Test portfolio endpoints."""

    def test_portfolio_optimize_endpoint(self):
        with patch("app.api.v1.portfolio.optimize_portfolio") as mock_opt:
            from app.core.schemas.portfolio import PortfolioResult
            mock_opt.return_value = PortfolioResult(
                symbols=["A", "B", "C"],
                weights=[0.33, 0.33, 0.34],
                expected_return=0.10,
                volatility=0.15,
                sharpe_ratio=0.67,
                correlation_matrix=[[1.0, 0.5, 0.3], [0.5, 1.0, 0.4], [0.3, 0.4, 1.0]],
                covariance_matrix=[[0.02, 0.01, 0.005], [0.01, 0.02, 0.006], [0.005, 0.006, 0.02]],
                effective_n=2.9,
                concentration=0.34,
            )

            response = client.post(
                "/api/v1/portfolio/optimize",
                json={
                    "returns": {"A": [0.001]*100, "B": [0.001]*100, "C": [0.001]*100},
                    "method": "max_sharpe",
                    "risk_free_rate": 0.05,
                },
            )
            assert response.status_code == 200

    def test_portfolio_allocate_endpoint(self):
        with patch("app.api.v1.portfolio.allocate_weights") as mock_alloc:
            mock_alloc.return_value = {"A": 0.33, "B": 0.33, "C": 0.34}

            response = client.post(
                "/api/v1/portfolio/allocate",
                json={
                    "returns": {"A": [0.001]*100, "B": [0.001]*100, "C": [0.001]*100},
                    "strategy": "equal_weight",
                },
            )
            assert response.status_code == 200


class TestValidationEndpoints:
    """Test validation endpoints."""

    def test_walk_forward_endpoint(self):
        with patch("app.api.v1.validation.walk_forward_validation") as mock_wf:
            from app.validation.walk_forward import WalkForwardResult
            result = WalkForwardResult()
            result.windows = [{"window_id": 0, "is_sharpe": 1.0, "oos_sharpe": 0.8, "oos_return": 0.1}]
            result.oos_returns = [0.1]
            result.oos_sharpes = [0.8]
            result.is_sharpes = [1.0]
            mock_wf.return_value = result

            response = client.post(
                "/api/v1/validation/walk-forward",
                json={
                    "returns": [0.001] * 252,
                    "strategy": "momentum",
                    "train_size": 100,
                    "test_size": 50,
                },
            )
            assert response.status_code == 200

    def test_purged_cv_endpoint(self):
        with patch("app.api.v1.validation.purged_kfold_cv") as mock_cv:
            from app.validation.purged_cv import PurgedCVResult
            result = PurgedCVResult()
            result.folds = [{"fold": 0, "oos_sharpe": 1.0, "oos_return": 0.1}]
            result.oos_sharpes = [1.0]
            result.oos_returns = [0.1]
            mock_cv.return_value = result

            response = client.post(
                "/api/v1/validation/purged-cv",
                json={
                    "returns": [0.001] * 252,
                    "strategy": "momentum",
                    "n_folds": 5,
                },
            )
            assert response.status_code == 200

    def test_deflated_sharpe_endpoint(self):
        with patch("app.api.v1.validation.deflated_sharpe_ratio") as mock_ds:
            mock_ds.return_value = {
                "deflated_sharpe": 0.8,
                "deflated_sharpe_p_value": 0.05,
                "is_significant": True,
            }

            response = client.post(
                "/api/v1/validation/deflated-sharpe",
                json={
                    "strategy_returns": [0.001] * 252,
                    "num_trials": 50,
                },
            )
            assert response.status_code == 200

    def test_reality_check_endpoint(self):
        with patch("app.api.v1.validation.whites_reality_check") as mock_rc:
            mock_rc.return_value = {"p_value": 0.05, "is_significant": True}

            response = client.post(
                "/api/v1/validation/reality-check",
                json={
                    "benchmark_returns": [0.0005] * 252,
                    "strategy_returns_matrix": {"s1": [0.001]*252, "s2": [0.0008]*252},
                },
            )
            assert response.status_code == 200

    def test_cost_stress_endpoint(self):
        with patch("app.api.v1.validation.cost_stress") as mock_cs:
            mock_cs.return_value = [
                {"cost_bps": 0, "sharpe": 1.0, "net_viable": True},
                {"cost_bps": 10, "sharpe": 0.8, "net_viable": True},
            ]

            response = client.post(
                "/api/v1/validation/cost-stress",
                json={
                    "returns": [0.001] * 252,
                    "trade_count": 50,
                },
            )
            assert response.status_code == 200


class TestQuantumEndpoints:
    """Test quantum endpoints."""

    def test_quantum_status_endpoint(self):
        with patch("app.api.v1.quantum.get_quantum_status") as mock_status:
            mock_status.return_value = {
                "available": True,
                "backend_name": "simulator",
                "simulator": True,
            }

            response = client.get("/api/v1/quantum/status")
            assert response.status_code == 200

    def test_quantum_backend_info_endpoint(self):
        with patch("app.api.v1.quantum.get_ibm_backend_info") as mock_info:
            mock_info.return_value = {"available": True, "backends": []}

            response = client.get("/api/v1/quantum/backend-info")
            assert response.status_code == 200

    def test_quantum_regime_detection_endpoint(self):
        with patch("app.api.v1.quantum.quantum_regime_detection") as mock_qrd:
            mock_qrd.return_value = {
                "status": "completed",
                "experiment_id": "QRD-test",
                "method": "pennylane_vqc",
                "backend": "default.qubit",
                "regimes": [],
            }

            response = client.post(
                "/api/v1/quantum/regime-detection",
                json={
                    "returns": [0.001] * 100,
                    "num_qubits": 4,
                    "epochs": 10,
                },
            )
            assert response.status_code == 200

    def test_quantum_portfolio_optimization_endpoint(self):
        with patch("app.api.v1.quantum.quantum_portfolio_optimization") as mock_qpo:
            mock_qpo.return_value = {
                "status": "completed",
                "experiment_id": "QPO-test",
                "method": "qaoa",
                "backend": "aer_simulator",
                "symbols": ["A", "B", "C"],
                "optimal_weights": [0.33, 0.33, 0.34],
                "selected_assets": ["A", "B"],
                "expected_return": 0.10,
                "volatility": 0.15,
                "sharpe_ratio": 0.67,
            }

            response = client.post(
                "/api/v1/quantum/portfolio-optimization",
                json={
                    "expected_returns": [0.1, 0.12, 0.08],
                    "cov_matrix": [[0.04, 0.01, 0.005], [0.01, 0.03, 0.008], [0.005, 0.008, 0.05]],
                    "symbols": ["A", "B", "C"],
                    "budget": 2,
                },
            )
            assert response.status_code == 200

    def test_quantum_job_status_endpoint(self):
        with patch("app.api.v1.quantum.get_quantum_job_status") as mock_job:
            mock_job.return_value = {
                "job_id": "test-job",
                "status": "DONE",
            }

            response = client.get("/api/v1/quantum/jobs/test-job")
            assert response.status_code == 200

    def test_list_experiments_endpoint(self):
        with patch("app.api.v1.quantum.list_experiments") as mock_list:
            mock_list.return_value = [
                {"experiment_id": "TEST-1", "experiment_type": "qaoa", "status": "completed"},
            ]

            response = client.get("/api/v1/quantum/experiments")
            assert response.status_code == 200


class TestAIEndpoints:
    """Test AI endpoints."""

    def test_ai_query_endpoint(self):
        with patch("app.api.v1.ai.research_query") as mock_query:
            mock_query.return_value = {
                "response": "Test response",
                "tools_called": [],
                "model": "gpt-oss-20b",
                "provider": "nvidia_nim",
            }

            response = client.post(
                "/api/v1/ai/query",
                json={"message": "What is Bitcoin?"},
            )
            assert response.status_code == 200

    def test_ai_explain_backtest_endpoint(self):
        with patch("app.api.v1.ai.explain_backtest") as mock_explain:
            mock_explain.return_value = "Backtest explanation"

            response = client.post(
                "/api/v1/ai/explain-backtest",
                json={"total_return": 0.15, "sharpe_ratio": 1.2},
            )
            assert response.status_code == 200


class TestCoinGeckoIntegration:
    """Test CoinGecko integration."""

    @pytest.mark.asyncio
    @patch("app.integrations.coingecko.coingecko_client.get_simple_price")
    async def test_get_simple_price(self, mock_get_price):
        from app.integrations.coingecko import coingecko_client
        mock_get_price.return_value = {"bitcoin": {"usd": 50000}}
        result = await coingecko_client.get_simple_price(["bitcoin"], ["usd"])
        assert "bitcoin" in result
        assert result["bitcoin"]["usd"] == 50000

    @pytest.mark.asyncio
    @patch("app.integrations.coingecko.coingecko_client.get_market_chart")
    async def test_get_market_chart(self, mock_get_chart):
        import pandas as pd
        import numpy as np
        from app.integrations.coingecko import coingecko_client

        df = pd.DataFrame({
            "price": np.array([50000, 51000]),
            "return": np.array([0.01, 0.02]),
        })
        mock_get_chart.return_value = df
        result = await coingecko_client.get_market_chart("bitcoin", "usd", 30)
        assert len(result) == 2

    @pytest.mark.asyncio
    @patch("app.integrations.coingecko.coingecko_client.get_trending")
    async def test_get_trending(self, mock_get_trending):
        from app.integrations.coingecko import coingecko_client
        mock_get_trending.return_value = [{"id": "bitcoin"}]
        result = await coingecko_client.get_trending()
        assert len(result) == 1


class TestDatabase:
    """Test database functions."""

    @pytest.mark.asyncio
    @patch("app.core.database.get_pool")
    async def test_save_quantum_job(self, mock_get_pool):
        from app.core.database import save_quantum_job
        mock_pool = AsyncMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_get_pool.return_value = mock_pool

        await save_quantum_job({"job_id": "test", "status": "DONE"})
        mock_conn.execute.assert_called()

    @pytest.mark.asyncio
    @patch("app.core.database.get_pool")
    async def test_get_quantum_job(self, mock_get_pool):
        from app.core.database import get_quantum_job
        mock_pool = AsyncMock()
        mock_conn = AsyncMock()
        mock_pool.acquire.return_value.__aenter__.return_value = mock_conn
        mock_conn.fetchrow.return_value = {"job_id": "test", "status": "DONE"}
        mock_get_pool.return_value = mock_pool

        result = await get_quantum_job("test")
        assert result is not None
        assert result["job_id"] == "test"