from fastapi import APIRouter

from app.data import service as data_service
from app.integrations import market_api

router = APIRouter(tags=["assets"])


@router.get("/assets")
def list_assets(asset_class: str | None = None, search: str | None = None,
               page: int = 1, page_size: int = 25):
    assets = market_api.get_supported_assets(asset_class, search)
    total = len(assets)
    start, end = (page - 1) * page_size, page * page_size
    return {"success": True,
            "data": [a.model_dump() for a in assets[start:end]],
            "meta": {"page": page, "page_size": page_size, "total": total},
            "error": None}


@router.get("/assets/{symbol}/history")
def asset_history(symbol: str, start_date: str = "2024-01-01",
                 end_date: str = "2025-01-01", interval: str = "1d"):
    _, clean = data_service.get_clean_history(symbol, start_date, end_date, interval)
    rows = clean.to_dict(orient="records")
    for r in rows:
        r["timestamp"] = r["timestamp"].isoformat()
    asset = market_api.validate_symbol(symbol)
    return {"success": True, "data": {
        "symbol": symbol, "interval": interval,
        "currency": asset.currency, "data": rows}, "meta": {}, "error": None}
