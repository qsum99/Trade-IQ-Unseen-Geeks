"""Backtesting engine (work_divide §§15-16, samarth.md §4). Stdlib only.

Long-only, single-position engine with strict look-ahead protection: a signal
at bar ``i`` may only fill at bar ``i+1`` or later via
``execution.resolve_price``. Takes a generic signal list — no imports from the
``strategies/`` package (work_divide §39).
"""

from __future__ import annotations

import math
from collections.abc import Callable

from samarth_work.backtesting.execution import (
    ExecutionConfig,
    apply_slippage,
    resolve_price,
)
from samarth_work.core_schemas.schemas import (
    BacktestRequest,
    EquityPoint,
    MarketBar,
    StrategySignal,
    Trade,
)
from samarth_work.quant_stub.formulas import position_size

CostFn = Callable[[float, str], float]

_ANNUALIZATION = math.sqrt(252)


def _compute_metrics(
    equity_values: list[float],
    initial_capital: float,
    round_trip_pnls: list[float],
    risk_free_rate: float = 0.0,
) -> dict:
    final = equity_values[-1] if equity_values else initial_capital
    if initial_capital:
        total_return = (final - initial_capital) / initial_capital
    else:
        total_return = 0.0

    rets = [
        equity_values[i] / equity_values[i - 1] - 1.0
        for i in range(1, len(equity_values))
        if equity_values[i - 1] != 0
    ]
    if len(rets) >= 2:
        mean = sum(rets) / len(rets)
        var = sum((r - mean) ** 2 for r in rets) / (len(rets) - 1)
        std = math.sqrt(var)
        volatility = std * _ANNUALIZATION
        rf_daily = float(risk_free_rate) / 252.0
        sharpe = ((mean - rf_daily) / std * _ANNUALIZATION) if std != 0 else 0.0
    else:
        volatility = 0.0
        sharpe = 0.0

    peak = float("-inf")
    max_drawdown = 0.0
    for v in equity_values:
        if v > peak:
            peak = v
        if peak > 0:
            dd = (v - peak) / peak
            if dd < max_drawdown:
                max_drawdown = dd

    n_trips = len(round_trip_pnls)
    total_trades = n_trips  # round trips = sells (each SELL closes a position)
    wins = sum(1 for p in round_trip_pnls if p > 0)
    win_rate = (wins / n_trips) if n_trips else 0.0
    gross_profit = sum(p for p in round_trip_pnls if p > 0)
    gross_loss = sum(-p for p in round_trip_pnls if p < 0)
    profit_factor = (gross_profit / gross_loss) if gross_loss > 0 else 0.0
    average_trade = (sum(round_trip_pnls) / n_trips) if n_trips else 0.0

    return {
        "total_return": total_return,
        "sharpe": sharpe,
        "volatility": volatility,
        "max_drawdown": max_drawdown,
        "total_trades": total_trades,
        "win_rate": win_rate,
        "profit_factor": profit_factor,
        "average_trade": average_trade,
    }


class BacktestEngine:
    """Long-only, single-position backtester over generic signal lists."""

    def run(
        self,
        bars: list[MarketBar],
        signals: list[StrategySignal],
        request: BacktestRequest,
        cost_fn: CostFn | None = None,
    ) -> dict:
        n = len(bars)
        backtest_id = f"bt_{request.symbol}_{request.strategy}_{n}"

        rate = request.transaction_cost
        if cost_fn is None:

            def cost_fn(trade_value: float, side: str) -> float:
                return rate * trade_value

        cfg = ExecutionConfig(slippage=request.slippage, mode=request.execution_price)

        # Map each signal to its bar index (date lookup, positional fallback).
        index_of = {b.timestamp: i for i, b in enumerate(bars)}
        fills_by_bar: dict[int, list[tuple[int, str, float]]] = {}
        for seq, sig in enumerate(signals):
            side = sig.signal.upper()
            if side not in ("BUY", "SELL"):
                continue  # HOLD / unknown -> no order
            si = index_of.get(sig.date, seq if seq < n else None)
            if si is None:
                continue
            raw = resolve_price(bars, si, cfg.mode)  # None on last bar -> no fill
            if raw is None or raw <= 0:
                continue
            fills_by_bar.setdefault(si + 1, []).append((seq, side, raw))
        for lst in fills_by_bar.values():
            lst.sort(key=lambda t: t[0])

        cash = float(request.initial_capital)
        holdings = 0.0
        trades: list[Trade] = []
        equity: list[EquityPoint] = []
        round_trip_pnls: list[float] = []
        trade_id = 1
        # Open-lot state for round-trip PnL (single position: at most one lot).
        open_qty = 0.0
        open_outlay = 0.0  # qty * buy_price + buy_cost

        for i, bar in enumerate(bars):
            for _, side, raw in fills_by_bar.get(i, []):
                fill = apply_slippage(side, raw, cfg.slippage)
                if fill <= 0:
                    continue
                if side == "BUY":
                    if holdings > 0:
                        continue  # already invested -> ignore (long-only, no add)
                    if request.position_sizing == "full":
                        qty = cash / fill if cash > 0 else 0.0
                    elif request.position_sizing == "fixed":
                        qty = float(request.fixed_quantity)
                    elif request.position_sizing == "risk_based":
                        qty = (
                            position_size(
                                cash, request.risk_fraction, request.stop_distance
                            )
                            if cash > 0
                            else 0.0
                        )
                    else:
                        raise ValueError(
                            f"Unknown position_sizing: {request.position_sizing!r}"
                        )
                    if qty <= 0:
                        continue
                    value = qty * fill
                    cost = cost_fn(value, side)
                    if value + cost > cash and value + cost > 0:
                        # Scale down so costs never drive cash negative.
                        scale = cash / (value + cost)
                        qty *= scale
                        value = qty * fill
                        cost = cost_fn(value, side)
                    if qty <= 0 or value <= 0:
                        continue
                    cash -= value + cost
                    holdings += qty
                    open_qty = qty
                    open_outlay = value + cost
                    trades.append(
                        Trade(
                            id=trade_id,
                            date=bar.timestamp,
                            side="BUY",
                            price=fill,
                            quantity=qty,
                            transaction_cost=cost,
                        )
                    )
                    trade_id += 1
                else:  # SELL closes the entire position
                    if holdings <= 0:
                        continue  # nothing to close -> ignore
                    qty = holdings
                    value = qty * fill
                    cost = cost_fn(value, side)
                    cash += value - cost
                    round_trip_pnls.append((value - cost) - open_outlay)
                    holdings = 0.0
                    open_qty = 0.0
                    open_outlay = 0.0
                    trades.append(
                        Trade(
                            id=trade_id,
                            date=bar.timestamp,
                            side="SELL",
                            price=fill,
                            quantity=qty,
                            transaction_cost=cost,
                        )
                    )
                    trade_id += 1

            equity_value = cash + holdings * bar.close
            equity.append(
                EquityPoint(date=bar.timestamp, portfolio_value=equity_value)
            )

        metrics = _compute_metrics(
            [p.portfolio_value for p in equity],
            float(request.initial_capital),
            round_trip_pnls,
            risk_free_rate=float(getattr(request, "risk_free_rate", 0.0)),
        )
        return {
            "backtest_id": backtest_id,
            "trades": trades,
            "equity": equity,
            "metrics": metrics,
        }
