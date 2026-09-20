"""Unit tests: quant_stub/formulas.py (Satish-compatible signatures)."""
import unittest

from helpers import CLOSES  # noqa: F401  (fixture module)
from helpers import market_bars  # noqa: F401


class TestFormulas(unittest.TestCase):
    def test_sma_values_and_prefix(self):
        from samarth_work.quant_stub.formulas import sma_series

        self.assertEqual(sma_series([1, 2, 3, 4, 5], 3), [None, None, 2.0, 3.0, 4.0])

    def test_sma_invalid_period(self):
        from samarth_work.quant_stub.formulas import sma_series

        with self.assertRaises(ValueError):
            sma_series([1, 2, 3], 1)

    def test_ema_seed_and_prefix(self):
        from samarth_work.quant_stub.formulas import ema_series

        out = ema_series([1, 2, 3, 4, 5], 3)
        self.assertEqual(out[:2], [None, None])
        self.assertAlmostEqual(out[2], 2.0)  # seeded with SMA(3)
        self.assertEqual(ema_series([], 3), [])
        with self.assertRaises(ValueError):
            ema_series([1, 2, 3], 1)

    def test_momentum_and_zero_base(self):
        from samarth_work.quant_stub.formulas import momentum

        out = momentum([100.0, 110.0], 1)
        self.assertIsNone(out[0])
        self.assertAlmostEqual(out[1], 0.1)
        self.assertEqual(momentum([0.0, 10.0], 1), [None, None])

    def test_zscore_constant_and_short(self):
        from samarth_work.quant_stub.formulas import zscore

        self.assertEqual(zscore([5.0, 5.0, 5.0]), [0.0, 0.0, 0.0])
        self.assertEqual(zscore([1.0]), [None])

    def test_position_size_and_validation(self):
        from samarth_work.quant_stub.formulas import position_size

        self.assertAlmostEqual(position_size(100000.0, 0.01, 10.0), 100.0)
        for bad in ((0.0, 0.01, 10.0), (100.0, 0.0, 10.0), (100.0, 0.01, 0.0)):
            with self.assertRaises(ValueError):
                position_size(*bad)


if __name__ == "__main__":
    unittest.main()
