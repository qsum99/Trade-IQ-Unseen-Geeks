"""Unit tests: backtesting/engine.py — T+1, sizing, ledger invariants."""
import unittest

from helpers import market_bars


def _sig(bars, idx, side):
    from samarth_work.core_schemas.schemas import StrategySignal

    return StrategySignal(date=bars[idx].timestamp, signal=side, price=bars[idx].close)


def _ctx(closes, **req_kw):
    from samarth_work.core_schemas.schemas import BacktestRequest

    bars = market_bars(closes)
    kw = dict(symbol="TEST", strategy="sma_crossover", initial_capital=100000.0,
              transaction_cost=0.0, slippage=0.0)
    kw.update(req_kw)
    return bars, BacktestRequest(**kw)


def _run(bars, request, signals, cost_fn=None):
    from samarth_work.backtesting.engine import BacktestEngine

    if cost_fn is None:
        return BacktestEngine().run(bars, signals, request)
    return BacktestEngine().run(bars, signals, request, cost_fn=cost_fn)


class TestEngine(unittest.TestCase):
    def test_t1_execution_and_invariants(self):
        from samarth_work.core_schemas.schemas import BacktestRequest

        bars = market_bars()  # default 15-bar series

        request = BacktestRequest(symbol="TEST", strategy="sma_crossover",
                                  initial_capital=100000.0,
                                  transaction_cost=0.001, slippage=0.0005)
        result = _run(bars, request, [_sig(bars, 1, "BUY"), _sig(bars, 5, "SELL")])
        self.assertEqual(len(result["equity"]), len(bars))
        index_of = {b.timestamp: i for i, b in enumerate(bars)}
        first_buy = next(t for t in result["trades"] if t.side == "BUY")
        self.assertGreater(index_of[first_buy.date], 1)  # T+1

        cash, holdings, fills = float(request.initial_capital), 0.0, {}
        for t in result["trades"]:
            fills.setdefault(t.date, []).append(t)
        for i, bar in enumerate(bars):
            for t in fills.get(bar.timestamp, []):
                if t.side == "BUY":
                    cash -= t.quantity * t.price + t.transaction_cost
                    holdings += t.quantity
                else:
                    cash += t.quantity * t.price - t.transaction_cost
                    holdings -= t.quantity
            self.assertGreaterEqual(cash, -1e-6, f"negative cash at bar {i}")
            self.assertGreaterEqual(holdings, -1e-9, f"negative holdings at bar {i}")
            self.assertAlmostEqual(cash + holdings * bar.close,
                                   result["equity"][i].portfolio_value, places=4)

    def test_fixed_sizing(self):
        bars, req = _ctx([100, 100, 100, 100, 100], position_sizing="fixed",
                         fixed_quantity=10.0)
        result = _run(bars, req, [_sig(bars, 0, "BUY")])
        self.assertEqual(len(result["trades"]), 1)
        self.assertAlmostEqual(result["trades"][0].quantity, 10.0)

    def test_risk_based_sizing(self):
        bars, req = _ctx([100, 100, 100, 100, 100], position_sizing="risk_based",
                         risk_fraction=0.01, stop_distance=10.0)
        result = _run(bars, req, [_sig(bars, 0, "BUY")])
        # position_size(100000, 0.01, 10) = 100 shares (risk-capital / stop_distance)
        self.assertAlmostEqual(result["trades"][0].quantity, 100.0)

    def test_sell_without_position_ignored(self):
        bars, req = _ctx([100, 101, 102, 103, 104])
        result = _run(bars, req, [_sig(bars, 1, "SELL")])
        self.assertEqual(result["trades"], [])
        self.assertEqual(result["metrics"]["total_trades"], 0)

    def test_double_buy_single_position(self):
        bars, req = _ctx([100, 101, 102, 103, 104, 105])
        result = _run(bars, req, [_sig(bars, 0, "BUY"), _sig(bars, 1, "BUY"),
                                  _sig(bars, 3, "SELL")])
        self.assertEqual(len([t for t in result["trades"] if t.side == "BUY"]), 1)
        self.assertEqual(len([t for t in result["trades"] if t.side == "SELL"]), 1)

    def test_last_bar_signal_no_fill(self):
        bars, req = _ctx([100, 101, 102])
        result = _run(bars, req, [_sig(bars, 2, "BUY")])
        self.assertEqual(result["trades"], [])

    def test_next_close_mode(self):
        bars, req = _ctx([100, 110, 120, 130], execution_price="next_close")
        result = _run(bars, req, [_sig(bars, 0, "BUY")])
        self.assertAlmostEqual(result["trades"][0].price, 110.0)

    def test_invalid_sizing_raises(self):
        bars, req = _ctx([100, 101, 102], position_sizing="martingale")
        with self.assertRaises(ValueError):
            _run(bars, req, [_sig(bars, 0, "BUY")])

    def test_all_hold_flat_equity(self):
        from samarth_work.core_schemas.schemas import StrategySignal

        bars, req = _ctx([100, 101, 102, 103])
        sigs = [StrategySignal(date=b.timestamp, signal="HOLD", price=b.close)
                for b in bars]
        result = _run(bars, req, sigs)
        self.assertEqual(result["trades"], [])
        self.assertAlmostEqual(result["metrics"]["total_return"], 0.0)
        for p in result["equity"]:
            self.assertAlmostEqual(p.portfolio_value, 100000.0)

    def test_custom_cost_fn_called(self):
        bars, req = _ctx([100, 101, 102, 103, 104])
        calls = []
        result = _run(bars, req, [_sig(bars, 0, "BUY"), _sig(bars, 2, "SELL")],
                      cost_fn=lambda v, s: calls.append((v, s)) or 5.0)
        self.assertGreaterEqual(len(calls), 2)  # BUY re-quotes on scale-down
        self.assertTrue(all(c.transaction_cost == 5.0 for c in result["trades"]))

    def test_single_bar_and_zero_capital(self):
        bars, req = _ctx([100.0])
        result = _run(bars, req, [])
        self.assertEqual(result["metrics"]["volatility"], 0.0)
        self.assertEqual(result["metrics"]["sharpe"], 0.0)
        bars0, req0 = _ctx([100.0], symbol="T", strategy="s", initial_capital=0.0)
        result0 = _run(bars0, req0, [])
        self.assertEqual(result0["metrics"]["total_return"], 0.0)


if __name__ == "__main__":
    unittest.main()
