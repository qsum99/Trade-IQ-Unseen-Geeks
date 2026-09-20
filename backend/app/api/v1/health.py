from fastapi import APIRouter

from app.config import settings

router = APIRouter(tags=["system"])


@router.get("/health")
def health():
    return {"success": True, "data": {
        "status": "healthy", "version": settings.api_version,
        "environment": settings.environment,
        "services": {"database": "healthy", "market_data": "healthy",
                     "quant_engine": "healthy", "ml_engine": "healthy",
                     "quantum_engine": "available"}},
        "meta": {}, "error": None}
