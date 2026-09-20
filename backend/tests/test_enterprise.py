"""
Enterprise & Institutional-Grade Test Suite
============================================
Tests:
1. TTLCache & CoinGecko Caching
2. PostgreSQL Schema & DAO Persistence (quantum_jobs, portfolio_optimizations, risk_assessments)
3. IBM Quantum Asynchronous Job Status Polling & Endpoint
4. Observability Middleware (X-Request-ID, X-Process-Time)
"""

import time
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.integrations.coingecko import TTLCache, CoinGeckoClient
from app.core.database import (
    init_database as init_db_schema,
    save_quantum_job,
    get_quantum_job,
    list_quantum_jobs,
    save_portfolio_run,
    save_risk_assessment,
)
from app.quantum.experiments import get_quantum_job_status


@pytest.fixture
def client():
    return TestClient(app)


def test_ttl_cache_operations():
    """Verify in-memory TTL cache expiration and eviction."""
    cache = TTLCache()
    cache.set("test_key", {"price": 100}, ttl_seconds=0.1)

    # Immediate hit
    assert cache.get("test_key") == {"price": 100}

    # After expiration
    time.sleep(0.15)
    assert cache.get("test_key") is None


@pytest.mark.asyncio
async def test_coingecko_client_caching():
    """Verify CoinGecko client caches responses to prevent 429 rate limits."""
    mock_cache = TTLCache()
    client = CoinGeckoClient(cache=mock_cache)

    # Seed cache
    mock_cache.set("price:bitcoin:usd", {"bitcoin": {"usd": 85000.0}}, ttl_seconds=10.0)

    # Should hit cache without making HTTP request
    result = await client.get_simple_price(["bitcoin"], ["usd"])
    assert result == {"bitcoin": {"usd": 85000.0}}


def test_database_persistence_crud():
    """Verify PostgreSQL schema initialization and DAO operations."""
    # 1. Initialize schema
    assert init_db_schema() is True

    # 2. Save and retrieve quantum job
    job_id = f"test_job_{int(time.time())}"
    job_data = {
        "job_id": job_id,
        "experiment_type": "bell_state_test",
        "qpu_backend": "ibm_fez",
        "num_qubits": 2,
        "shots": 512,
        "status": "QUEUED",
        "circuit_depth": 8,
        "error_report": {"mean_readout_error": 0.019},
        "result_counts": {"00": 260, "11": 252},
        "fidelity": 0.98,
    }
    assert save_quantum_job(job_data) is True

    retrieved = get_quantum_job(job_id)
    assert retrieved is not None
    assert retrieved["job_id"] == job_id
    assert retrieved["qpu_backend"] == "ibm_fez"
    assert retrieved["status"] == "QUEUED"
    assert retrieved["fidelity"] == 0.98

    # 3. List quantum jobs
    jobs = list_quantum_jobs(limit=5)
    assert len(jobs) >= 1
    assert any(j["job_id"] == job_id for j in jobs)

    # 4. Save portfolio run
    port_data = {
        "id": f"port_{int(time.time())}",
        "method": "max_sharpe",
        "symbols": ["BTC", "ETH"],
        "weights": {"BTC": 0.6, "ETH": 0.4},
        "expected_return": 0.35,
        "volatility": 0.22,
        "sharpe_ratio": 1.59,
    }
    assert save_portfolio_run(port_data) is True

    # 5. Save risk assessment
    risk_data = {
        "id": f"risk_{int(time.time())}",
        "var_historical_95": -0.045,
        "var_parametric_95": -0.042,
        "cvar_95": -0.062,
        "max_drawdown": -0.15,
        "sharpe_ratio": 1.45,
        "sortino_ratio": 2.1,
        "metrics": {"calmar": 2.33},
    }
    assert save_risk_assessment(risk_data) is True


def test_quantum_job_status_and_endpoint(client):
    """Verify asynchronous quantum job polling and API endpoint."""
    test_job_id = f"qjob_poll_{int(time.time())}"
    job_data = {
        "job_id": test_job_id,
        "experiment_type": "vqc_regime",
        "qpu_backend": "ibm_fez",
        "num_qubits": 4,
        "shots": 1024,
        "status": "DONE",
        "circuit_depth": 12,
        "result_counts": {"0000": 510, "1111": 514},
        "fidelity": 0.99,
    }
    save_quantum_job(job_data)

    # Query via service function
    status = get_quantum_job_status(test_job_id)
    assert status["job_id"] == test_job_id
    assert status["status"] == "DONE"

    # Query via API endpoint
    response = client.get(f"/api/v1/quantum/jobs/{test_job_id}")
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["job_id"] == test_job_id
    assert data["status"] == "DONE"
    assert data["fidelity"] == 0.99


def test_observability_middleware_headers(client):
    """Verify X-Request-ID and X-Process-Time headers on all API responses."""
    response = client.get("/health")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    assert "X-Process-Time" in response.headers
    assert response.headers["X-Process-Time"].endswith("ms")

    # Custom request ID propagation
    custom_id = "institutional-req-12345"
    response2 = client.get("/health", headers={"X-Request-ID": custom_id})
    assert response2.headers["X-Request-ID"] == custom_id
