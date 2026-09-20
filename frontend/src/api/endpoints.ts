// Endpoint builders for every backend domain (docs/api.md §57).
// Components/hooks import these — never raw URL strings.

export const endpoints = {
  health: () => "/health",

  auth: {
    register: () => "/auth/register",
    login: () => "/auth/login",
    me: () => "/auth/me",
  },

  assets: (params?: { asset_class?: string; provider?: string; search?: string; page?: number; page_size?: number }) =>
    `/assets${toQuery(params)}`,
  assetHistory: (
    symbol: string,
    params?: { start_date?: string; end_date?: string; interval?: string; adjusted?: boolean; provider?: string },
  ) => `/assets/${encodeURIComponent(symbol)}/history${toQuery(params)}`,

  dataValidate: () => "/data/validate",
  analyticsSummary: () => "/analytics/summary",

  indicators: {
    sma: () => "/indicators/sma",
    ema: () => "/indicators/ema",
    returns: () => "/indicators/returns",
    volatility: () => "/indicators/volatility",
    sharpe: () => "/indicators/sharpe",
    drawdown: () => "/indicators/drawdown",
  },

  correlation: {
    matrix: () => "/correlation/matrix",
    rolling: () => "/correlation/rolling",
  },

  strategies: () => "/strategies",
  strategySignals: () => "/strategies/signals",
  regimeAdaptive: () => "/strategies/regime-adaptive",

  backtests: (params?: { status?: string; strategy?: string; page?: number; page_size?: number }) =>
    `/backtests${toQuery(params)}`,
  backtest: (id: string) => `/backtests/${encodeURIComponent(id)}`,
  backtestEquity: (id: string) => `/backtests/${encodeURIComponent(id)}/equity`,
  backtestTrades: (id: string) => `/backtests/${encodeURIComponent(id)}/trades`,
  backtestMetrics: (id: string) => `/backtests/${encodeURIComponent(id)}/metrics`,
  backtestBenchmark: (id: string) => `/backtests/${encodeURIComponent(id)}/benchmark`,
  backtestTrust: (id: string) => `/backtests/${encodeURIComponent(id)}/trust-report`,

  paperTrade: () => "/paper-trade",
  candles: (symbol: string, params?: { period?: string; interval?: string }) =>
    `/candles/${encodeURIComponent(symbol)}${toQuery(params)}`,
  candleTick: (symbol: string, params?: { interval?: string }) =>
    `/candles/${encodeURIComponent(symbol)}/tick${toQuery(params)}`,

  robustness: {
    parameterStress: () => "/robustness/parameter-stress",
    costStress: () => "/robustness/cost-stress",
    walkForward: () => "/robustness/walk-forward",
  },

  regimes: {
    detect: () => "/regimes/detect",
    compare: () => "/regimes/compare",
    byAsset: (asset: string) => `/regimes/${encodeURIComponent(asset)}`,
  },

  risk: {
    metrics: () => "/risk/metrics",
    var: () => "/risk/var",
    cvar: () => "/risk/cvar",
    monteCarlo: () => "/risk/monte-carlo",
  },

  portfolio: {
    create: () => "/portfolio/create",
    analyze: () => "/portfolio/analyze",
    optimize: () => "/portfolio/optimize",
  },

  quantum: {
    status: () => "/quantum/status",
    regime: () => "/quantum/regime",
    portfolioOptimize: () => "/quantum/portfolio-optimize",
    experiment: (id: string) => `/quantum/experiments/${encodeURIComponent(id)}`,
  },

  ai: {
    research: () => "/ai/research",
    backtest: () => "/ai/backtest",
    explain: () => "/ai/explain",
  },

  research: {
    create: () => "/research/experiments",
    list: (params?: { page?: number; page_size?: number; status?: string; type?: string }) =>
      `/research/experiments${toQuery(params)}`,
    byId: (id: string) => `/research/experiments/${encodeURIComponent(id)}`,
    compare: () => "/research/compare",
  },

  news: (params?: { category?: string; symbol?: string; limit?: number }) =>
    `/news${toQuery(params)}`,
  newsBreaking: (params?: { limit?: number }) =>
    `/news/breaking${toQuery(params)}`,
  newsRefresh: () => "/news/refresh",

  whatsapp: {
    preview: (params?: { phone?: string }) => `/whatsapp/preview${toQuery(params)}`,
    subscribe: () => "/whatsapp/subscribe",
    sendTest: () => "/whatsapp/send-test",
    subscribers: () => "/whatsapp/subscribers",
  },

  job: (jobId: string) => `/jobs/${encodeURIComponent(jobId)}`,
} as const;

function toQuery(params?: Record<string, string | number | boolean | undefined>): string {
  if (!params) return "";
  const q = new URLSearchParams();
  for (const [k, v] of Object.entries(params)) {
    if (v !== undefined && v !== "") q.set(k, String(v));
  }
  const s = q.toString();
  return s ? `?${s}` : "";
}
