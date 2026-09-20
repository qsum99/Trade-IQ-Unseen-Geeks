"""Mean-reversion strategy (work_divide §14). Stdlib only."""
from __future__ import annotations

from samarth_work.core_schemas.schemas import MarketBar, StrategySignal
from samarth_work.quant_stub.formulas import zscore
from samarth_work.strategies.base import Strategy


class MeanReversion(Strategy):
    """BUY when rolling z-score < -entry_z, SELL when > +entry_z."""

    id = "mean_reversion"
    name = "Mean Reversion"
    description = "Generates signals from rolling z-score of close price"
    default_params = {"lookback": 20, "entry_z": 2.0}

    def __init__(self, lookback: int = 20, entry_z: float = 2.0) -> None:
        super().__init__(lookback=lookback, entry_z=entry_z)
        self.lookback: int = lookback
        self.entry_z: float = entry_z

    def generate_signals(self, bars: list[MarketBar]) -> list[StrategySignal]:
        closes = [b.close for b in bars]
        out: list[StrategySignal] = []
        for i, bar in enumerate(bars):
            signal = "HOLD"
            # Only closes up to index i (never look ahead); need a full window.
            if i + 1 >= self.lookback:
                window = closes[i + 1 - self.lookback : i + 1]
                z = zscore(window)[-1]
                if z is not None:
                    if z < -self.entry_z:
                        signal = "BUY"
                    elif z > self.entry_z:
                        signal = "SELL"
            out.append(StrategySignal(date=bar.timestamp, signal=signal, price=bar.close))
        return out
