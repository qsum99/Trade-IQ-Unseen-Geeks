"""In-memory backtest result store (work_divide §20 GET endpoints).

Holds completed run payloads so equity/trades/metrics/benchmark/trust
can be fetched individually. Process-local only — the FastAPI service
layer will replace this with PostgreSQL without changing getter names.
Stdlib only.
"""
from __future__ import annotations

_STORE: dict[str, dict] = {}


def save(backtest_id: str, payload: dict) -> None:
    _STORE[backtest_id] = payload


def get(backtest_id: str) -> dict | None:
    return _STORE.get(backtest_id)


def list_ids() -> list[str]:
    return list(_STORE.keys())


def clear() -> None:
    _STORE.clear()
