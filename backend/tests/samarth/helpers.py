"""Shared fixtures for Samarth unit tests (stdlib only)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "app"))

CLOSES = [100, 101, 102, 103, 105, 104, 102, 99, 97, 96, 98, 100, 103, 107, 106]


def make_bars(closes=None):
    """Plain-dict bars (benchmark/costs/api paths)."""
    closes = list(CLOSES if closes is None else closes)
    bars = []
    for i, c in enumerate(closes):
        bars.append(
            {
                "date": f"2024-01-{i + 1:02d}",
                "timestamp": f"2024-01-{i + 1:02d}",
                "symbol": "TEST",
                "open": float(c),
                "high": float(c) + 0.5,
                "low": float(c) - 0.5,
                "close": float(c),
                "adjusted_close": float(c),
                "volume": 1_000_000.0,
            }
        )
    return bars


def market_bars(closes=None):
    """MarketBar objects (strategy/engine paths)."""
    from samarth_work.core_schemas.schemas import MarketBar

    closes = list(CLOSES if closes is None else closes)
    return [
        MarketBar(
            timestamp=f"2024-01-{i + 1:02d}",
            symbol="TEST",
            open=float(c),
            high=float(c) + 0.5,
            low=float(c) - 0.5,
            close=float(c),
            adjusted_close=float(c),
            volume=1_000_000.0,
        )
        for i, c in enumerate(closes)
    ]


def signal_side(sig):
    if isinstance(sig, dict):
        return str(sig.get("signal", sig.get("side", ""))).upper()
    return str(getattr(sig, "signal", getattr(sig, "side", ""))).upper()
