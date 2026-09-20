"""Satish-compatible formula stubs (work_divide §4).

Real implementation lives in quantum-hackthon/backend/app/quant/formulas.py.
Signatures here are FROZEN — do not change. Samarth's code imports from here.
Stdlib only (offline env).
"""
from __future__ import annotations


def sma_series(prices: list[float], n: int) -> list[float | None]:
    if n < 2:
        raise ValueError("SMA period must be >= 2")
    out: list[float | None] = [None] * len(prices)
    acc = 0.0
    for i, p in enumerate(prices):
        acc += p
        if i >= n:
            acc -= prices[i - n]
        if i >= n - 1:
            out[i] = acc / n
    return out


def ema_series(prices: list[float], n: int) -> list[float | None]:
    if n < 2:
        raise ValueError("EMA period must be >= 2")
    if not prices:
        return []
    alpha = 2.0 / (n + 1)
    out: list[float | None] = [None] * len(prices)
    # Seed with SMA(n) at index n-1 (standard)
    if len(prices) >= n:
        seed = sum(prices[:n]) / n
        out[n - 1] = seed
        prev = seed
        for i in range(n, len(prices)):
            prev = alpha * prices[i] + (1 - alpha) * prev
            out[i] = prev
    return out


def momentum(prices: list[float], n: int) -> list[float | None]:
    out: list[float | None] = [None] * len(prices)
    for i in range(n, len(prices)):
        base = prices[i - n]
        out[i] = (prices[i] / base - 1.0) if base else None
    return out


def zscore(values: list[float]) -> list[float | None]:
    n = len(values)
    if n < 2:
        return [None] * n
    mean = sum(values) / n
    var = sum((v - mean) ** 2 for v in values) / (n - 1)
    sd = var ** 0.5
    if sd == 0:
        return [0.0] * n
    return [(v - mean) / sd for v in values]


def position_size(capital: float, risk_fraction: float, stop_distance: float) -> float:
    if capital <= 0 or risk_fraction <= 0 or stop_distance <= 0:
        raise ValueError("capital, risk_fraction, stop_distance must be > 0")
    return (capital * risk_fraction) / stop_distance
