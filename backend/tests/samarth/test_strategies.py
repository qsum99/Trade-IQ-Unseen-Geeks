"""Unit tests: strategies/ — all 5 strategies + registry (work_divide §14)."""
import unittest

from helpers import market_bars


class TestSmaCrossover(unittest.TestCase):
    def test_buy_and_sell(self):
        from samarth_work.strategies.registry import get_strategy

        strat = get_strategy("sma_crossover", fast_period=2, slow_period=5)
        sides = [s.signal for s in strat.generate_signals(market_bars())]
        self.assertIn("BUY", sides)
        self.assertIn("SELL", sides)

    def test_invalid_params(self):
        from samarth_work.strategies.sma import SmaCrossover

        with self.assertRaises(ValueError):
            SmaCrossover(fast_period=50, slow_period=20)


class TestEmaTrend(unittest.TestCase):
    def test_fires_both_sides(self):
        from samarth_work.strategies.ema import EmaTrend

        sides = [s.signal for s in
                 EmaTrend(fast_period=2, slow_period=5).generate_signals(market_bars())]
        self.assertIn("BUY", sides)
        self.assertIn("SELL", sides)


class TestMomentum(unittest.TestCase):
    def test_both_sides(self):
        from samarth_work.strategies.momentum import MomentumStrategy

        sides = [s.signal for s in
                 MomentumStrategy(lookback=3, threshold=0.01).generate_signals(market_bars())]
        self.assertIn("BUY", sides)
        self.assertIn("SELL", sides)


class TestMeanReversion(unittest.TestCase):
    def test_spike_fires(self):
        from samarth_work.strategies.mean_reversion import MeanReversion

        closes = [100.0] * 10 + [150.0] + [100.0] * 10
        sides = [s.signal for s in
                 MeanReversion(lookback=10, entry_z=1.5).generate_signals(market_bars(closes))]
        self.assertTrue(any(s != "HOLD" for s in sides), f"no signal fired: {sides}")


class TestRegimeAdaptive(unittest.TestCase):
    def test_routing_rejects_and_holds(self):
        from samarth_work.core_schemas.schemas import StrategySignal
        from samarth_work.strategies.regime import RegimeAdaptive

        bars = market_bars([100, 101, 102, 103])
        buys = [StrategySignal(date=b.timestamp, signal="BUY", price=b.close) for b in bars]
        sells = [StrategySignal(date=b.timestamp, signal="SELL", price=b.close) for b in bars]
        ra = RegimeAdaptive(
            mapping={"bull": "mom", "bear": "mr",
                     "high_volatility": "mr", "low_volatility": "mom"})
        out = ra.select(bars, ["bull", "bear", "unknown", "bull"],
                        {"mom": buys, "mr": sells})
        self.assertEqual([s.signal for s in out], ["BUY", "SELL", "HOLD", "BUY"])
        self.assertEqual(out[0].price, bars[0].close)  # re-stamped, no leakage
        with self.assertRaises(ValueError):
            ra.select(bars, ["bull", "bear"], {"mom": buys, "mr": sells})
        with self.assertRaises(ValueError):
            ra.select(bars, ["bull"] * 4, {"mom": buys[:2], "mr": sells})
        self.assertTrue(all(s.signal == "HOLD" for s in ra.generate_signals(bars)))


class TestStrategyBase(unittest.TestCase):
    def test_base_raises(self):
        from samarth_work.strategies.base import Strategy

        with self.assertRaises(NotImplementedError):
            Strategy().generate_signals([])


class TestRegistry(unittest.TestCase):
    def test_all_signal_invariants(self):
        from samarth_work.strategies.registry import STRATEGIES, get_strategy

        self.assertEqual(sorted(STRATEGIES),
                         ["ema_trend", "mean_reversion", "momentum",
                          "regime_adaptive", "sma_crossover"])
        bars = market_bars()
        for sid in sorted(STRATEGIES):
            with self.subTest(strategy=sid):
                sigs = get_strategy(sid).generate_signals(bars)
                self.assertEqual(len(sigs), len(bars))
                for sig, bar in zip(sigs, bars):
                    self.assertIn(sig.signal, ("BUY", "SELL", "HOLD"))
                    self.assertEqual(sig.price, bar.close)
                    self.assertEqual(sig.date, bar.timestamp)

    def test_unknown_and_describe(self):
        from samarth_work.strategies.registry import _param_type, describe, get_strategy

        with self.assertRaises(ValueError):
            get_strategy("nope")
        desc = describe()
        self.assertEqual(len(desc), 5)
        for entry in desc:
            for p in entry["parameters"]:
                self.assertIn("name", p)
                self.assertIn("type", p)
                self.assertIn("default", p)
        self.assertEqual(_param_type(True), "boolean")
        self.assertEqual(_param_type([1]), "array")
        self.assertEqual(_param_type(object()), "string")


if __name__ == "__main__":
    unittest.main()
