"""EMA trend strategy (work_divide §14). Stdlib only."""
from __future__ import annotations

from samarth_work.core_schemas.schemas import MarketBar, StrategySignal
from samarth_work.quant_stub.formulas import ema_series
from samarth_work.strategies.base import Strategy


class EmaTrend(Strategy):
    """BUY (LONG) when fast EMA crosses above slow EMA, SELL on cross below."""

    id = "ema_trend"
    name = "EMA Trend"
    description = "Generates signals using fast and slow EMA trend"
    default_params = {"fast_period": 20, "slow_period": 50}

    def __init__(self, fast_period: int = 20, slow_period: int = 50) -> None:
        if fast_period >= slow_period:
            raise ValueError("fast_period must be < slow_period")
        super().__init__(fast_period=fast_period, slow_period=slow_period)
        self.fast_period: int = fast_period
        self.slow_period: int = slow_period

    def generate_signals(self, bars: list[MarketBar]) -> list[StrategySignal]:
        closes = [b.close for b in bars]
        fast = ema_series(closes, self.fast_period)
        slow = ema_series(closes, self.slow_period)
        out: list[StrategySignal] = []
        for i, bar in enumerate(bars):
            f, s = fast[i], slow[i]
            signal = "HOLD"
            if f is not None and s is not None and i > 0:
                pf, ps = fast[i - 1], slow[i - 1]
                if pf is not None and ps is not None:
                    if f > s and pf <= ps:
                        signal = "BUY"  # LONG entry
                    elif f < s and pf >= ps:
                        signal = "SELL"  # LONG exit
            out.append(StrategySignal(date=bar.timestamp, signal=signal, price=bar.close))
        return out
