"""Unit tests: backtesting/execution.py — slippage, T+1, impact."""
import unittest

from helpers import market_bars


class TestExecution(unittest.TestCase):
    def test_slippage_directions(self):
        from samarth_work.backtesting.execution import apply_slippage

        self.assertAlmostEqual(apply_slippage("BUY", 100.0, 0.0005), 100.05)
        self.assertAlmostEqual(apply_slippage("SELL", 100.0, 0.0005), 99.95)
        with self.assertRaises(ValueError):
            apply_slippage("HOLD", 100.0, 0.0005)

    def test_resolve_modes_and_last_bar(self):
        from samarth_work.backtesting.execution import resolve_price

        bars = market_bars([100, 110, 120])
        self.assertAlmostEqual(resolve_price(bars, 0, "next_open"), 110.0)
        bars[1].close = 115.0
        self.assertAlmostEqual(resolve_price(bars, 0, "next_close"), 115.0)
        self.assertIsNone(resolve_price(bars, 2, "next_open"))
        with self.assertRaises(ValueError):
            resolve_price(bars, 0, "vwap")

    def test_impact(self):
        from samarth_work.backtesting.execution import estimate_impact

        self.assertEqual(estimate_impact(1e6, 0.0, 1e7, 1.0), 0.0)
        self.assertEqual(estimate_impact(1e6, 0.1, 0.0, 1.0), 0.0)
        self.assertAlmostEqual(estimate_impact(1e6, 0.1, 1e7, 1.0), 0.01)


if __name__ == "__main__":
    unittest.main()
