"""Unit tests: backtesting/costs.py — versioned Indian charge engine."""
import unittest


class TestCosts(unittest.TestCase):
    def test_delivery_buy_breakdown(self):
        from samarth_work.backtesting.costs import CostConfig

        cfg = CostConfig()
        self.assertEqual(cfg.version, "zerodha-2026-09")
        out = cfg.compute(100000.0, "BUY")
        self.assertEqual(out["brokerage"], 0.0)  # delivery: zero brokerage
        self.assertAlmostEqual(out["stt"], 100.0)  # 0.001 both sides
        self.assertAlmostEqual(out["exchange"], 100000.0 * 0.0000345)
        self.assertAlmostEqual(out["sebi"], 100000.0 * 0.000001)
        self.assertAlmostEqual(out["stamp"], 100000.0 * 0.00015)
        self.assertAlmostEqual(
            out["gst"], 0.18 * (out["brokerage"] + out["sebi"] + out["exchange"]))
        self.assertGreater(out["total"], 0.0)
        self.assertAlmostEqual(
            out["total"],
            out["brokerage"] + out["stt"] + out["exchange"]
            + out["sebi"] + out["stamp"] + out["gst"])

    def test_intraday_stt_sell_only_and_cap(self):
        from samarth_work.backtesting.costs import compute

        sell = compute(10000.0, "SELL", segment="equity_intraday", product="MIS")
        buy = compute(10000.0, "BUY", segment="equity_intraday", product="MIS")
        self.assertAlmostEqual(sell["stt"], 10000.0 * 0.00025)
        self.assertEqual(buy["stt"], 0.0)
        self.assertAlmostEqual(sell["brokerage"], min(0.0003 * 10000.0, 20.0))
        big = compute(10_000_000.0, "BUY", segment="equity_intraday", product="MIS")
        self.assertAlmostEqual(big["brokerage"], 20.0)  # flat cap
        self.assertEqual(big["stt"], 0.0)
        self.assertEqual(sell["stamp"], 0.0)
        self.assertGreater(buy["stamp"], 0.0)

    def test_compute_simple(self):
        from samarth_work.backtesting.costs import compute_simple

        self.assertAlmostEqual(compute_simple(50000.0, 0.001)["total"], 50.0)

    def test_custom_config_respected(self):
        from samarth_work.backtesting.costs import CostConfig

        cfg = CostConfig(brokerage_flat=5.0, brokerage_pct=0.001, version="test-v1")
        out = cfg.compute(100000.0, "SELL", segment="equity_intraday", product="MIS")
        self.assertAlmostEqual(out["brokerage"], 5.0)
        self.assertEqual(cfg.version, "test-v1")

    def test_negative_value_treated_as_abs(self):
        from samarth_work.backtesting.costs import compute

        self.assertEqual(compute(-50000.0, "BUY"), compute(50000.0, "BUY"))

    def test_is_intraday_by_product(self):
        from samarth_work.backtesting.costs import CostConfig

        cfg = CostConfig()
        self.assertTrue(cfg.is_intraday("equity_delivery", "MIS"))
        self.assertFalse(cfg.is_intraday("equity_delivery", "CNC"))


if __name__ == "__main__":
    unittest.main()
