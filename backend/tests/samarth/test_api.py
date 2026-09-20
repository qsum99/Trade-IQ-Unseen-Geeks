"""Unit tests: api_logic/ — envelope contracts for /strategies + /backtests."""
import unittest

from helpers import CLOSES, make_bars, market_bars


class TestStrategiesApi(unittest.TestCase):
    def test_list_strategies(self):
        from samarth_work.api_logic.strategies_api import list_strategies

        out = list_strategies()
        self.assertTrue(out["success"])
        self.assertEqual(len(out["data"]), 5)

    def test_signals_for_unknown(self):
        from samarth_work.api_logic.strategies_api import signals_for

        out = signals_for("nope", [])
        self.assertFalse(out["success"])
        self.assertIsNotNone(out["error"])

    def test_signals_for_sma(self):
        from samarth_work.api_logic.strategies_api import signals_for

        bars = market_bars()
        out = signals_for("sma_crossover", bars, {"fast_period": 2, "slow_period": 5})
        self.assertTrue(out["success"])
        self.assertEqual(len(out["data"]["signals"]), len(bars))


class TestBacktestsApi(unittest.TestCase):
    def test_run_backtest_nested_style(self):
        from samarth_work.api_logic.backtests_api import run_backtest

        bars = market_bars()
        req = {
            "name": "TEST SMA",
            "symbol": "TEST",
            "strategy": {"type": "sma_crossover",
                         "parameters": {"fast_period": 2, "slow_period": 5}},
            "period": {"start_date": "2024-01-01", "end_date": "2024-01-15"},
            "capital": {"initial": 100000.0, "position_sizing": "full"},
            "execution": {"transaction_cost": 0.001, "slippage": 0.0005,
                          "execution_price": "next_open"},
            "benchmark": "buy_and_hold",
        }
        out = run_backtest(req, bars)
        self.assertTrue(out["success"], out.get("error"))
        self.assertIn("backtest_id", out["data"])
        self.assertEqual(len(out["data"]["equity"]), len(bars))
        self.assertIn("metrics", out["data"])
        self.assertIn("trades", out["data"])

    def test_run_backtest_dict_bars(self):
        from samarth_work.api_logic.backtests_api import run_backtest

        out = run_backtest({"symbol": "TEST", "strategy": "sma_crossover",
                            "initial_capital": 50000.0}, make_bars())
        self.assertTrue(out["success"], out.get("error"))
        self.assertEqual(out["data"]["symbol"], "TEST")
        self.assertEqual(len(out["data"]["equity"]), len(CLOSES))

    def test_run_backtest_failure_envelope(self):
        from samarth_work.api_logic.backtests_api import run_backtest

        out = run_backtest({"symbol": "T", "strategy": "sma_crossover"}, [42])
        self.assertFalse(out["success"])
        self.assertEqual(out["error"]["code"], "BACKTEST_FAILED")

    def test_fallback_result_path(self):
        from samarth_work.api_logic.backtests_api import _fallback_result
        from samarth_work.core_schemas.schemas import BacktestRequest

        out = _fallback_result("bt_x", BacktestRequest(symbol="T", strategy="s",
                              initial_capital=1000.0), [])
        self.assertTrue(out["fallback"])
        self.assertEqual(out["final_value"], 1000.0)

    def test_trust_report(self):
        from samarth_work.api_logic.backtests_api import trust_report

        keys = {"lookahead_bias_check", "data_leakage_check", "execution_model_check",
                "transaction_cost_check", "out_of_sample_check"}
        default = trust_report("bt_1")["data"]
        self.assertEqual(set(default) - {"backtest_id", "overall"}, keys)
        self.assertEqual(default["overall"], "review")  # OOS warning default
        passed = trust_report("bt_1", {k: {"status": "passed"} for k in keys})["data"]
        self.assertEqual(passed["overall"], "pass")
        failed = trust_report("bt_1",
                              {"lookahead_bias_check": {"status": "failed"}})["data"]
        self.assertEqual(failed["overall"], "fail")


class TestRegimeAdaptiveApi(unittest.TestCase):
    def test_routes_by_regime(self):
        from samarth_work.api_logic.strategies_api import regime_adaptive

        bars = market_bars([100, 101, 102, 103, 104, 105, 106, 107])
        timeline = ["bull"] * 4 + ["bear"] * 4
        out = regime_adaptive(
            bars, timeline,
            mapping={"bull": "momentum", "bear": "mean_reversion",
                     "high_volatility": "mean_reversion", "low_volatility": "momentum"},
            strategy_params={"momentum": {"lookback": 2, "threshold": 0.001},
                             "mean_reversion": {"lookback": 3, "entry_z": 0.5}})
        self.assertTrue(out["success"], out.get("error"))
        self.assertEqual(len(out["data"]["signals"]), len(bars))
        self.assertEqual(out["data"]["regime_model"], "kmeans")

    def test_bad_timeline_errors(self):
        from samarth_work.api_logic.strategies_api import regime_adaptive

        out = regime_adaptive(market_bars([100, 101]), ["bull"])  # length mismatch
        self.assertFalse(out["success"])

    def test_unknown_strategy_falls_back_to_hold(self):
        from samarth_work.api_logic.strategies_api import regime_adaptive

        bars = market_bars([100, 101, 102, 103])
        out = regime_adaptive(bars, ["bull"] * 4, mapping={"bull": "nope"})
        self.assertTrue(out["success"])
        self.assertTrue(all(s["signal"] == "HOLD" for s in out["data"]["signals"]))


class TestBacktestStore(unittest.TestCase):
    def _run(self):
        from samarth_work.api_logic.backtests_api import run_backtest

        return run_backtest(
            {"symbol": "TEST", "strategy": {"type": "sma_crossover",
             "parameters": {"fast_period": 2, "slow_period": 5}},
             "initial_capital": 100000.0}, market_bars())

    def test_roundtrip_getters(self):
        from samarth_work.api_logic.backtests_api import (
            get_benchmark, get_backtest, get_equity, get_metrics,
            get_trades, list_backtests)

        out = self._run()
        self.assertTrue(out["success"], out.get("error"))
        bid = out["data"]["backtest_id"]
        self.assertIn("benchmark", out["data"])
        self.assertIn("excess_return", out["data"]["benchmark"]["compare"])
        self.assertIn(bid, list_backtests()["data"]["backtest_ids"])
        self.assertEqual(get_backtest(bid)["data"]["backtest_id"], bid)
        self.assertEqual(len(get_equity(bid)["data"]["equity"]),
                         len(get_backtest(bid)["data"]["equity"]))
        self.assertEqual(get_trades(bid)["data"]["trades"],
                         get_backtest(bid)["data"]["trades"])
        self.assertEqual(get_metrics(bid)["data"]["metrics"],
                         get_backtest(bid)["data"]["metrics"])
        self.assertIn("compare", get_benchmark(bid)["data"]["benchmark"])

    def test_unknown_id(self):
        from samarth_work.api_logic.backtests_api import get_backtest, get_equity

        self.assertFalse(get_backtest("bt_missing")["success"])
        self.assertEqual(get_equity("bt_missing")["error"]["code"], "NOT_FOUND")


if __name__ == "__main__":
    unittest.main()
