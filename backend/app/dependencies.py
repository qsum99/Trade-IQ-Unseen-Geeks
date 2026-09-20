"""Shared FastAPI dependencies (request id, pagination)."""
from __future__ import annotations

import uuid

from fastapi import Request


def get_request_id(request: Request) -> str:
    return request.headers.get("X-Request-ID", f"req_{uuid.uuid4().hex[:8]}")
