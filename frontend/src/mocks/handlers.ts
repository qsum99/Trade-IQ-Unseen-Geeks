// MSW mock handlers mirroring docs/api.md example payloads.
// Flow: Frontend → apiClient → (MSW mock | real FastAPI). No component rewrite
// needed when the backend comes online — just point NEXT_PUBLIC_API_BASE_URL
// at it. Wire these in src/mocks/browser.ts + instrumentation when needed.

import { http, HttpResponse } from "msw";

const BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000/api/v1";
const path = (p: string) => `${BASE}${p}`;

export const handlers = [
  http.get(path("/health"), () =>
    HttpResponse.json({
      success: true,
      data: {
        status: "healthy",
        version: "1.0.0",
        environment: "development",
        services: {
          database: "healthy",
          market_data: "healthy",
          quant_engine: "healthy",
          ml_engine: "healthy",
          quantum_engine: "available",
        },
      },
    }),
  ),

  http.get(path("/assets"), () =>
    HttpResponse.json({
      success: true,
      data: [
        { symbol: "BTC-USD", name: "Bitcoin", asset_class: "crypto", currency: "USD", exchange: "CRYPTO", provider: "binance", active: true },
        { symbol: "GC=F", name: "Gold", asset_class: "commodity", currency: "USD", exchange: "COMEX", provider: "yahoo", active: true },
        { symbol: "NVDA", name: "NVIDIA Corporation", asset_class: "equity", currency: "USD", exchange: "NASDAQ", provider: "yahoo", active: true },
      ],
    }),
  ),

  http.get(path("/strategies"), () =>
    HttpResponse.json({
      success: true,
      data: [
        { id: "sma_crossover", name: "SMA Crossover", description: "Fast/slow SMA trend following", parameters: [{ name: "fast_period", type: "integer", default: 20 }, { name: "slow_period", type: "integer", default: 50 }] },
        { id: "ema_trend", name: "EMA Trend", parameters: [] },
        { id: "momentum", name: "Momentum", parameters: [] },
        { id: "mean_reversion", name: "Mean Reversion", parameters: [] },
      ],
    }),
  ),

  http.post(path("/backtests"), () =>
    HttpResponse.json({ success: true, data: { backtest_id: "bt_mock_001", status: "completed" } }),
  ),

  http.get(path("/backtests/bt_mock_001"), () =>
    HttpResponse.json({
      success: true,
      data: {
        id: "bt_mock_001",
        status: "completed",
        strategy: "sma_crossover",
        symbol: "NVDA",
        initial_capital: 100000,
        final_value: 137500,
        total_return: 0.375,
        annualized_return: 0.173,
        sharpe: 1.31,
        volatility: 0.28,
        max_drawdown: -0.16,
        total_trades: 18,
      },
    }),
  ),
];
