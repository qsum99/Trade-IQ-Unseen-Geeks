"""Momentum strategy (work_divide §14). Stdlib only."""
from __future__ import annotations

from samarth_work.core_schemas.schemas import MarketBar, StrategySignal
from samarth_work.quant_stub.formulas import momentum
from samarth_work.strategies.base import Strategy


class MomentumStrategy(Strategy):
    """BUY when lookback return > threshold, SELL when < -threshold."""

    id = "momentum"
    name = "Momentum"
    description = "Generates signals from lookback price momentum"
    default_params = {"lookback": 20, "threshold": 0.02}

    def __init__(self, lookback: int = 20, threshold: float = 0.02) -> None:
        super().__init__(lookback=lookback, threshold=threshold)
        self.lookback: int = lookback
        self.threshold: float = threshold

    def generate_signals(self, bars: list[MarketBar]) -> list[StrategySignal]:
        closes = [b.close for b in bars]
        mom = momentum(closes, self.lookback)
        out: list[StrategySignal] = []
        for i, bar in enumerate(bars):
            m = mom[i]
            if m is None:
                signal = "HOLD"
            elif m > self.threshold:
                signal = "BUY"
            elif m < -self.threshold:
                signal = "SELL"
            else:
                signal = "HOLD"
            out.append(StrategySignal(date=bar.timestamp, signal=signal, price=bar.close))
        return out
