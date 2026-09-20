from fastapi import APIRouter

from app.analytics import correlation as C
from app.analytics import indicators as I
from app.analytics import performance as P
from app.core.schemas.analytics import (
    AnalyticsSummaryRequest,
    CorrelationMatrixRequest,
    DataValidateRequest,
    IndicatorRequest,
    RollingCorrelationRequest,
)
from app.data import service as data_service

router = APIRouter(tags=["analytics"])


@router.post("/data/validate")
def validate(req: DataValidateRequest):
    return {"success": True, "data": data_service.get_quality(
        req.symbol, req.start_date, req.end_date, req.provider), "meta": {}, "error": None}


@router.post("/indicators/sma")
def sma(req: IndicatorRequest):
    return {"success": True, "data": I.sma_points(req.symbol, req.start_date, req.end_date, req.period), "meta": {}, "error": None}


@router.post("/indicators/ema")
def ema(req: IndicatorRequest):
    return {"success": True, "data": I.ema_points(req.symbol, req.start_date, req.end_date, req.period), "meta": {}, "error": None}


@router.post("/indicators/returns")
def rets(req: IndicatorRequest):
    return {"success": True, "data": I.returns_summary(req.symbol, req.start_date, req.end_date, req.method), "meta": {}, "error": None}


@router.post("/indicators/volatility")
def vol(req: IndicatorRequest):
    return {"success": True, "data": I.volatility_summary(req.symbol, req.start_date, req.end_date, req.window, req.annualization_factor), "meta": {}, "error": None}


@router.post("/indicators/sharpe")
def sharpe(req: IndicatorRequest):
    return {"success": True, "data": I.sharpe_summary(req.symbol, req.start_date, req.end_date, req.risk_free_rate, req.annualization_factor), "meta": {}, "error": None}


@router.post("/indicators/drawdown")
def dd(req: IndicatorRequest):
    return {"success": True, "data": I.drawdown_summary(req.symbol, req.start_date, req.end_date), "meta": {}, "error": None}


@router.post("/analytics/summary")
def summary(req: AnalyticsSummaryRequest):
    return {"success": True, "data": P.summary(req.symbol, req.start_date, req.end_date, req.indicators), "meta": {}, "error": None}


@router.post("/correlation/matrix")
def corr_matrix(req: CorrelationMatrixRequest):
    return {"success": True, "data": C.matrix(req.symbols, req.start_date, req.end_date, req.method), "meta": {}, "error": None}


@router.post("/correlation/rolling")
def corr_rolling(req: RollingCorrelationRequest):
    return {"success": True, "data": C.rolling(req.symbols, req.window, req.start_date, req.end_date), "meta": {}, "error": None}
