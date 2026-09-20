"""Strategies API logic (api.md §§16-17,29). Stdlib only.

Lazy-imports the strategy registry INSIDE functions so this module has no
hard dependency on sibling-agent files. Falls back to a static 5-entry
catalog when the registry is not yet present.
"""
from __future__ import annotations

from dataclasses import asdict, is_dataclass

from samarth_work.core_schemas.schemas import envelope, error_envelope

FALLBACK_STRATEGIES: list[dict] = [
    {
        "id": "sma_crossover",
        "name": "SMA Crossover",
        "description": "Generates signals using fast and slow SMA",
        "parameters": [
            {"name": "fast_period", "type": "integer", "default": 20},
            {"name": "slow_period", "type": "integer", "default": 50},
        ],
    },
    {
        "id": "ema_trend",
        "name": "EMA Trend",
        "description": "EMA20 > EMA50 -> LONG trend following",
        "parameters": [
            {"name": "fast_period", "type": "integer", "default": 20},
            {"name": "slow_period", "type": "integer", "default": 50},
        ],
    },
    {
        "id": "momentum",
        "name": "Momentum",
        "description": "20d return above threshold -> BUY",
        "parameters": [
            {"name": "lookback", "type": "integer", "default": 20},
            {"name": "threshold", "type": "number", "default": 0.02},
        ],
    },
    {
        "id": "mean_reversion",
        "name": "Mean Reversion",
        "description": "Z-score entry/exit around rolling mean",
        "parameters": [
            {"name": "lookback", "type": "integer", "default": 20},
            {"name": "entry_z", "type": "number", "default": 2.0},
        ],
    },
    {
        "id": "regime_adaptive",
        "name": "Regime Adaptive",
        "description": "Bull/bear/volatility-regime strategy map (configurable)",
        "parameters": [
            {"name": "regime_model", "type": "string", "default": "rule_based"},
            {"name": "mapping", "type": "object", "default": {}},
        ],
    },
]


def _to_jsonable(obj):
    if is_dataclass(obj):
        return asdict(obj)
    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_jsonable(v) for v in obj]
    return obj


def list_strategies() -> dict:
    """GET /strategies — registry-backed, static fallback on ImportError."""
    try:
        from samarth_work.strategies import registry as reg  # lazy

        for attr in ("list_strategies", "describe", "list_all", "all_strategies"):
            fn = getattr(reg, attr, None)
            if callable(fn):
                return envelope(_to_jsonable(fn()))
        catalog = getattr(reg, "STRATEGIES", None)
        if isinstance(catalog, dict):
            try:
                from samarth_work.strategies.registry import describe as _describe  # lazy

                return envelope(_to_jsonable(_describe()))
            except ImportError:
                pass
            return envelope(_to_jsonable(list(catalog)))
        if isinstance(catalog, list):
            return envelope(_to_jsonable(catalog))
    except ImportError:
        pass
    return envelope([dict(s) for s in FALLBACK_STRATEGIES])


def _coerce_bars(bars: list, symbol: str = "TEST") -> list:
    """Accept MarketBar or plain-dict bars, return MarketBar list."""
    from samarth_work.core_schemas.schemas import MarketBar  # lazy

    out = []
    for i, b in enumerate(bars or []):
        if hasattr(b, "close") and hasattr(b, "timestamp"):
            out.append(b)
            continue
        if isinstance(b, dict):
            close = float(b.get("close", b.get("adjusted_close", b.get("price", 0.0))))
            out.append(MarketBar(
                timestamp=str(b.get("timestamp", b.get("date", f"bar_{i}"))),
                symbol=str(b.get("symbol", symbol)),
                open=float(b.get("open", close)),
                high=float(b.get("high", close)),
                low=float(b.get("low", close)),
                close=close,
                adjusted_close=b.get("adjusted_close"),
                volume=b.get("volume")))
            continue
        raise TypeError(f"unsupported bar type: {type(b)}")
    return out


def regime_adaptive(bars: list, regime_timeline: list[str],
                    mapping: dict | None = None,
                    strategy_params: dict | None = None,
                    regime_model: str = "kmeans") -> dict:
    """POST /strategies/regime-adaptive (api.md §29, work_divide §14).

    Builds signals for each mapped strategy, then routes per-bar by regime.
    Unknown/unbuildable strategies are skipped (those bars fall back to HOLD).
    """
    from samarth_work.strategies.regime import RegimeAdaptive  # lazy
    from samarth_work.strategies.registry import get_strategy  # lazy

    try:
        mbars = _coerce_bars(bars)
        ra = RegimeAdaptive(
            regime_model=regime_model,
            mapping=dict(mapping) if mapping else None) if mapping else RegimeAdaptive(
            regime_model=regime_model)
        strategy_params = dict(strategy_params or {})
        signals_by_strategy: dict[str, list] = {}
        for sid in set(ra.mapping.values()):
            try:
                strat = get_strategy(sid, **strategy_params.get(sid, {}))
            except (ValueError, TypeError):
                continue  # unbuildable -> HOLD via select's missing-sid path
            gen = getattr(strat, "generate_signals", None)
            if gen is None:
                continue
            try:
                signals_by_strategy[sid] = gen(mbars, strategy_params.get(sid, {}))
            except TypeError:
                signals_by_strategy[sid] = gen(mbars)
        signals = ra.select(mbars, list(regime_timeline or []), signals_by_strategy)
        return envelope({"strategy": "regime_adaptive", "regime_model": ra.regime_model,
                         "mapping": ra.mapping, "signals": _to_jsonable(signals)})
    except (ValueError, AttributeError, TypeError) as exc:
        return error_envelope("STRATEGY_FAILED", str(exc))


def signals_for(strategy_id: str, bars: list, params: dict | None = None) -> dict:
    """POST /strategies/signals — resolve strategy lazily, wrap in envelope."""
    params = params or {}
    try:
        from samarth_work.strategies import registry as reg  # lazy

        strategy = None
        getter = getattr(reg, "get_strategy", None) or getattr(reg, "get", None)
        if callable(getter):
            try:
                strategy = getter(strategy_id, **params)
            except TypeError:
                strategy = getter(strategy_id)
        elif isinstance(getattr(reg, "STRATEGIES", None), dict):
            entry = reg.STRATEGIES.get(strategy_id)
            strategy = entry(**params) if isinstance(entry, type) else entry
        if strategy is None:
            return error_envelope("STRATEGY_NOT_FOUND", f"Unknown strategy: {strategy_id}")
        gen = getattr(strategy, "generate_signals", strategy)
        try:
            signals = gen(bars, params) if params else gen(bars)
        except TypeError:
            signals = gen(bars)
        return envelope({"strategy": strategy_id, "signals": _to_jsonable(signals)})
    except ImportError:
        return error_envelope(
            "STRATEGY_ENGINE_UNAVAILABLE",
            "Strategy registry not yet present in this workspace",
        )
    except (ValueError, AttributeError) as exc:
        return error_envelope("STRATEGY_FAILED", str(exc))
