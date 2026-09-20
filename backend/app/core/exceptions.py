"""Central exceptions with error codes."""
from __future__ import annotations


class AppError(Exception):
    def __init__(self, code: str, message: str, details: dict | None = None, status: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}
        self.status = status


class AssetNotFound(AppError):
    def __init__(self, symbol: str):
        super().__init__("ASSET_NOT_FOUND", f"Asset {symbol} not found", {"symbol": symbol}, 404)


class InsufficientData(AppError):
    def __init__(self, required: int, available: int):
        super().__init__(
            "INSUFFICIENT_DATA",
            f"At least {required} records required, got {available}",
            {"required": required, "available": available},
            422,
        )


class ProviderError(AppError):
    def __init__(self, provider: str, message: str):
        super().__init__("DATA_PROVIDER_ERROR", message, {"provider": provider}, 503)
