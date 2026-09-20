// TypeScript contracts mirroring the backend OpenAPI/Pydantic schemas
// (docs/api.md). Backend is the source of truth — regenerate from OpenAPI
// once the backend team publishes it; MSW mocks must match these shapes.

export type AssetClass = "equity" | "crypto" | "commodity" | "index" | "macro";

export interface Asset {
  symbol: string;
  name: string;
  asset_class: AssetClass | string;
  region?: "IN" | "US" | "Global" | string;
  currency: string;
  exchange: string;
  provider: string;
  active: boolean;
}

export interface OhlcvBar {
  timestamp: string; // ISO-8601
  open: number;
  high: number;
  low: number;
  close: number;
  adjusted_close?: number | null;
  volume?: number | null;
}

export interface AssetHistory {
  symbol: string;
  interval: string;
  currency: string;
  data: OhlcvBar[];
}

export interface HealthStatus {
  status: string;
  version: string;
  environment: string;
  services: Record<string, string>;
}

export interface StrategyParam {
  name: string;
  type: "integer" | "number" | "string" | "boolean";
  default?: number | string | boolean;
}

export interface StrategyInfo {
  id: string;
  name: string;
  description?: string;
  parameters: StrategyParam[];
}

export type StrategyType =
  | "sma_crossover"
  | "ema_trend"
  | "momentum"
  | "mean_reversion"
  | "buy_and_hold"
  | "regime_adaptive";

export interface BacktestCreate {
  name: string;
  symbol: string;
  strategy: { type: StrategyType; parameters: Record<string, number | string> };
  period: { start_date: string; end_date: string };
  capital: { initial: number; position_sizing: string };
  execution: { transaction_cost: number; slippage: number; execution_price: string };
  benchmark?: string;
}

export type BacktestStatus = "queued" | "running" | "completed" | "failed";

export interface BacktestResult {
  id: string;
  status: BacktestStatus;
  strategy: string;
  symbol: string;
  initial_capital: number;
  final_value: number;
  total_return: number; // raw decimal, e.g. 0.375 → UI renders 37.5%
  annualized_return: number;
  sharpe: number;
  volatility: number;
  max_drawdown: number;
  total_trades: number;
}

export interface EquityPoint {
  date: string;
  portfolio_value: number;
  benchmark_value: number;
}

export interface Trade {
  id: number;
  date: string;
  side: "BUY" | "SELL";
  price: number;
  quantity: number;
  transaction_cost: number;
}

export interface TrustReport {
  lookahead_bias_check: { status: string };
  data_leakage_check: { status: string };
  execution_model_check: { status: string };
  transaction_cost_check: { status: string };
  out_of_sample_check: { status: string; message?: string };
  overall: string;
}

export interface CorrelationMatrix {
  method: string;
  symbols: string[];
  matrix: number[][];
}

export interface JobStatus {
  job_id: string;
  status: "queued" | "running" | "completed" | "failed";
  progress?: number;
  message?: string;
  result_type?: string;
  result_id?: string;
  error?: { code: string; message: string };
}
