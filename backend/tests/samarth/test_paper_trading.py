"""Unit tests for paper trading engine and API (samarth_work.paper_trading)."""
import unittest
from unittest.mock import patch, MagicMock

from helpers import CLOSES, make_bars, market_bars
from samarth_work.core_schemas.schemas import StrategySignal


class TestPaperTrading(unittest.TestCase):
    def test_paper_engine_run_with_seeded_bars(self):
        from samarth_work.paper_trading import PaperTradingEngine

        eng = PaperTradingEngine(symbol="TEST", interval="1d", slippage=0.0005)
        bars = market_bars()
        eng.seed_bars(bars)
        self.assertEqual(len(eng._current_bars()), len(bars))

        signals = [
            StrategySignal(date=b.timestamp, signal="BUY" if i % 4 == 0 else "SELL" if i % 4 == 2 else "HOLD", price=b.close)
            for i, b in enumerate(bars)
        ]
        res = eng.run(signals, initial_capital=100000.0)
        self.assertEqual(res["status"], "completed")
        self.assertIn("total_return", res)
        self.assertIn("sharpe", res)
        self.assertIn("metrics", res)
        self.assertEqual(len(res["equity"]), len(bars))

    def test_paper_trade_api_with_mocked_yfinance(self):
        from samarth_work.api_logic.backtests_api import paper_trade, trust_report
        import pandas as pd

        # Create mock yfinance history dataframe
        dates = pd.date_range("2024-01-01", periods=30, freq="D")
        mock_df = pd.DataFrame(
            {
                "Open": [100.0 + i for i in range(30)],
                "High": [105.0 + i for i in range(30)],
                "Low": [95.0 + i for i in range(30)],
                "Close": [100.0 + (10 if i % 6 > 3 else -5) + i for i in range(30)],
                "Volume": [1000.0 for _ in range(30)],
            },
            index=dates,
        )

        with patch("yfinance.Ticker") as mock_ticker:
            instance = MagicMock()
            instance.history.return_value = mock_df
            mock_ticker.return_value = instance

            res = paper_trade(
                symbol="MOCK.NS",
                strategy="sma_crossover",
                parameters={"fast_period": 2, "slow_period": 5},
                initial_capital=50000.0,
            )

            self.assertTrue(res["success"], res.get("error"))
            data = res["data"]
            self.assertEqual(data["status"], "completed")
            self.assertEqual(data["symbol"], "MOCK.NS")
            self.assertEqual(data["initial_capital"], 50000.0)
            self.assertIn("total_return", data)
            self.assertIn("equity_curve", data)
            self.assertGreaterEqual(len(data["equity_curve"]), 30)

            # Test that trust report can fetch this paper trade
            b_id = data["backtest_id"]
            tr = trust_report(b_id)
            self.assertTrue(tr["success"])
            self.assertEqual(tr["data"]["backtest_id"], b_id)

    def test_candles_api_with_mocked_yfinance(self):
        try:
            from main import get_candles, get_latest_tick
        except ImportError:
            from app.main import get_candles, get_latest_tick
        import pandas as pd

        dates = pd.date_range("2024-01-01", periods=10, freq="D")
        mock_df = pd.DataFrame(
            {
                "Open": [100.0 + i for i in range(10)],
                "High": [105.0 + i for i in range(10)],
                "Low": [95.0 + i for i in range(10)],
                "Close": [102.0 + i for i in range(10)],
                "Volume": [5000 + i * 100 for i in range(10)],
            },
            index=dates,
        )

        with patch("yfinance.Ticker") as mock_ticker:
            instance = MagicMock()
            instance.history.return_value = mock_df
            mock_ticker.return_value = instance

            # Test daily candles
            res = get_candles("BTC-USD", period="1mo", interval="1d")
            self.assertTrue(res["success"])
            self.assertEqual(res["symbol"], "BTC-USD")
            self.assertEqual(res["count"], 10)
            first_candle = res["data"][0]
            self.assertIn("open", first_candle)
            self.assertIn("high", first_candle)
            self.assertIn("low", first_candle)
            self.assertIn("close", first_candle)
            self.assertIn("volume", first_candle)
            self.assertIn("time", first_candle)

            # Test intraday candles (1h with 2y period adjusted to 730d)
            res_1h = get_candles("BTC-USD", period="2y", interval="1h")
            self.assertTrue(res_1h["success"])
            self.assertEqual(res_1h["period"], "730d")  # auto-adjusted safe period

            # Test intraday candles (15m with 1y period adjusted to 60d)
            res_15m = get_candles("BTC-USD", period="1y", interval="15m")
            self.assertTrue(res_15m["success"])
            self.assertEqual(res_15m["period"], "60d")

            # Test tick
            tick_res = get_latest_tick("BTC-USD", interval="1h")
            self.assertTrue(tick_res["success"])
            self.assertIsNotNone(tick_res["data"])
            self.assertEqual(tick_res["data"]["close"], 111.0)

    def test_fetch_history_and_feed_helpers(self):
        from samarth_work.paper_trading import PaperTradingEngine
        import pandas as pd

        eng = PaperTradingEngine(symbol="TEST", interval="1d")

        # Test empty feed helpers
        self.assertEqual(eng._current_bars(), [])

        # Test fetch_history success
        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        mock_df = pd.DataFrame(
            {
                "Open": [100.0] * 5,
                "High": [105.0] * 5,
                "Low": [95.0] * 5,
                "Close": [102.0] * 5,
                "Volume": [1000] * 5,
            },
            index=dates,
        )
        with patch("yfinance.Ticker") as mock_ticker:
            instance = MagicMock()
            instance.history.return_value = mock_df
            mock_ticker.return_value = instance

            bars = eng.fetch_history(start="2024-01-01", end="2024-01-05")
            self.assertEqual(len(bars), 5)
            self.assertEqual(len(eng._current_bars()), 5)

        # Test fetch_history exception branch
        with patch("yfinance.Ticker", side_effect=Exception("network error")):
            bars_err = eng.fetch_history(start="2024-01-01", end="2024-01-05")
            self.assertEqual(bars_err, [])


