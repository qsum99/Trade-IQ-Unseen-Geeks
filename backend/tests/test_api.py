from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health():
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["data"]["status"] == "healthy"


def test_assets_and_history():
    r = client.get("/api/v1/assets?asset_class=crypto")
    assert r.status_code == 200
    assert any(a["symbol"] == "BTC-USD" for a in r.json()["data"])
    r = client.get("/api/v1/assets/NVDA/history?start_date=2024-01-01&end_date=2024-03-01")
    assert r.status_code == 200
    assert len(r.json()["data"]["data"]) > 20


def test_indicators_and_correlation():
    assert client.post("/api/v1/indicators/sma", json={"symbol": "NVDA", "start_date": "2024-01-01", "end_date": "2024-04-01", "period": 20}).status_code == 200
    assert client.post("/api/v1/indicators/sharpe", json={"symbol": "NVDA", "start_date": "2024-01-01", "end_date": "2024-06-01"}).status_code == 200
    assert client.post("/api/v1/analytics/summary", json={"symbol": "NVDA", "start_date": "2024-01-01", "end_date": "2024-04-01"}).status_code == 200
    r = client.post("/api/v1/correlation/matrix", json={"symbols": ["NVDA", "BTC-USD"], "start_date": "2024-01-01", "end_date": "2024-04-01"})
    assert r.status_code == 200
    assert r.json()["data"]["matrix"][0][0] == 1.0
    assert client.post("/api/v1/data/validate", json={"symbol": "NVDA", "start_date": "2024-01-01", "end_date": "2024-04-01"}).status_code == 200
