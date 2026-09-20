"""Satish x Samarth integration: data -> strategies -> backtests over HTTP."""
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

PERIOD = {"start_date": "2024-01-01", "end_date": "2024-03-01"}


def test_strategies_catalog():
    r = client.get("/api/v1/strategies")
    assert r.status_code == 200
    ids = {s["id"] for s in r.json()["data"]}
    assert {"sma_crossover", "ema_trend", "momentum", "mean_reversion", "regime_adaptive"} <= ids


def test_signals_end_to_end():
    r = client.post("/api/v1/strategies/signals", json={
        "symbol": "NVDA", "strategy": "sma_crossover",
        "parameters": {"fast_period": 5, "slow_period": 15}, **PERIOD})
    assert r.status_code == 200, r.text
    assert len(r.json()["data"]["signals"]) > 20


def test_signals_unknown_is_404():
    r = client.post("/api/v1/strategies/signals", json={
        "symbol": "NVDA", "strategy": "nope", "parameters": {}, **PERIOD})
    assert r.status_code == 404
    assert r.json()["success"] is False


def test_signals_bad_params_is_422():
    r = client.post("/api/v1/strategies/signals", json={
        "symbol": "NVDA", "strategy": "sma_crossover",
        "parameters": {"fast_period": 50, "slow_period": 5}, **PERIOD})
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "STRATEGY_FAILED"


def test_regime_adaptive_needs_timeline():
    r = client.post("/api/v1/strategies/regime-adaptive", json={"symbol": "NVDA", **PERIOD})
    assert r.status_code == 422  # regime detection lands with Somesh


def test_regime_adaptive_with_timeline():
    n = len(client.get("/api/v1/assets/NVDA/history?start_date=2024-01-01&end_date=2024-02-01").json()["data"]["data"])
    r = client.post("/api/v1/strategies/regime-adaptive", json={
        "symbol": "NVDA", "regime_model": "kmeans",
        "mapping": {"bull": "momentum", "bear": "mean_reversion"},
        "strategy_params": {"momentum": {"lookback": 2, "threshold": 0.001},
                            "mean_reversion": {"lookback": 3, "entry_z": 0.5}},
        "regime_timeline": ["bull"] * (n // 2) + ["bear"] * (n - n // 2),
        "start_date": "2024-01-01", "end_date": "2024-02-01"})
    assert r.status_code == 200, r.text
    assert len(r.json()["data"]["signals"]) == n


def test_bridge_helpers():
    from unittest.mock import patch

    from app.api.v1._samarth_bridge import http_status_for, known_strategy_ids

    assert http_status_for("NOT_FOUND") == 404
    assert http_status_for("STRATEGY_NOT_FOUND") == 404
    assert http_status_for("INVALID_PARAMETER") == 422
    assert http_status_for("BACKTEST_FAILED") == 500
    assert "sma_crossover" in known_strategy_ids()
    with patch("app.samarth_work.api_logic.strategies_api.list_strategies", side_effect=ValueError("down")):
        assert known_strategy_ids() == set()


def test_backtest_full_lifecycle():
    run = client.post("/api/v1/backtests", json={
        "name": "NVDA SMA 5/15", "symbol": "NVDA",
        "strategy": {"type": "sma_crossover", "parameters": {"fast_period": 5, "slow_period": 15}},
        "period": PERIOD,
        "capital": {"initial": 100000, "position_sizing": "full"},
        "execution": {"transaction_cost": 0.001, "slippage": 0.0005, "execution_price": "next_open"},
        "benchmark": "buy_and_hold"})
    assert run.status_code == 200, run.text
    bid = run.json()["data"]["backtest_id"]
    assert run.json()["data"]["benchmark"]["compare"]["excess_return"] is not None

    for tail in ["", "/equity", "/trades", "/metrics", "/benchmark", "/trust-report"]:
        r = client.get(f"/api/v1/backtests/{bid}{tail}")
        assert r.status_code == 200, tail
    assert client.get("/api/v1/backtests/bt_missing").status_code == 404
    assert bid in client.get("/api/v1/backtests").json()["data"]["backtest_ids"]
    trust = client.get(f"/api/v1/backtests/{bid}/trust-report").json()["data"]
    assert trust["overall"] in ("pass", "review", "fail")
