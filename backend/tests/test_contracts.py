"""Contract + branch coverage: market_api, schemas, exceptions, middleware, all endpoints."""
from unittest.mock import patch

import pandas as pd
from fastapi.testclient import TestClient

from app.config import settings
from app.core import constants
from app.core.exceptions import AppError, AssetNotFound, InsufficientData, ProviderError
from app.core.schemas.common import ERROR_CODES, APIResponse, ErrorDetail, ErrorResponse
from app.core.schemas.market import SUPPORTED_ASSETS, Asset, DataQualityReport
from app.dependencies import get_request_id
from app.integrations import market_api
from app.main import app

client = TestClient(app)


def _df(symbol="NVDA"):
    return market_api._synthetic_history(symbol, "2024-01-01", "2024-02-15")


def test_constants_and_settings():
    assert constants.API_VERSION == "1.0.0"
    assert constants.DEFAULT_ANNUALIZATION_EQUITY == 252
    assert constants.DEFAULT_ANNUALIZATION_CRYPTO == 365
    assert settings.app_name == "Quant Platform API"


def test_common_schemas():
    ok = APIResponse(data={"a": 1}, meta={"request_id": "r"})
    assert ok.success is True
    err = ErrorResponse(data=None, meta={}, error=ErrorDetail(code="X", message="m"))
    assert err.success is False
    assert "ASSET_NOT_FOUND" in ERROR_CODES


def test_exceptions_model():
    e = AppError("INVALID_PARAMETER", "bad", {"f": "x"}, 422)
    assert (e.code, e.status) == ("INVALID_PARAMETER", 422)
    assert AssetNotFound("ZZZ").status == 404
    assert InsufficientData(252, 10).status == 422
    assert ProviderError("yahoo", "down").status == 503


def test_dependencies_request_id():
    assert get_request_id(type("H", (), {"headers": {"X-Request-ID": "req_abc"}})()) == "req_abc"
    assert get_request_id(type("H2", (), {"headers": {}})()).startswith("req_")


def test_market_api_filters_and_ad_hoc():
    assert len(market_api.client.get_supported_assets("crypto")) >= 1
    assert len(market_api.client.get_supported_assets(search="nvidia")) >= 1
    assert len(market_api.client.get_supported_assets("nope")) == 0
    assert market_api.client.validate_symbol("NVDA").symbol == "NVDA"
    ad = market_api.client.validate_symbol("CUSTOM.X")
    assert ad.symbol == "CUSTOM.X"
    q = market_api.client.get_quote("NVDA")
    assert set(q) == {"symbol", "price", "currency", "timestamp"}
    bench = market_api.client.get_benchmark_history("2024-01-01", "2024-02-01")
    assert len(bench) > 10
    # convenience wrappers
    assert len(market_api.get_history("NVDA", "2024-01-01", "2024-02-01")) > 10
    assert market_api.get_latest_price("NVDA").symbol == "NVDA"
    assert market_api.get_quote("NVDA")["symbol"] == "NVDA"
    assert len(market_api.get_supported_assets()) == len(SUPPORTED_ASSETS)
    assert market_api.validate_symbol("NVDA").symbol == "NVDA"
    assert len(market_api.get_benchmark_history("2024-01-01", "2024-02-01")) > 0


def test_market_api_yahoo_branches():
    import builtins
    real_import = builtins.__import__

    def fake_import(name, *a, **k):
        if name == "yfinance":
            raise ImportError("no yf")
        return real_import(name, *a, **k)

    with patch("builtins.__import__", side_effect=fake_import):
        assert market_api._try_yahoo("NVDA", "2024-01-01", "2024-02-01") is None
    # exception branch (bad download)
    with patch("yfinance.download", side_effect=ValueError("boom")):
        assert market_api._try_yahoo("NVDA", "2024-01-01", "2024-02-01") is None
    # empty download -> None
    with patch("yfinance.download", return_value=pd.DataFrame()):
        assert market_api._try_yahoo("NVDA", "2024-01-01", "2024-02-01") is None
    # AssetNotFound when both layers empty
    with patch("app.integrations.market_api._try_yahoo", return_value=None), patch("app.integrations.market_api._synthetic_history", return_value=pd.DataFrame()):
        try:
            market_api.client.get_history("EMPTY", "2024-01-01", "2024-02-01")
            raise AssertionError("should raise")
        except AssetNotFound:
            pass


def test_all_endpoints_covered():
    base = {"symbol": "NVDA", "start_date": "2024-01-01", "end_date": "2024-04-01"}
    for ep in ["sma", "ema", "returns", "volatility", "sharpe", "drawdown"]:
        r = client.post(f"/api/v1/indicators/{ep}", json={**base, "period": 10, "window": 10, "method": "log"})
        assert r.status_code == 200, ep
    r = client.post("/api/v1/analytics/summary", json={**base, "indicators": {"sma": [10], "ema": [10]}})
    assert r.status_code == 200
    r = client.post("/api/v1/correlation/rolling", json={"symbols": ["NVDA", "BTC-USD"], "window": 10, **{k: base[k] for k in ("start_date", "end_date")}})
    assert r.status_code == 200 and len(r.json()["data"]["series"]) > 0
    # single-symbol rolling branch
    r = client.post("/api/v1/correlation/rolling", json={"symbols": ["NVDA"], "window": 10, "start_date": "2024-01-01", "end_date": "2024-04-01"})
    assert r.json()["data"]["series"] == []
    # assets pagination + search + history + root + request id echo
    assert client.get("/api/v1/assets?page=1&page_size=2").json()["meta"]["page_size"] == 2
    assert client.get("/api/v1/assets?search=nvidia").status_code == 200
    assert client.get("/").json()["success"] is True
    r = client.get("/api/v1/health", headers={"X-Request-ID": "req_test123"})
    assert r.headers["X-Request-ID"] == "req_test123"
    assert "X-Request-ID" in client.get("/api/v1/health").headers


def test_error_handler_and_quality_model():
    import asyncio

    from app.main import app_error_handler

    resp = asyncio.run(app_error_handler(type("R", (), {"headers": {}})(), AssetNotFound("ZZZ")))
    assert resp.status_code == 404
    rep = DataQualityReport(symbol="X", records=10, missing_values=1, duplicate_records=0, invalid_prices=0, date_gaps=0, quality_score=90.0)
    assert rep.quality_score == 90.0
    a = Asset(symbol="T", name="T")
    assert a.active is True


def test_normalization_empty_and_gaps():
    from app.data import normalization as N
    assert N.normalize(pd.DataFrame()).empty
    df = _df()
    rep = N.quality_report(df, df, "NVDA")
    assert rep.records == len(df)
