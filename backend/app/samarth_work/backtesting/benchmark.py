"""Benchmark engine (samarth.md §4, work_divide §19, math_eq §§22-28).

Buy & Hold on the SAME bars/capital as the strategy, plus
strategy-vs-bench comparison: excess, tracking error, IR, capture ratios.
Stdlib only.
"""
from __future__ import annotations

import math
import statistics

from samarth_work.core_schemas.schemas import EquityPoint

_ANNUAL = 252.0


def _close_of(bar) -> float:
    if isinstance(bar, dict):
        for k in ("close", "adjusted_close", "price"):
            if bar.get(k) is not None:
                return float(bar[k])
        raise KeyError("bar dict has no close/adjusted_close/price")
    for attr in ("close", "adjusted_close", "price"):
        v = getattr(bar, attr, None)
        if v is not None:
            return float(v)
    raise AttributeError("bar has no close/adjusted_close/price")


def _date_of(bar, fallback: str) -> str:
    if isinstance(bar, dict):
        return str(bar.get("date", bar.get("timestamp", fallback)))
    return str(getattr(bar, "date", getattr(bar, "timestamp", fallback)))


def buy_and_hold(bars: list, initial_capital: float) -> list[EquityPoint]:
    """All-in at first close (fractional qty allowed), hold to the end."""
    if not bars:
        return []
    first = _close_of(bars[0])
    if first <= 0:
        raise ValueError("first close must be positive")
    capital = float(initial_capital)
    curve: list[EquityPoint] = []
    for i, bar in enumerate(bars):
        px = _close_of(bar)
        value = capital * px / first
        date = _date_of(bar, f"bar_{i}")
        curve.append(EquityPoint(date=date, portfolio_value=value, benchmark_value=value))
    return curve


def _values_of(curve: list) -> list[float]:
    vals: list[float] = []
    for p in curve:
        if isinstance(p, (int, float)):
            vals.append(float(p))
        elif isinstance(p, dict):
            for k in ("portfolio_value", "benchmark_value", "value", "close"):
                if p.get(k) not in (None, 0):
                    vals.append(float(p[k]))
                    break
            else:
                vals.append(float(p.get("portfolio_value", 0.0)))
        else:
            pv = float(getattr(p, "portfolio_value", 0.0))
            if pv == 0.0 and float(getattr(p, "benchmark_value", 0.0)) != 0.0:
                pv = float(getattr(p, "benchmark_value"))
            vals.append(pv)
    return vals


def _simple_returns(values: list[float]) -> list[float]:
    rets = []
    for prev, cur in zip(values, values[1:]):
        rets.append(cur / prev - 1.0 if prev else 0.0)
    return rets


def _max_drawdown(values: list[float]) -> float:
    peak = -math.inf
    mdd = 0.0
    for v in values:
        peak = max(peak, v)
        if peak > 0:
            mdd = min(mdd, (v - peak) / peak)
    return mdd


def _sharpe(daily: list[float], risk_free: float) -> float:
    if len(daily) < 2:
        return 0.0
    rf_daily = float(risk_free) / _ANNUAL
    excess = [r - rf_daily for r in daily]
    sd = statistics.stdev(excess) if len(excess) > 1 else 0.0
    if sd == 0:
        return 0.0
    return statistics.mean(excess) / sd * math.sqrt(_ANNUAL)


def _capture(strat_daily: list[float], bench_daily: list[float], up: bool) -> float:
    sel = [i for i, r in enumerate(bench_daily) if (r > 0 if up else r < 0)]
    if not sel:
        return 0.0
    s_cum = 1.0
    b_cum = 1.0
    for i in sel:
        s_cum *= 1.0 + strat_daily[i]
        b_cum *= 1.0 + bench_daily[i]
    s_ret, b_ret = s_cum - 1.0, b_cum - 1.0
    if b_ret == 0:
        return 0.0
    return s_ret / b_ret * 100.0


def compare(
    strategy_equity: list,
    bench_equity: list,
    risk_free: float = 0.0,
) -> dict:
    """Strategy vs benchmark on aligned equity curves (math_eq §§22-28)."""
    s_vals = _values_of(strategy_equity)
    b_vals = _values_of(bench_equity)
    if len(s_vals) < 2 or len(b_vals) < 2:
        raise ValueError("need >= 2 equity points per curve")
    n = min(len(s_vals), len(b_vals))
    s_vals, b_vals = s_vals[:n], b_vals[:n]

    s_ret = s_vals[-1] / s_vals[0] - 1.0 if s_vals[0] else 0.0
    b_ret = b_vals[-1] / b_vals[0] - 1.0 if b_vals[0] else 0.0
    excess = s_ret - b_ret

    s_daily = _simple_returns(s_vals)
    b_daily = _simple_returns(b_vals)
    active = [s - b for s, b in zip(s_daily, b_daily)]
    te = (statistics.stdev(active) * math.sqrt(_ANNUAL)) if len(active) > 1 else 0.0
    ir = (statistics.mean(active) * _ANNUAL / te) if te else 0.0

    return {
        "strategy_return": s_ret,
        "benchmark_return": b_ret,
        "excess_return": excess,
        "tracking_error": te,
        "information_ratio": ir,
        "upside_capture": _capture(s_daily, b_daily, up=True),
        "downside_capture": _capture(s_daily, b_daily, up=False),
        "strategy_sharpe": _sharpe(s_daily, risk_free),
        "benchmark_sharpe": _sharpe(b_daily, risk_free),
        "strategy_mdd": _max_drawdown(s_vals),
        "benchmark_mdd": _max_drawdown(b_vals),
    }
