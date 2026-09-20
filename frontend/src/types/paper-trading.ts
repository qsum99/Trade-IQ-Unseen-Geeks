export interface StrategyParameter {
  name: string;
  type: string;
  default: number | string | Record<string, unknown>;
  description?: string;
}

export interface Strategy {
  id: string;
  name: string;
  description: string;
  parameters: StrategyParameter[];
}

export interface Trade {
  id: number;
  date: string;
  side: 'BUY' | 'SELL';
  price: number;
  quantity: number;
  transaction_cost: number;
  order_type?: string;
  realized_pnl?: number | null;
  return_pct?: number | null;
  holding_period?: string | null;
}

export interface EquityPoint {
  date: string;
  portfolio_value: number;
}

export interface BenchmarkPoint {
  date: string;
  portfolio_value: number;
}

export interface BenchmarkComparison {
  excess_return?: number;
  tracking_error?: number;
  information_ratio?: number;
  upside_capture?: number;
  downside_capture?: number;
}

export interface TrustReportCheck {
  status: 'passed' | 'warning' | 'review' | 'failed' | 'pass' | 'fail';
  message?: string;
  details?: Record<string, unknown>;
}

export interface TrustReport {
  backtest_id: string;
  overall: 'pass' | 'review' | 'fail';
  lookahead_bias_check: TrustReportCheck;
  data_leakage_check: TrustReportCheck;
  execution_model_check: TrustReportCheck;
  transaction_cost_check: TrustReportCheck;
  out_of_sample_check: TrustReportCheck;
}

export interface PaperTradeResult {
  backtest_id: string;
  status: string;
  symbol: string;
  strategy: string;
  initial_capital: number;
  final_value: number;
  total_return: number;
  sharpe: number;
  volatility: number;
  max_drawdown: number;
  total_trades: number;
  win_rate: number;
  profit_factor: number;
  average_trade: number;
  trades: Trade[];
  equity: number[];
  equity_curve: EquityPoint[];
  benchmark?: {
    curve: BenchmarkPoint[];
    compare?: BenchmarkComparison;
  } | null;
}

export interface PaperTradeRequest {
  symbol: string;
  strategy: string;
  parameters?: Record<string, unknown>;
  initial_capital?: number;
  slippage?: number;
  execution_price?: 'next_open' | 'next_close';
  interval?: string;
}

export interface CandleData {
  time: number;
  date: string;
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface CandleResponse {
  success: boolean;
  symbol: string;
  period: string;
  interval: string;
  count: number;
  data: CandleData[];
  error?: string;
}

export interface CandleTickResponse {
  success: boolean;
  symbol: string;
  data: (CandleData & { fetched_at: string }) | null;
  error?: string;
}
