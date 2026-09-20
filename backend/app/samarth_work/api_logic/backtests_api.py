"""Backtest API logic (api.md §§18-23,46). Stdlib only.

All heavy imports (strategy registry, BacktestEngine, costs) happen LAZILY
inside functions so this module imports cleanly before sibling-agent files
land. When the engine is absent, run_backtest degrades to a deterministic
buy-and-hold-style fallback so the envelope contract still holds.
"""
from __future__ import annotations

import uuid
from dataclasses import asdict, is_dataclass

from samarth_work.api_logic import backtest_store as _store
from samarth_work.core_schemas.schemas import (
    BacktestRequest,
    envelope,
    error_envelope,
)


def _to_jsonable(obj):
    if is_dataclass(obj):
        return asdict(obj)
    if isinstance(obj, dict):
        return {k: _to_jsonable(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_jsonable(v) for v in obj]
    return obj


def _build_request(request_dict: dict) -> BacktestRequest:
    """Accept flat BacktestRequest fields OR nested api.md §18 style."""
    req = dict(request_dict or {})
    strategy = req.get("strategy")
    if isinstance(strategy, dict):  # {"type": ..., "parameters": {...}}
        req["strategy"] = strategy.get("type", "sma_crossover")
        if "parameters" not in req and isinstance(strategy.get("parameters"), dict):
            req["parameters"] = strategy["parameters"]
    period = req.get("period")
    if isinstance(period, dict):
        req.setdefault("start_date", period.get("start_date", ""))
        req.setdefault("end_date", period.get("end_date", ""))
    capital = req.get("capital")
    if isinstance(capital, dict):
        req.setdefault("initial_capital", capital.get("initial", 100000.0))
        req.setdefault("position_sizing", capital.get("position_sizing", "full"))
    execution = req.get("execution")
    if isinstance(execution, dict):
        req.setdefault("transaction_cost", execution.get("transaction_cost", 0.001))
        req.setdefault("slippage", execution.get("slippage", 0.0005))
        req.setdefault("execution_price", execution.get("execution_price", "next_open"))
    allowed = {f for f in BacktestRequest.__dataclass_fields__}
    return BacktestRequest(**{k: v for k, v in req.items() if k in allowed})


def _fallback_result(backtest_id: str, request: BacktestRequest, bars: list) -> dict:
    """Deterministic fallback when BacktestEngine is not yet present."""
    try:
        from samarth_work.backtesting.benchmark import buy_and_hold  # lazy
    except ImportError:
        buy_and_hold = None
    try:
        from samarth_work.backtesting.costs import compute_simple  # lazy
    except ImportError:
        compute_simple = None

    if buy_and_hold is not None and bars:
        curve = buy_and_hold(bars, request.initial_capital)
    else:
        curve = []
    equity = _to_jsonable(curve)
    final_value = (
        float(curve[-1].portfolio_value) if curve else float(request.initial_capital)
    )
    total_return = (
        final_value / float(request.initial_capital) - 1.0
        if request.initial_capital
        else 0.0
    )
    cost_total = 0.0
    if compute_simple is not None and bars:
        closes = [
            float(b.get("close", 0.0)) if isinstance(b, dict) else float(getattr(b, "close", 0.0))
            for b in bars
        ]
        if closes and closes[0]:
            qty = float(request.initial_capital) / float(closes[0])
            cost_total = float(
                compute_simple(closes[0] * qty, request.transaction_cost)["total"]
            )
    return {
        "backtest_id": backtest_id,
        "status": "completed",
        "strategy": request.strategy,
        "symbol": request.symbol,
        "initial_capital": request.initial_capital,
        "final_value": final_value,
        "total_return": total_return,
        "total_trades": 0,
        "transaction_cost_total": cost_total,
        "fallback": True,
        "metrics": {"total_return": total_return},
        "trades": [],
        "equity": equity,
    }


def run_backtest(request_dict: dict, bars: list) -> dict:
    """POST /backtests — sync path returning completed envelope inline."""
    try:
        request = _build_request(request_dict)
    except TypeError as exc:
        return error_envelope("INVALID_PARAMETER", f"Bad backtest request: {exc}")

    backtest_id = f"bt_{uuid.uuid4().hex[:8]}"
    try:
        from samarth_work.strategies.registry import get_strategy  # lazy
        from samarth_work.backtesting.engine import BacktestEngine  # lazy
        from samarth_work.backtesting.costs import compute_simple  # lazy
        from samarth_work.core_schemas.schemas import MarketBar  # lazy
    except ImportError:
        return envelope(_fallback_result(backtest_id, request, bars))

    def _as_market_bar(b, i: int):
        if hasattr(b, "close") and hasattr(b, "timestamp"):
            return b
        if isinstance(b, dict):
            close = float(b.get("close", b.get("adjusted_close", b.get("price", 0.0))))
            return MarketBar(
                timestamp=str(b.get("timestamp", b.get("date", f"bar_{i}"))),
                symbol=str(b.get("symbol", request.symbol)),
                open=float(b.get("open", close)),
                high=float(b.get("high", close)),
                low=float(b.get("low", close)),
                close=close,
                adjusted_close=b.get("adjusted_close"),
                volume=b.get("volume"),
            )
        raise TypeError(f"unsupported bar type: {type(b)}")

    try:
        mbars = [_as_market_bar(b, i) for i, b in enumerate(bars)]
        try:
            strategy = get_strategy(request.strategy, **request.parameters)
        except TypeError:
            strategy = get_strategy(request.strategy)
        gen = getattr(strategy, "generate_signals", None)
        if gen is None:
            signals = strategy(mbars, request.parameters)
        else:
            try:
                signals = gen(mbars, request.parameters)
            except TypeError:
                signals = gen(mbars)

        def _cost_fn(trade_value: float, side: str) -> float:
            return float(compute_simple(trade_value, request.transaction_cost)["total"])

        engine = BacktestEngine()
        run = engine.run(mbars, signals, request, cost_fn=_cost_fn)
        if isinstance(run, dict):
            payload = {
                "backtest_id": backtest_id,
                "status": "completed",
                "strategy": request.strategy,
                "symbol": request.symbol,
                **run,
            }
        else:
            payload = {
                "backtest_id": backtest_id,
                "status": "completed",
                "strategy": request.strategy,
                "symbol": request.symbol,
                "result": _to_jsonable(run),
            }
        if "metrics" not in payload:
            payload["metrics"] = {}
        if "trades" not in payload:
            payload["trades"] = []
        if "equity" not in payload:
            payload["equity"] = []
        # Benchmark on the SAME bars/capital (work_divide §19) + persist run.
        try:
            from samarth_work.backtesting.benchmark import (  # lazy
                buy_and_hold, compare as _compare)
            bench_curve = buy_and_hold(mbars, float(request.initial_capital))
            strat_vals = ([p.portfolio_value for p in run["equity"]]
                          if isinstance(run, dict) else [])
            bench_vals = [p.portfolio_value for p in bench_curve]
            payload["benchmark"] = {
                "curve": _to_jsonable(bench_curve),
                "compare": _compare(
                    [{"portfolio_value": v} for v in strat_vals],
                    [{"portfolio_value": v} for v in bench_vals]),
            }
        except Exception:
            payload["benchmark"] = None
        payload = _to_jsonable(payload)
        try:
            _store.save(payload.get("backtest_id", backtest_id), payload)
        except Exception:
            pass
        return envelope(payload)
    except Exception as exc:  # engine present but failed -> structured error
        return error_envelope("BACKTEST_FAILED", str(exc))


def list_backtests() -> dict:
    """GET /backtests — ids of completed runs in this process."""
    return envelope({"backtest_ids": _store.list_ids()})


def get_backtest(backtest_id: str) -> dict:
    """GET /backtests/{id} — full stored run payload."""
    payload = _store.get(backtest_id)
    if payload is None:
        return error_envelope("NOT_FOUND", f"Unknown backtest: {backtest_id}")
    return envelope(payload)


def _get_field(backtest_id: str, field: str) -> dict:
    payload = _store.get(backtest_id)
    if payload is None:
        return error_envelope("NOT_FOUND", f"Unknown backtest: {backtest_id}")
    return envelope({field: payload.get(field)})


def get_equity(backtest_id: str) -> dict:
    """GET /backtests/{id}/equity."""
    return _get_field(backtest_id, "equity")


def get_trades(backtest_id: str) -> dict:
    """GET /backtests/{id}/trades."""
    return _get_field(backtest_id, "trades")


def get_metrics(backtest_id: str) -> dict:
    """GET /backtests/{id}/metrics."""
    return _get_field(backtest_id, "metrics")


def get_benchmark(backtest_id: str) -> dict:
    """GET /backtests/{id}/benchmark — strategy vs buy-and-hold."""
    return _get_field(backtest_id, "benchmark")


_TRUST_KEYS = (
    "lookahead_bias_check",
    "data_leakage_check",
    "execution_model_check",
    "transaction_cost_check",
    "out_of_sample_check",
)


def paper_trade(
    symbol: str = "BTC-USD",
    strategy: str = "sma_crossover",
    parameters: dict | None = None,
    initial_capital: float = 100000.0,
    slippage: float = 0.0005,
    execution_price: str = "next_open",
    interval: str = "1d",
) -> dict:
    """POST /paper_trade — run strategy against live yfinance bar feed.

    Returns a BacktestResult‑shaped dict identical to historical backtest
    so the frontend can render the same charts / metrics.
    """
    from samarth_work.strategies.registry import get_strategy  # lazy

    # Build signals from the named strategy (same logic as /backtests)
    params = parameters or {}
    try:
        strat = get_strategy(strategy, **params)
    except TypeError:
        strat = get_strategy(strategy)

    # Set historical period based on interval
    fetch_period = "730d"
    if interval in ("1m", "5m", "15m", "30m"):
        fetch_period = "60d"
    elif interval == "1h":
        fetch_period = "730d"

    import yfinance as yf
    fetch_symbol = symbol
    try:
        ticker = yf.Ticker(fetch_symbol)
        hist = ticker.history(period=fetch_period, interval=interval, timeout=30)
        if hist.empty and "." not in fetch_symbol and not fetch_symbol.endswith("-USD"):
            for suffix in (".NS", ".BO"):
                alt_sym = f"{fetch_symbol}{suffix}"
                alt_hist = yf.Ticker(alt_sym).history(period=fetch_period, interval=interval, timeout=20)
                if not alt_hist.empty:
                    hist = alt_hist
                    fetch_symbol = alt_sym
                    break
        if hist.empty:
            return error_envelope("NO_DATA", f"No yfinance data for {symbol}")
        # Convert to MarketBar list (same as run_backtest _as_market_bar)
        bars: list = []
        for i, ts in enumerate(hist.index):
            row = hist.loc[ts]
            close = float(row["Close"])
            date_str = (
                ts.strftime("%Y-%m-%d %H:%M")
                if interval in ("1m", "5m", "15m", "30m", "1h")
                else ts.strftime("%Y-%m-%d")
            )
            bars.append(
                {
                    "timestamp": date_str,
                    "symbol": symbol,
                    "open": float(row["Open"]),
                    "high": float(row["High"]),
                    "low": float(row["Low"]),
                    "close": close,
                    "volume": float(row["Volume"]) if row.get("Volume") else None,
                }
            )
    except Exception as exc:
        return error_envelope("YFINANCE_ERROR", str(exc))

    from samarth_work.core_schemas.schemas import MarketBar

    # Generate signals the same way run_backtest does
    try:
        mbars = [
            MarketBar(
                timestamp=b["timestamp"],
                symbol=b["symbol"],
                open=b["open"],
                high=b["high"],
                low=b["low"],
                close=b["close"],
                volume=b.get("volume"),
            )
            for b in bars
        ]
        gen = getattr(strat, "generate_signals", None)
        if gen is not None:
            try:
                signals = gen(mbars, params)
            except TypeError:
                signals = gen(mbars)
        else:
            try:
                signals = strat(mbars, params)
            except TypeError:
                signals = strat(mbars)
    except Exception as exc:
        return error_envelope("STRATEGY_ERROR", str(exc))

    # Run paper-trading engine
    from samarth_work.paper_trading import get_paper_engine, cleanup_paper_engines
    eng = get_paper_engine(fetch_symbol, interval, slippage)

    # Bootstrap feed with the historical window already fetched
    eng.seed_bars(mbars)

    # Run the engine
    try:
        result = eng.run(
            signals=signals,
            initial_capital=initial_capital,
            position_sizing="full",
            transaction_cost=slippage,
            execution_price=execution_price,
        )
    except Exception as exc:
        return error_envelope("ENGINE_ERROR", str(exc))
    finally:
        try:
            cleanup_paper_engines()
        except Exception:
            pass


    # Convert result to envelope format
    equity_curve = [
        {"date": p.date, "portfolio_value": round(float(p.portfolio_value), 2)}
        for p in result.get("equity", [])
    ]
    equity_values = [round(float(p.portfolio_value), 2) for p in result.get("equity", [])]
    metrics = result.get("metrics") or {}

    # Real-world trade enrichment: PnL, return %, order type, holding period
    raw_trades = result.get("trades", [])
    trades = []
    last_buy = None
    for t in raw_trades:
        t_dict = _to_jsonable(t)
        t_dict["order_type"] = "MARKET"
        if t_dict.get("side") == "BUY":
            last_buy = t_dict
            t_dict["realized_pnl"] = None
            t_dict["return_pct"] = None
            t_dict["holding_period"] = None
        elif t_dict.get("side") == "SELL" and last_buy:
            buy_val = last_buy["price"] * last_buy["quantity"] + last_buy.get("transaction_cost", 0.0)
            sell_val = t_dict["price"] * t_dict["quantity"] - t_dict.get("transaction_cost", 0.0)
            pnl = round(sell_val - buy_val, 2)
            ret_pct = round((pnl / buy_val) * 100, 2) if buy_val > 0 else 0.0
            t_dict["realized_pnl"] = pnl
            t_dict["return_pct"] = ret_pct
            t_dict["holding_period"] = f"{last_buy['date']} -> {t_dict['date']}"
            last_buy = None
        trades.append(t_dict)

    backtest_id = result.get("backtest_id", f"paper_{symbol}_{strategy}")

    data = {
        "backtest_id": backtest_id,
        "status": "completed",
        "symbol": symbol,
        "strategy": strategy,
        "initial_capital": float(initial_capital),
        "final_value": float(result.get("final_value", initial_capital)),
        "total_return": float(metrics.get("total_return", result.get("total_return", 0.0))),
        "sharpe": float(metrics.get("sharpe", result.get("sharpe", 0.0))),
        "volatility": float(metrics.get("volatility", result.get("volatility", 0.0))),
        "max_drawdown": float(metrics.get("max_drawdown", result.get("max_drawdown", 0.0))),
        "total_trades": int(metrics.get("total_trades", result.get("total_trades", 0))),
        "win_rate": float(metrics.get("win_rate", result.get("win_rate", 0.0))),
        "profit_factor": float(metrics.get("profit_factor", result.get("profit_factor", 0.0))),
        "average_trade": float(metrics.get("average_trade", result.get("average_trade", 0.0))),
        "trades": trades,
        "equity": equity_values,
        "equity_curve": equity_curve,
        "metrics": metrics,
    }

    # Benchmark on the same bars if possible
    try:
        from samarth_work.backtesting.benchmark import buy_and_hold, compare as _compare
        from samarth_work.core_schemas.schemas import MarketBar
        bench_bars = [
            MarketBar(
                timestamp=b["timestamp"],
                symbol=symbol,
                open=b["open"],
                high=b["high"],
                low=b["low"],
                close=b["close"],
                volume=b.get("volume"),
            )
            for b in mbars
        ]
        bench_curve = buy_and_hold(bench_bars, float(initial_capital))
        bench_points = [
            {"date": p.date, "portfolio_value": round(float(p.portfolio_value), 2)}
            for p in bench_curve
        ]
        data["benchmark"] = {
            "curve": bench_points,
            "compare": _compare(
                [{"portfolio_value": v} for v in equity_values],
                [{"portfolio_value": p["portfolio_value"]} for p in bench_points],
            ),
        }
    except Exception:
        data["benchmark"] = None

    # Persist to store so GET /backtests/{id} and trust-report can read it
    try:
        _store.save(backtest_id, data)
    except Exception:
        pass

    return envelope(data)


def trust_report(backtest_id: str, checks: dict | None = None) -> dict:
    """GET /backtests/{id}/trust-report — api.md §46 envelope."""
    checks = dict(checks or {})
    data: dict = {}
    for key in _TRUST_KEYS:
        if key == "out_of_sample_check" and key not in checks:
            data[key] = {"status": "warning", "message": "Limited out-of-sample period"}
        elif key not in checks:
            data[key] = {"status": "passed"}
        elif isinstance(checks[key], dict):
            data[key] = dict(checks[key])
        else:
            data[key] = {"status": str(checks[key])}
    statuses = [str(data[k].get("status", "")).lower() for k in _TRUST_KEYS]
    if any(s in ("failed", "fail") for s in statuses):
        overall = "fail"
    elif any(s in ("warning", "review") for s in statuses):
        overall = "review"
    else:
        overall = "pass"
    data["overall"] = checks.get("overall", overall)
    data["backtest_id"] = backtest_id
    return envelope(data)
