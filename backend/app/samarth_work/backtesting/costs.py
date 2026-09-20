"""Indian transaction-cost engine (samarth.md §4, work_divide §18, math_eq §§43-49).

Total = Brokerage + STT + Exchange + SEBI + Stamp + GST (+ Slippage + Impact,
which live in execution.py, NOT here).

Rates are VERSIONED config (CostConfig), never hardcoded in formulas.
Default preset mirrors Zerodha-style equity schedule (Sept 2026).
Stdlib only.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass
class CostConfig:
    """Versioned brokerage/charge preset. Bump `version` when rates change."""

    version: str = "zerodha-2026-09"
    brokerage_flat: float = 20.0
    brokerage_pct: float = 0.0003
    stt_delivery: float = 0.001
    stt_intraday: float = 0.00025
    exchange_rate: float = 0.0000345
    sebi_rate: float = 0.000001  # Rs 10 / crore
    stamp_buy: float = 0.00015
    gst_rate: float = 0.18

    def is_intraday(self, segment: str = "equity_delivery", product: str = "CNC") -> bool:
        seg = (segment or "").lower()
        prod = (product or "").upper()
        return "intraday" in seg or prod in ("MIS", "INTRADAY")

    def compute(
        self,
        trade_value: float,
        side: str,
        segment: str = "equity_delivery",
        product: str = "CNC",
    ) -> dict:
        """Break down charges for one side of a trade.

        trade_value: Price * Quantity (sign ignored, abs taken).
        side: "BUY" | "SELL" (case-insensitive).
        Returns {brokerage, stt, exchange, sebi, stamp, gst, total}.
        """
        value = abs(float(trade_value))
        s = (side or "").upper()
        intraday = self.is_intraday(segment, product)

        if intraday:
            brokerage = min(self.brokerage_pct * value, self.brokerage_flat)
            stt = self.stt_intraday * value if s == "SELL" else 0.0
        else:
            brokerage = 0.0
            stt = self.stt_delivery * value

        exchange = value * self.exchange_rate
        sebi = value * self.sebi_rate
        stamp = value * self.stamp_buy if s == "BUY" else 0.0
        gst = self.gst_rate * (brokerage + sebi + exchange)
        total = brokerage + stt + exchange + sebi + stamp + gst
        return {
            "brokerage": brokerage,
            "stt": stt,
            "exchange": exchange,
            "sebi": sebi,
            "stamp": stamp,
            "gst": gst,
            "total": total,
        }


_DEFAULT = CostConfig()


def compute(
    trade_value: float,
    side: str,
    segment: str = "equity_delivery",
    product: str = "CNC",
    config: CostConfig | None = None,
) -> dict:
    """Module-level convenience wrapper using the default (or given) preset."""
    cfg = config or _DEFAULT
    return cfg.compute(trade_value, side, segment=segment, product=product)


def compute_simple(trade_value: float, rate: float) -> dict:
    """Flat-rate fallback for tests / global assets: {"total": value * rate}."""
    return {"total": abs(float(trade_value)) * float(rate)}
