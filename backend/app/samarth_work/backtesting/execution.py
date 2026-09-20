"""Execution simulator (work_divide §17, samarth.md §4). Stdlib only.

Pipeline: Signal -> Execution Price (T+1) -> Slippage -> Market Impact -> Fees -> Fill.

Look-ahead protection: a signal indexed at bar ``i`` may ONLY fill at bar
``i+1`` or later. Same-bar fills are forbidden.
"""

from __future__ import annotations

from dataclasses import dataclass

from samarth_work.core_schemas.schemas import MarketBar


@dataclass
class ExecutionConfig:
    slippage: float = 0.0005
    mode: str = "next_open"  # next_open | next_close
    market_impact_k: float = 0.0
    market_impact_alpha: float = 1.0
    adv: float = 0.0


def apply_slippage(side: str, signal_price: float, s: float) -> float:
    """Adjust a raw execution price for slippage.

    BUY  -> price * (1 + s)  (pay up)
    SELL -> price * (1 - s)  (give up)
    """
    side_u = side.upper()
    if side_u == "BUY":
        return signal_price * (1 + s)
    if side_u == "SELL":
        return signal_price * (1 - s)
    raise ValueError(f"Unknown side: {side!r} (expected BUY|SELL)")


def resolve_price(
    bars: list[MarketBar], signal_index: int, mode: str
) -> float | None:
    """Return the T+1 execution price for a signal at ``signal_index``.

    ``next_open``  -> next bar's open; ``next_close`` -> next bar's close.
    Returns None when there is no next bar (signal on the last bar -> no fill),
    so look-ahead protection holds by construction.
    """
    if signal_index < 0 or signal_index + 1 >= len(bars):
        return None
    nxt = bars[signal_index + 1]
    if mode == "next_open":
        return nxt.open
    if mode == "next_close":
        return nxt.close
    raise ValueError(f"Unknown execution mode: {mode!r} (expected next_open|next_close)")


def estimate_impact(order_value: float, k: float, adv: float, alpha: float) -> float:
    """Market-impact estimate: ``k * (Q / ADV) ** alpha`` (label ESTIMATED).

    ``order_value`` plays the role of Q. Returns 0.0 when there is no impact
    model (``k == 0``) or no volume baseline (``adv == 0``).
    """
    if k == 0 or adv == 0:
        return 0.0
    if adv <= 0 or order_value <= 0:
        return 0.0
    return k * ((order_value / adv) ** alpha)
