"""
API v1 Router Aggregator
========================
Combines our domain routers under the /api/v1 prefix.
"""

from __future__ import annotations

from fastapi import APIRouter

from app.api.v1.health import router as health_router
from app.api.v1.assets import router as assets_router
from app.api.v1.analytics import router as analytics_router

api_v1_router = APIRouter()

api_v1_router.include_router(health_router)
api_v1_router.include_router(assets_router)
api_v1_router.include_router(analytics_router)

__all__ = ["api_v1_router"]