"""Base strategy interface (work_divide §§14,16). Stdlib only."""
from __future__ import annotations

from samarth_work.core_schemas.schemas import MarketBar, StrategySignal


class Strategy:
    """Base class for all strategies.

    Attributes:
        id: registry key (e.g. "sma_crossover").
        name: human-readable name.
        description: one-line description for GET /strategies.
        default_params: constructor defaults exposed via describe().
    """

    id: str = "base"
    name: str = "Base Strategy"
    description: str = "Base strategy interface."
    default_params: dict = {}

    def __init__(self, **params: object) -> None:
        merged = dict(self.default_params)
        merged.update(params)
        self.params: dict = merged
        for key, value in merged.items():
            setattr(self, key, value)

    def generate_signals(self, bars: list[MarketBar]) -> list[StrategySignal]:
        raise NotImplementedError
