// ---------------------------------------------------------------------------
// MOCK market-data + strategy engine (frontend stand-in ONLY).
// The real math lives in the FastAPI backend (docs/arch.md §8–11). Every
// function here is deterministic (seeded) so the UI is stable until the
// backend OpenAPI is wired in — then replace these call sites with apiClient.
// ---------------------------------------------------------------------------

export interface Bar {
  date: string; // ISO yyyy-mm-dd
  open: number;
  high: number;
  low: number;
  close: number;
  volume: number;
}

export interface AssetMeta {
  symbol: string;
  name: string;
  assetClass: "Crypto" | "Commodity" | "Equity" | "Index";
  /** Market region — drives the Indian / US equity split in filters. */
  region: "IN" | "US" | "Global";
  currency: "USD" | "INR";
  exchange: string;
  provider: string;
  color: string;
  /** Search keywords (e.g. "nasdaq", "snp") — matched by asset search boxes. */
  aliases?: string[];
}

export const ASSETS: AssetMeta[] = [
  { symbol: "BTC-USD", name: "Bitcoin", assetClass: "Crypto", region: "Global", currency: "USD", exchange: "CRYPTO", provider: "binance", color: "#f7931a", aliases: ["bitcoin", "btc"] },
  { symbol: "ETH-USD", name: "Ethereum", assetClass: "Crypto", region: "Global", currency: "USD", exchange: "CRYPTO", provider: "binance", color: "#627eea", aliases: ["ethereum", "eth"] },
  { symbol: "GC=F", name: "Gold Futures", assetClass: "Commodity", region: "Global", currency: "USD", exchange: "COMEX", provider: "yahoo", color: "#d4af37", aliases: ["gold", "gcf"] },
  { symbol: "NVDA", name: "NVIDIA Corp", assetClass: "Equity", region: "US", currency: "USD", exchange: "NASDAQ", provider: "yahoo", color: "#76b900", aliases: ["nvidia", "nvda"] },
  { symbol: "RELIANCE.NS", name: "Reliance Industries", assetClass: "Equity", region: "IN", currency: "INR", exchange: "NSE", provider: "nse", color: "#0d9488", aliases: ["reliance", "ril"] },
  { symbol: "^NSEI", name: "NIFTY 50", assetClass: "Index", region: "IN", currency: "INR", exchange: "NSE", provider: "nse", color: "#2563eb", aliases: ["nifty", "nsei"] },
  { symbol: "^IXIC", name: "NASDAQ Composite", assetClass: "Index", region: "US", currency: "USD", exchange: "NASDAQ", provider: "yahoo", color: "#6366f1", aliases: ["nasdaq", "ixic", "nasdaq composite"] },
  { symbol: "^GSPC", name: "S&P 500", assetClass: "Index", region: "US", currency: "USD", exchange: "SNP", provider: "yahoo", color: "#0ea5e9", aliases: ["s&p", "snp", "sp500", "s&p 500", "gspc", "spx"] },
];

const BASE: Record<string, { price: number; drift: number; vol: number; volume: number }> = {
  "BTC-USD": { price: 28500, drift: 0.0016, vol: 0.042, volume: 18_400 },
  "ETH-USD": { price: 1820, drift: 0.0012, vol: 0.048, volume: 96_000 },
  "GC=F": { price: 1980, drift: 0.00028, vol: 0.009, volume: 148_000 },
  NVDA: { price: 48.2, drift: 0.0022, vol: 0.031, volume: 411_254_000 },
  "RELIANCE.NS": { price: 2440, drift: 0.00052, vol: 0.014, volume: 12_400_000 },
  "^NSEI": { price: 19850, drift: 0.00042, vol: 0.0085, volume: 312_000_000 },
  "^IXIC": { price: 16200, drift: 0.0009, vol: 0.016, volume: 4_500_000_000 },
  "^GSPC": { price: 5200, drift: 0.0006, vol: 0.011, volume: 3_900_000_000 },
};

function hashSeed(s: string): number {
  let h = 2166136261;
  for (let i = 0; i < s.length; i++) {
    h ^= s.charCodeAt(i);
    h = Math.imul(h, 16777619);
  }
  return h >>> 0;
}

function mulberry32(seed: number) {
  let a = seed;
  return () => {
    a |= 0;
    a = (a + 0x6d2b79f5) | 0;
    let t = Math.imul(a ^ (a >>> 15), 1 | a);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

const DAY = 86_400_000;

export function getHistory(symbol: string, days = 760): Bar[] {
  const cfg = BASE[symbol] ?? BASE["NVDA"];
  const rand = mulberry32(hashSeed(symbol));
  // Gaussian-ish shocks via summed uniforms
  const shock = () => (rand() + rand() + rand() - 1.5) * 2;
  const bars: Bar[] = [];
  let price = cfg.price;
  // Walk BACKWARDS from a fixed "today" so the latest price is realistic.
  const today = new Date("2026-09-18T00:00:00Z").getTime();
  const closes: number[] = [price];
  for (let i = 1; i < days; i++) {
    const r = cfg.drift + cfg.vol * shock() * 0.62;
    price = price / (1 + r); // step backwards
    closes.unshift(price);
  }
  // Deterministic regime drift overlays (bull 2023, drawdown 2022-like tail at start)
  for (let i = 0; i < days; i++) {
    const t = i / days;
    const regime = 1 + 0.55 * Math.sin(t * Math.PI * 2.2 + hashSeed(symbol) % 7) * t;
    const c = closes[i] * (0.72 + 0.38 * regime);
    const o = c * (1 + (shock() * cfg.vol) / 4);
    const h = Math.max(o, c) * (1 + rand() * cfg.vol * 0.7);
    const l = Math.min(o, c) * (1 - rand() * cfg.vol * 0.7);
    const d = new Date(today - (days - 1 - i) * DAY);
    bars.push({
      date: d.toISOString().slice(0, 10),
      open: round(o),
      high: round(h),
      low: round(l),
      close: round(c),
      volume: Math.round(cfg.volume * (0.6 + rand() * 0.9)),
    });
  }
  return bars;
}

const round = (v: number) => Math.round(v * 100) / 100;

export function smaOf(values: number[], n: number): (number | null)[] {
  return values.map((_, i) => {
    if (i < n - 1) return null;
    let s = 0;
    for (let k = i - n + 1; k <= i; k++) s += values[k];
    return s / n;
  });
}

export function emaOf(values: number[], n: number): (number | null)[] {
  const k = 2 / (n + 1);
  const out: (number | null)[] = [];
  let prev: number | null = null;
  values.forEach((v, i) => {
    if (i < n - 1) {
      out.push(null);
      return;
    }
    if (i === n - 1) {
      let s = 0;
      for (let k2 = 0; k2 < n; k2++) s += values[k2];
      prev = s / n;
      out.push(prev);
      return;
    }
    prev = v * k + (prev as number) * (1 - k);
    out.push(prev);
  });
  return out;
}

export function drawdownSeries(equity: number[]): number[] {
  let peak = -Infinity;
  return equity.map((v) => {
    peak = Math.max(peak, v);
    return peak === 0 ? 0 : (v - peak) / peak;
  });
}

export function maxDrawdown(equity: number[]): number {
  return Math.min(...drawdownSeries(equity), 0);
}

function stats(returns: number[], periods = 252, rf = 0.02) {
  if (returns.length < 2) return { vol: 0, sharpe: 0 };
  const mean = returns.reduce((a, b) => a + b, 0) / returns.length;
  const variance =
    returns.reduce((a, b) => a + (b - mean) * (b - mean), 0) / (returns.length - 1);
  const vol = Math.sqrt(variance) * Math.sqrt(periods);
  const excess = mean * periods - rf;
  return { vol, sharpe: vol === 0 ? 0 : excess / vol };
}

// ------------------------------- Backtest --------------------------------

export interface MockTrade {
  id: number;
  date: string;
  side: "BUY" | "SELL";
  price: number;
  quantity: number;
  cost: number;
}

export interface MockBacktest {
  equity: { date: string; value: number; benchmark: number }[];
  trades: MockTrade[];
  signals: { date: string; side: "BUY" | "SELL"; price: number }[];
  metrics: {
    totalReturn: number;
    annualized: number;
    sharpe: number;
    volatility: number;
    maxDD: number;
    numTrades: number;
    winRate: number;
    finalValue: number;
    benchReturn: number;
    benchSharpe: number;
    benchDD: number;
  };
}

export function runBacktest(
  symbol: string,
  fast = 20,
  slow = 50,
  initial = 100_000,
  cost = 0.001,
  slippage = 0.0005,
): MockBacktest {
  const bars = getHistory(symbol);
  const closes = bars.map((b) => b.close);
  const f = smaOf(closes, fast);
  const s = smaOf(closes, slow);

  let cash = initial;
  let shares = 0;
  let entryPx = 0;
  let wins = 0;
  let closed = 0;
  const trades: MockTrade[] = [];
  const signals: MockBacktest["signals"] = [];
  const equity: MockBacktest["equity"] = [];

  const benchShares = (initial * (1 - cost)) / closes[0];
  let id = 1;

  for (let i = 0; i < bars.length; i++) {
    const px = closes[i];
    const inPos = i >= slow && (f[i] as number) > (s[i] as number);
    // Execute at next bar (T+1): apply pending state from previous bar
    if (i > slow) {
      const wasIn = (f[i - 1] as number) > (s[i - 1] as number);
      if (!wasIn && inPos && cash > 0) {
        const exec = px * (1 + slippage);
        const qty = (cash * (1 - cost)) / exec;
        cash = 0;
        shares = qty;
        entryPx = exec;
        const fee = qty * exec * cost;
        trades.push({ id: id++, date: bars[i].date, side: "BUY", price: round(exec), quantity: round(qty * 100) / 100, cost: round(fee) });
        signals.push({ date: bars[i].date, side: "BUY", price: round(exec) });
      } else if (wasIn && !inPos && shares > 0) {
        const exec = px * (1 - slippage);
        const proceeds = shares * exec * (1 - cost);
        const fee = shares * exec * cost;
        if (exec > entryPx) wins++;
        closed++;
        cash = proceeds;
        shares = 0;
        trades.push({ id: id++, date: bars[i].date, side: "SELL", price: round(exec), quantity: round(shares === 0 ? 0 : 0) || 0, cost: round(fee) });
        // fix quantity display (shares already zeroed)
        trades[trades.length - 1].quantity = Math.round((proceeds / exec) * 100) / 100;
        signals.push({ date: bars[i].date, side: "SELL", price: round(exec) });
      }
    }
    const value = cash + shares * px;
    equity.push({ date: bars[i].date, value: round(value), benchmark: round(benchShares * px) });
  }
  // Liquidate at end
  const lastPx = closes[closes.length - 1];
  const finalValue = cash + shares * lastPx * (1 - cost);

  const vals = equity.map((e) => e.value);
  const rets = vals.slice(1).map((v, i) => v / vals[i] - 1);
  const benchVals = equity.map((e) => e.benchmark);
  const benchRets = benchVals.slice(1).map((v, i) => v / benchVals[i] - 1);
  const { vol, sharpe } = stats(rets);
  const bench = stats(benchRets);
  const years = bars.length / 252;
  const totalReturn = finalValue / initial - 1;
  const benchReturn = benchVals[benchVals.length - 1] / initial - 1;

  return {
    equity,
    trades,
    signals,
    metrics: {
      totalReturn,
      annualized: Math.pow(1 + totalReturn, 1 / years) - 1,
      sharpe,
      volatility: vol,
      maxDD: maxDrawdown(vals),
      numTrades: trades.length,
      winRate: closed === 0 ? 0 : wins / closed,
      finalValue: round(finalValue),
      benchReturn,
      benchSharpe: bench.sharpe,
      benchDD: maxDrawdown(benchVals),
    },
  };
}

// ----------------------------- Correlation -------------------------------

export function corrMatrix(symbols: string[]): { symbols: string[]; matrix: number[][] } {
  const rets = symbols.map((s) => {
    const h = getHistory(s, 260);
    const c = h.map((b) => b.close);
    return c.slice(1).map((v, i) => v / c[i] - 1);
  });
  const n = Math.min(...rets.map((r) => r.length));
  const pearson = (a: number[], b: number[]) => {
    const ma = a.reduce((x, y) => x + y, 0) / a.length;
    const mb = b.reduce((x, y) => x + y, 0) / b.length;
    let num = 0;
    let da = 0;
    let db = 0;
    for (let i = 0; i < a.length; i++) {
      num += (a[i] - ma) * (b[i] - mb);
      da += (a[i] - ma) * (a[i] - ma);
      db += (b[i] - mb) * (b[i] - mb);
    }
    return da === 0 || db === 0 ? 0 : num / Math.sqrt(da * db);
  };
  const matrix = symbols.map((_, i) =>
    symbols.map((_, j) => {
      if (i === j) return 1;
      const v = pearson(rets[i].slice(-n), rets[j].slice(-n));
      return Math.round(v * 100) / 100;
    }),
  );
  return { symbols, matrix };
}

export function rollingCorr(a: string, b: string, window = 60): { date: string; value: number }[] {
  const ha = getHistory(a);
  const hb = getHistory(b);
  const n = Math.min(ha.length, hb.length);
  const out: { date: string; value: number }[] = [];
  for (let i = window; i < n; i++) {
    const ra = ha.slice(i - window, i).map((x, k, arr) => (k === 0 ? 0 : x.close / arr[k - 1].close - 1)).slice(1);
    const rb = hb.slice(i - window, i).map((x, k, arr) => (k === 0 ? 0 : x.close / arr[k - 1].close - 1)).slice(1);
    const ma = ra.reduce((x, y) => x + y, 0) / ra.length;
    const mb = rb.reduce((x, y) => x + y, 0) / rb.length;
    let num = 0;
    let da = 0;
    let db = 0;
    for (let k = 0; k < ra.length; k++) {
      num += (ra[k] - ma) * (rb[k] - mb);
      da += (ra[k] - ma) * (ra[k] - ma);
      db += (rb[k] - mb) * (rb[k] - mb);
    }
    out.push({ date: ha[i].date, value: da === 0 || db === 0 ? 0 : Math.round((num / Math.sqrt(da * db)) * 100) / 100 });
  }
  return out;
}

// ------------------------------ Asset search ------------------------------

/** Text search over symbol + name + aliases (e.g. "nasdaq", "snp", "nifty"). */
export function searchAssets(query: string, exclude: string[] = [], limit = 6): AssetMeta[] {
  const q = query.trim().toLowerCase();
  if (!q) return [];
  return ASSETS.filter(
    (a) =>
      !exclude.includes(a.symbol) &&
      (a.symbol.toLowerCase().includes(q) ||
        a.name.toLowerCase().includes(q) ||
        (a.aliases ?? []).some((k) => k.includes(q))),
  ).slice(0, limit);
}

// -------------------------------- Regimes --------------------------------

export interface RegimeSegment {
  label: "Bull" | "Bear" | "High Vol" | "Low Vol";
  from: string;
  to: string;
}

export function regimeTimeline(symbol: string): RegimeSegment[] {
  const bars = getHistory(symbol, 760);
  const segs: RegimeSegment[] = [];
  const labels: RegimeSegment["label"][] = ["Bear", "Bull", "High Vol", "Bull", "Low Vol", "Bull"];
  const span = Math.floor(bars.length / labels.length);
  labels.forEach((label, i) => {
    segs.push({
      label,
      from: bars[i * span].date,
      to: bars[Math.min(bars.length - 1, (i + 1) * span - 1)].date,
    });
  });
  return segs;
}
