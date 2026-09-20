"""FastAPI entrypoint — Satish foundation + Samarth strategies/backtests."""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.api.v1 import analytics, assets, backtests, health, strategies, risk, portfolio, quantum, ai, validation, paper_trading, news, whatsapp
from app.core.exceptions import AppError

# Rate limiter
limiter = Limiter(key_func=get_remote_address, default_limits=["100/minute"])

app = FastAPI(title="Quant Platform API", version="1.0.0",
              docs_url="/docs", openapi_url="/openapi.json")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True,
                   allow_methods=["*"], allow_headers=["*"])


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    rid = request.headers.get("X-Request-ID", "req_unknown")
    return JSONResponse(status_code=exc.status, content={
        "success": False, "data": None, "meta": {"request_id": rid},
        "error": {"code": exc.code, "message": exc.message, "details": exc.details}})


@app.middleware("http")
async def add_request_id(request: Request, call_next):
    import uuid
    rid = request.headers.get("X-Request-ID", f"req_{uuid.uuid4().hex[:8]}")
    resp = await call_next(request)
    resp.headers["X-Request-ID"] = rid
    return resp


app.include_router(health.router, prefix="/api/v1")
app.include_router(assets.router, prefix="/api/v1")
app.include_router(analytics.router, prefix="/api/v1")
app.include_router(strategies.router, prefix="/api/v1")
app.include_router(backtests.router, prefix="/api/v1")
app.include_router(risk.router, prefix="/api/v1")
app.include_router(portfolio.router, prefix="/api/v1")
app.include_router(quantum.router, prefix="/api/v1")
app.include_router(ai.router, prefix="/api/v1")
app.include_router(validation.router, prefix="/api/v1")
app.include_router(paper_trading.router, prefix="/api/v1")
app.include_router(paper_trading.router)
app.include_router(news.router, prefix="/api/v1")
app.include_router(whatsapp.router, prefix="/api/v1")

# Compatibility exports
get_candles = paper_trading.get_candles
get_latest_tick = paper_trading.get_latest_tick
run_paper_trading = paper_trading.run_paper_trading



@app.get("/")
def root():
    return {"success": True, "data": {"name": "Quant Platform API", "version": "1.0.0"}, "meta": {}, "error": None}
