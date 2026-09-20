"""Regime-adaptive strategy (api.md §29, work_divide §14). Stdlib only."""
from __future__ import annotations

from samarth_work.core_schemas.schemas import MarketBar, StrategySignal
from samarth_work.strategies.base import Strategy

DEFAULT_MAPPING: dict[str, str] = {
    "bull": "momentum",
    "bear": "mean_reversion",
    "high_volatility": "mean_reversion",
    "low_volatility": "ema_trend",
}


class RegimeAdaptive(Strategy):
    """Route each bar's signal to the strategy mapped for that bar's regime."""

    id = "regime_adaptive"
    name = "Regime Adaptive"
    description = "Selects per-bar signals from mapped strategies by regime label"
    default_params = {"regime_model": "kmeans", "mapping": dict(DEFAULT_MAPPING)}

    def __init__(
        self,
        regime_model: str = "kmeans",
        mapping: dict[str, str] | None = None,
    ) -> None:
        resolved = dict(DEFAULT_MAPPING) if mapping is None else dict(mapping)
        super().__init__(regime_model=regime_model, mapping=resolved)
        self.regime_model: str = regime_model
        self.mapping: dict[str, str] = resolved

    def generate_signals(self, bars: list[MarketBar]) -> list[StrategySignal]:
        # Without a regime timeline there is no routing info: HOLD everywhere.
        return [StrategySignal(date=b.timestamp, signal="HOLD", price=b.close) for b in bars]

    def select(
        self,
        bars: list[MarketBar],
        regime_timeline: list[str],
        signals_by_strategy: dict[str, list[StrategySignal]],
    ) -> list[StrategySignal]:
        if len(regime_timeline) != len(bars):
            raise ValueError("regime_timeline length must match bars length")
        for sid, sigs in signals_by_strategy.items():
            if len(sigs) != len(bars):
                raise ValueError(f"signals for '{sid}' length must match bars length")
        out: list[StrategySignal] = []
        for i, bar in enumerate(bars):
            regime = regime_timeline[i]
            sid = self.mapping.get(regime)
            if sid is None or sid not in signals_by_strategy:
                out.append(StrategySignal(date=bar.timestamp, signal="HOLD", price=bar.close))
                continue
            picked = signals_by_strategy[sid][i]
            # Re-stamp date/price to this bar so routing cannot leak other bars.
            out.append(StrategySignal(date=bar.timestamp, signal=picked.signal, price=bar.close))
        return out
