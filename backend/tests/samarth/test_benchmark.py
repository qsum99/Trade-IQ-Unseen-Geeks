"""Unit tests: backtesting/benchmark.py — buy-hold + strategy comparison."""
import unittest

from helpers import CLOSES, make_bars


class TestBenchmark(unittest.TestCase):
    def test_buy_and_hold_final(self):
        from samarth_work.backtesting.benchmark import buy_and_hold

        curve = buy_and_hold(make_bars(), 100000.0)
        self.assertEqual(len(curve), len(CLOSES))
        self.assertAlmostEqual(curve[-1].portfolio_value, 100000.0 * CLOSES[-1] / CLOSES[0])

    def test_compare_excess(self):
        from samarth_work.backtesting.benchmark import buy_and_hold, compare

        bench = buy_and_hold(make_bars(), 100000.0)
        strat = [{"portfolio_value": 100000.0 + (p.portfolio_value - 100000.0) * 1.5}
                 for p in bench]
        out = compare(strat, bench)
        for key in ("strategy_return", "benchmark_return", "excess_return",
                    "tracking_error", "information_ratio", "upside_capture",
                    "downside_capture", "strategy_sharpe", "benchmark_sharpe",
                    "strategy_mdd", "benchmark_mdd"):
            self.assertIn(key, out)
        self.assertAlmostEqual(out["excess_return"],
                               out["strategy_return"] - out["benchmark_return"])
        self.assertGreaterEqual(out["tracking_error"], 0.0)

    def test_empty_bars(self):
        from samarth_work.backtesting.benchmark import buy_and_hold

        self.assertEqual(buy_and_hold([], 100000.0), [])

    def test_zero_first_close_raises(self):
        from samarth_work.backtesting.benchmark import buy_and_hold

        with self.assertRaises(ValueError):
            buy_and_hold(make_bars([0.0, 100.0]), 100000.0)

    def test_compare_too_short_raises(self):
        from samarth_work.backtesting.benchmark import compare

        with self.assertRaises(ValueError):
            compare([100.0], [100.0])

    def test_flat_market_zero_excess(self):
        from samarth_work.backtesting.benchmark import compare

        out = compare([100000.0] * 10, [100000.0] * 10)
        self.assertAlmostEqual(out["excess_return"], 0.0)
        self.assertAlmostEqual(out["upside_capture"], 0.0)
        self.assertAlmostEqual(out["downside_capture"], 0.0)

    def test_dict_bars_float_curves_and_sharpe_guards(self):
        from samarth_work.backtesting.benchmark import _sharpe, buy_and_hold, compare

        curve = buy_and_hold(make_bars([100.0, 110.0, 121.0]), 1000.0)
        self.assertEqual(len(curve), 3)
        self.assertAlmostEqual(curve[-1].portfolio_value, 1210.0)
        out = compare([100.0, 110.0, 121.0], [100.0, 105.0, 110.0])
        self.assertGreater(out["strategy_return"], out["benchmark_return"])
        self.assertEqual(_sharpe([0.01], 0.0), 0.0)
        self.assertEqual(_sharpe([0.01, 0.01, 0.01], 0.0), 0.0)  # zero variance


if __name__ == "__main__":
    unittest.main()
