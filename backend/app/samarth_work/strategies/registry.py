"""Strategy registry (api.md §16). Stdlib only."""
from __future__ import annotations

from samarth_work.strategies.base import Strategy
from samarth_work.strategies.ema import EmaTrend
from samarth_work.strategies.mean_reversion import MeanReversion
from samarth_work.strategies.momentum import MomentumStrategy
from samarth_work.strategies.regime import RegimeAdaptive
from samarth_work.strategies.sma import SmaCrossover

STRATEGIES: dict[str, type[Strategy]] = {
    SmaCrossover.id: SmaCrossover,
    EmaTrend.id: EmaTrend,
    MomentumStrategy.id: MomentumStrategy,
    MeanReversion.id: MeanReversion,
    RegimeAdaptive.id: RegimeAdaptive,
}


def get_strategy(strategy_id: str, **params: object) -> Strategy:
    try:
        cls = STRATEGIES[strategy_id]
    except KeyError:
        raise ValueError(
            f"Unknown strategy '{strategy_id}'. Available: {sorted(STRATEGIES)}"
        ) from None
    return cls(**params)  # type: ignore[arg-type]


def _param_type(value: object) -> str:
    if isinstance(value, bool):
        return "boolean"
    if isinstance(value, int):
        return "integer"
    if isinstance(value, float):
        return "number"
    if isinstance(value, str):
        return "string"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    return "string"


def describe() -> list[dict]:
    """Return [{id, name, description, parameters:[{name,type,default}]}]."""
    out: list[dict] = []
    for sid, cls in STRATEGIES.items():
        params = [
            {"name": name, "type": _param_type(default), "default": default}
            for name, default in cls.default_params.items()
        ]
        out.append(
            {
                "id": sid,
                "name": cls.name,
                "description": cls.description,
                "parameters": params,
            }
        )
    return out
