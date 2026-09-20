"""API load / stress handling: concurrency, throughput, latency, soak."""
import statistics
import time
from concurrent.futures import ThreadPoolExecutor

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

BASE = {"symbol": "NVDA", "start_date": "2024-01-01", "end_date": "2024-04-01"}
ENDPOINTS = [
    ("GET", "/api/v1/health", None),
    ("GET", "/api/v1/assets?page=1&page_size=10", None),
    ("GET", "/api/v1/assets/NVDA/history?start_date=2024-01-01&end_date=2024-03-01", None),
    ("POST", "/api/v1/indicators/sma", {**BASE, "period": 20}),
    ("POST", "/api/v1/indicators/volatility", {**BASE, "window": 20}),
    ("POST", "/api/v1/analytics/summary", {**BASE, "indicators": {"sma": [20], "ema": [20]}}),
    ("POST", "/api/v1/correlation/matrix", {"symbols": ["NVDA", "BTC-USD"], "start_date": "2024-01-01", "end_date": "2024-04-01"}),
]


def _call(spec):
    method, url, payload = spec
    t0 = time.perf_counter()
    try:
        if method == "GET":
            r = client.get(url)
        else:
            r = client.post(url, json=payload)
        ok = r.status_code == 200 and r.json().get("success") is True
        return ok, time.perf_counter() - t0, r.status_code
    except Exception:  # noqa: BLE001
        return False, time.perf_counter() - t0, 0


def test_burst_concurrency():
    """200 requests across 20 workers — no failures, bounded latency."""
    specs = [ENDPOINTS[i % len(ENDPOINTS)] for i in range(200)]
    with ThreadPoolExecutor(max_workers=20) as pool:
        results = list(pool.map(_call, specs))
    oks = [r for r in results if r[0]]
    lat = [r[1] for r in results]
    assert len(oks) == 200, f"failures: {200 - len(oks)}"
    assert statistics.mean(lat) < 5.0
    assert max(lat) < 15.0


def test_sustained_throughput():
    """Sequential soak: 100 mixed calls, measure req/s."""
    t0 = time.perf_counter()
    for i in range(100):
        ok, _, code = _call(ENDPOINTS[i % len(ENDPOINTS)])
        assert ok, f"call {i} failed with {code}"
    elapsed = time.perf_counter() - t0
    rps = 100 / elapsed
    assert rps > 2.0, f"throughput too low: {rps:.2f} req/s"
    print(f"\nthroughput: {rps:.2f} req/s over {elapsed:.1f}s")


def test_heavy_endpoint_under_load():
    """Heaviest payload (summary+correlation) x20 concurrent."""
    heavy = [
        ("POST", "/api/v1/analytics/summary", {**BASE, "indicators": {"sma": [20, 50], "ema": [20, 50]}}),
        ("POST", "/api/v1/correlation/matrix", {"symbols": ["NVDA", "BTC-USD", "GC=F"], "start_date": "2024-01-01", "end_date": "2024-06-01"}),
    ] * 10
    with ThreadPoolExecutor(max_workers=10) as pool:
        results = list(pool.map(_call, heavy))
    assert all(r[0] for r in results)
    p95 = sorted(r[1] for r in results)[int(len(results) * 0.95) - 1]
    assert p95 < 15.0, f"p95 latency too high: {p95:.2f}s"
