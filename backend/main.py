"""
Development Entrypoint
======================
Run this file directly with:
    python main.py
or with uv:
    uv run uvicorn app.main:app --reload --port 8000
"""

import uvicorn
from app.config import settings

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="info",
    )
