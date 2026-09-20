"""API Endpoints for Real-Time Live Financial News."""
from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Query

from app.services.news_service import get_live_news, get_breaking_news, clear_cache

router = APIRouter(prefix="/news", tags=["news"])


@router.get("")
def list_news(
    category: str = Query(default="all", description="Category: all, macro, crypto, equities, india"),
    symbol: Optional[str] = Query(default=None, description="Optional asset symbol (e.g., AAPL, NVDA, BTC)"),
    limit: int = Query(default=25, ge=1, le=100, description="Max news articles to return")
):
    """Retrieve real-time authenticated financial news with sentiment and asset tags."""
    items = get_live_news(category=category, symbol=symbol, limit=limit)
    return {
        "success": True,
        "data": items,
        "meta": {
            "category": category,
            "symbol": symbol,
            "count": len(items),
            "source": "live_financial_wire"
        },
        "error": None
    }


@router.get("/breaking")
def breaking_news(
    limit: int = Query(default=6, ge=1, le=20, description="Number of breaking headlines for nav ticker")
):
    """Retrieve fast breaking headlines specifically for the top navbar ticker."""
    items = get_breaking_news(limit=limit)
    return {
        "success": True,
        "data": items,
        "meta": {
            "count": len(items),
            "timestamp": "live"
        },
        "error": None
    }


@router.post("/refresh")
def force_refresh_news():
    """Invalidate news cache and fetch fresh wire updates."""
    clear_cache()
    fresh_items = get_live_news(category="all", limit=25)
    return {
        "success": True,
        "data": {
            "message": "News cache refreshed successfully",
            "items_count": len(fresh_items)
        },
        "meta": {},
        "error": None
    }
