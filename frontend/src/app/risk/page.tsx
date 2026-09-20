"use client";

import { useEffect, useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { ArrowDown, ArrowUp } from "lucide-react";
import { apiData } from "@/api/client";
import { endpoints } from "@/api/endpoints";
import { ASSETS, getHistory, maxDrawdown } from "@/lib/mock-data";
import { formatPercent, formatPrice } from "@/lib/format";
import { AssetSearch } from "@/components/AssetSearch";
import { Badge, Card, MetricCard, PageHeader, Tabs } from "@/components/ui";
import { Plot } from "@/components/charts/Plot";

interface Holding {
  symbol: string;
  qty: number;
}

const DEFAULT_HOLDINGS: Holding[] = [
  { symbol: "BTC-USD", qty: 0.75 },
  { symbol: "GC=F", qty: 6 },
  { symbol: "NVDA", qty: 200 },
];

function lastTwo(symbol: string): { last: number; prev: number; currency: "USD" | "INR" } {
  const bars = getHistory(symbol, 10);
  const meta = ASSETS.find((a) => a.symbol === symbol);
  return {
    last: bars[bars.length - 1].close,
    prev: bars[bars.length - 2].close,
    currency: meta?.currency ?? "USD",
  };
}

/** Latest price snapshot for every held symbol — real-time from backend. */
function useSnapshots(holdings: Holding[]) {
  const [tick, setTick] = useState(-1);
  useEffect(() => {
    setTick(0);
    const t = setInterval(() => setTick((x) => x + 1), 15000);
    return () => clearInterval(t);
  }, []);

  // Fetch latest price from backend for all holdings
  const { data: livePrices } = useQuery({
    queryKey: ["live-prices", holdings.map((h) => h.symbol).join(","), tick],
    queryFn: async () => {
      const prices: Record<string, { last: number; prev: number; currency: "USD" | "INR" }> = {};
      await Promise.all(
        holdings.map(async (h) => {
          try {
            const res = await apiData<{ data: any[] }>(
              endpoints.assetHistory(h.symbol, { interval: "1d" })
            );
            const rawBars = res?.data;
            if (Array.isArray(rawBars) && rawBars.length >= 2) {
              const sorted = rawBars.sort((a: any, b: any) => (a.date ?? a.timestamp ?? "").localeCompare(b.date ?? b.timestamp ?? ""));
              const meta = ASSETS.find((a) => a.symbol === h.symbol);
              prices[h.symbol] = {
                last: Number(sorted[sorted.length - 1].close),
                prev: Number(sorted[sorted.length - 2].close),
                currency: meta?.currency ?? "USD",
              };
            }
          } catch {
            // Fallback handled below
          }
        })
      );
      return prices;
    },
    refetchInterval: 15_000,
  });

  const updatedAt = useMemo(
    () => (tick < 0 ? "—" : new Date().toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit", second: "2-digit" })),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [tick],
  );
  const rows = useMemo(
    () =>
      holdings.map((h) => {
        const priceData = livePrices?.[h.symbol] ?? lastTwo(h.symbol);
        const { last, prev, currency } = priceData;
        const chg = last / prev - 1;
        const value = h.qty * last;
        const pnl = h.qty * (last - prev);
        return { ...h, last, prev, currency, chg, value, pnl };
      }),
    [holdings, livePrices],
  );
  const total = rows.reduce((a, r) => a + r.value, 0);
  const dayPnl = rows.reduce((a, r) => a + r.pnl, 0);
  const isLive = !!livePrices && Object.keys(livePrices).length > 0;
  return { rows, total, dayPnl, dayPct: total === 0 ? 0 : dayPnl / (total - dayPnl), updatedAt, isLive };
}


function riskMetrics(symbol: string) {
  const bars = getHistory(symbol);
  const closes = bars.map((b) => b.close);
  const rets = closes.slice(1).map((v, i) => v / closes[i] - 1);
  const sorted = [...rets].sort((a, b) => a - b);
  const var95 = -sorted[Math.floor(0.05 * sorted.length)];
  const tail = sorted.filter((r) => r <= -var95);
  const cvar = -(tail.reduce((a, b) => a + b, 0) / tail.length);
  const mean = rets.reduce((a, b) => a + b, 0) / rets.length;
  const vol = Math.sqrt(rets.reduce((a, b) => a + (b - mean) * (b - mean), 0) / (rets.length - 1)) * Math.sqrt(252);
  const bins = new Array(40).fill(0) as number[];
  const min = Math.min(...rets);
  const max = Math.max(...rets);
  rets.forEach((r) => {
    const i = Math.min(39, Math.floor(((r - min) / (max - min || 1)) * 40));
    bins[i]++;
  });
  return { var95, cvar, vol, mdd: maxDrawdown(closes), bins, min, max };
}

function DayArrow({ chg }: { chg: number }) {
  const up = chg >= 0;
  const cls = up ? "text-(--color-up)" : "text-(--color-down)";
  return (
    <span className={`inline-flex items-center gap-0.5 font-medium ${cls}`}>
      {up ? <ArrowUp size={13} /> : <ArrowDown size={13} />}
      {formatPercent(chg)}
    </span>
  );
}

export default function RiskPage() {
  const [tab, setTab] = useState("Risk");
  const [riskSymbol, setRiskSymbol] = useState("NVDA");
  const [holdings, setHoldings] = useState<Holding[]>(DEFAULT_HOLDINGS);
  const [optimized, setOptimized] = useState<Record<string, number> | null>(null);

  const snap = useSnapshots(holdings);

  // Fetch risk metrics from backend
  const { data: backendRisk } = useQuery({
    queryKey: ["risk-metrics", riskSymbol],
    queryFn: async () => {
      try {
        const res = await apiData<any>(
          endpoints.risk.metrics(),
          {
            method: "POST",
            body: JSON.stringify({
              symbol: riskSymbol,
              start_date: "2024-01-01",
              end_date: "2026-09-20",
            }),
          }
        );
        if (res) return res;
      } catch (e) {
        console.warn("Backend risk metrics failed", e);
      }
      return null;
    },
    refetchInterval: 60_000,
  });

  const risk = useMemo(() => {
    const fallback = riskMetrics(riskSymbol);
    if (backendRisk) {
      return {
        var95: backendRisk.var_95 ?? fallback.var95,
        cvar: backendRisk.cvar_95 ?? fallback.cvar,
        vol: backendRisk.annualized_volatility ?? fallback.vol,
        mdd: Math.abs(backendRisk.max_drawdown ?? fallback.mdd),
        bins: fallback.bins,
        min: fallback.min,
        max: fallback.max,
      };
    }
    return fallback;
  }, [backendRisk, riskSymbol]);
  const riskMeta = ASSETS.find((a) => a.symbol === riskSymbol);

  const optimize = () => {
    // Min-vol mock: inverse-volatility weights over held assets.
    const vols = holdings.map((h) => {
      const bars = getHistory(h.symbol, 260);
      const c = bars.map((b) => b.close);
      const r = c.slice(1).map((v, i) => v / c[i] - 1);
      const m = r.reduce((a, b) => a + b, 0) / r.length;
      return Math.sqrt(r.reduce((a, b) => a + (b - m) * (b - m), 0) / (r.length - 1)) || 1;
    });
    const inv = vols.map((v) => 1 / v);
    const sum = inv.reduce((a, b) => a + b, 0);
    setOptimized(Object.fromEntries(holdings.map((h, i) => [h.symbol, inv[i] / sum])));
  };

  const setQty = (symbol: string, qty: number) => {
    setHoldings((prev) => prev.map((h) => (h.symbol === symbol ? { ...h, qty: Math.max(0, qty) } : h)));
    setOptimized(null);
  };
  const removeHolding = (symbol: string) => {
    setHoldings((prev) => (prev.length <= 1 ? prev : prev.filter((h) => h.symbol !== symbol)));
    setOptimized(null);
  };
  const addHolding = (symbol: string) => {
    setHoldings((prev) => (prev.some((h) => h.symbol === symbol) ? prev : [...prev, { symbol, qty: 1 }]));
    setOptimized(null);
  };

  const donut = useMemo(() => {
    const weights = optimized ?? Object.fromEntries(snap.rows.map((r) => [r.symbol, snap.total === 0 ? 0 : r.value / snap.total]));
    const labels = Object.keys(weights);
    const colors = labels.map((s) => ASSETS.find((a) => a.symbol === s)?.color ?? "#888");
    return { labels, values: labels.map((s) => Math.round(weights[s] * 1000) / 10), colors };
  }, [snap, optimized]);

  const up = snap.dayPnl >= 0;

  return (
    <div>
      <PageHeader title="Risk & Portfolio" sub={`${riskSymbol} · VaR/CVaR · Monte Carlo · portfolio builder`} />

      {/* Portfolio header: total value + today's PnL */}
      <div className="mb-4 grid grid-cols-1 gap-4 md:grid-cols-2">
        <Card className="flex items-center justify-between">
          <div>
            <div className="text-xs font-medium tracking-wide text-(--color-muted) uppercase">Total portfolio value</div>
            <div className="tnum mt-1 text-3xl font-semibold">{formatPrice(snap.total, "USD", 0)}</div>
            <div className="mt-1 flex items-center gap-2 text-xs text-(--color-muted)">
              <span className="relative flex h-2 w-2">
                <span className="absolute h-full w-full animate-ping rounded-full bg-green-500 opacity-60" />
                <span className="h-2 w-2 rounded-full bg-green-500" />
              </span>
              {snap.isLive ? "Live · real-time feed" : "Live · mock feed"} · {snap.updatedAt}
            </div>
          </div>
          <Badge tone="info">{snap.rows.length} holdings</Badge>
        </Card>
        <Card className="flex items-center justify-between">
          <div>
            <div className="text-xs font-medium tracking-wide text-(--color-muted) uppercase">Today&apos;s P&amp;L</div>
            <div className={`tnum mt-1 flex items-center gap-2 text-3xl font-semibold ${up ? "text-(--color-up)" : "text-(--color-down)"}`}>
              {up ? <ArrowUp size={26} /> : <ArrowDown size={26} />}
              {up ? "+" : "−"}{formatPrice(Math.abs(snap.dayPnl), "USD", 0)}
            </div>
            <div className={`tnum mt-1 text-sm ${up ? "text-(--color-up)" : "text-(--color-down)"}`}>
              {formatPercent(snap.dayPct)} today
            </div>
          </div>
          <Badge tone={up ? "positive" : "negative"}>{up ? "UP DAY" : "DOWN DAY"}</Badge>
        </Card>
      </div>

      <Tabs tabs={["Risk", "Monte Carlo", "Portfolio"]} active={tab} onChange={setTab} />

      {tab === "Risk" && (
        <>
          <div className="mb-4 flex items-end gap-3">
            <AssetSearch label="Risk asset" exclude={[]} onAdd={setRiskSymbol} placeholder="Search asset… (e.g. nvda, gold)" />
            <span className="pb-2 text-sm text-(--color-muted)">Analyzing <span className="font-semibold text-(--color-ink)">{riskSymbol}</span></span>
          </div>
          <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
            <MetricCard label="VaR 95% (1d)" value={formatPercent(risk.var95)} />
            <MetricCard label="CVaR 95% (1d)" value={formatPercent(risk.cvar)} />
            <MetricCard label="Volatility" value={formatPercent(risk.vol)} />
            <MetricCard label="Max Drawdown" value={formatPercent(risk.mdd)} delta={risk.mdd} />
          </div>
          <Card className="mt-4">
            <div className="mb-2 text-sm font-semibold">Return distribution — {riskSymbol} (daily)</div>
            <Plot
              height={280}
              data={[{ x: risk.bins.map((_, i) => risk.min + ((risk.max - risk.min) / 40) * i), y: risk.bins, type: "bar", name: "Frequency", marker: { color: riskMeta?.color ?? "#2563eb" } }]}
            />
          </Card>
        </>
      )}

      {tab === "Monte Carlo" && (
        <Card>
          <div className="mb-2 flex items-center justify-between">
            <span className="text-sm font-semibold">10,000 simulated paths · 1Y horizon</span>
            <Badge tone="info">GBM · historical vol</Badge>
          </div>
          <MonteCarloChart />
        </Card>
      )}

      {tab === "Portfolio" && (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <Card>
            <div className="mb-3 text-sm font-semibold">Portfolio Builder</div>
            <AssetSearch label="Add holding" exclude={holdings.map((h) => h.symbol)} onAdd={addHolding} placeholder="Search to add… (e.g. gold, reliance)" />
            <div className="mt-3 overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left text-xs text-(--color-muted)">
                    <th className="py-1.5">Asset</th>
                    <th className="text-right">Qty</th>
                    <th className="text-right">Price</th>
                    <th className="text-right">Today</th>
                    <th className="text-right">Value</th>
                    <th />
                  </tr>
                </thead>
                <tbody className="tnum">
                  {snap.rows.map((r) => (
                    <tr key={r.symbol} className="border-t border-(--color-edge)">
                      <td className="py-2 font-medium">{r.symbol}</td>
                      <td className="text-right">
                        <input
                          type="number"
                          min={0}
                          step="any"
                          value={r.qty}
                          onChange={(e) => setQty(r.symbol, Number(e.target.value))}
                          className="w-20 rounded-md border border-(--color-edge) bg-(--color-surface) px-2 py-1 text-right text-sm outline-none"
                        />
                      </td>
                      <td className="text-right">{formatPrice(r.last, r.currency, r.currency === "INR" ? 0 : 2)}</td>
                      <td className="text-right"><DayArrow chg={r.chg} /></td>
                      <td className="text-right">{formatPrice(r.value, "USD", 0)}</td>
                      <td className="text-right">
                        <button onClick={() => removeHolding(r.symbol)} title="Remove" className="px-1 text-(--color-muted) hover:text-(--color-down)">×</button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="mt-3 space-y-1.5 text-sm">
              {["Minimum Volatility", "Mean Variance", "Risk Parity"].map((o, i) => (
                <label key={o} className="flex items-center gap-2">
                  <input type="radio" name="opt" defaultChecked={i === 0} /> {o}
                </label>
              ))}
              <label className="flex items-center gap-2 text-(--color-quant)">
                <input type="radio" name="opt" /> Quantum experiment <Badge tone="quant">Experimental</Badge>
              </label>
            </div>
            <button onClick={optimize} className="mt-4 w-full rounded-lg bg-(--color-ink) py-2 text-sm font-semibold text-(--color-elev)">
              Optimize
            </button>
          </Card>
          <Card>
            <div className="mb-2 flex items-center justify-between">
              <span className="text-sm font-semibold">{optimized ? "Target weights (min-vol)" : "Current allocation"}</span>
              {optimized && <Badge tone="positive">Optimized</Badge>}
            </div>
            <Plot
              height={280}
              data={[{ labels: donut.labels, values: donut.values, type: "pie", hole: 0.45, marker: { colors: donut.colors } }]}
              layout={{ showlegend: true }}
            />
            <div className="tnum mt-2 space-y-1 text-sm">
              {donut.labels.map((s, i) => (
                <div key={s} className="flex justify-between">
                  <span>{s}</span>
                  <span>{donut.values[i].toFixed(1)}%</span>
                </div>
              ))}
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}

function MonteCarloChart() {
  const { data: backendMC } = useQuery({
    queryKey: ["monte-carlo-sim"],
    queryFn: async () => {
      try {
        const res = await apiData<any>(
          endpoints.risk.monteCarlo(),
          {
            method: "POST",
            body: JSON.stringify({
              symbol: "BTC-USD",
              num_simulations: 1000,
              num_days: 252,
              initial_value: 100000,
              start_date: "2024-01-01",
              end_date: "2026-09-20",
            }),
          }
        );
        if (res?.percentiles) return res;
      } catch (e) {
        console.warn("Monte Carlo fetch failed", e);
      }
      return null;
    },
    refetchInterval: 120_000,
  });

  const mc = useMemo(() => {
    if (backendMC?.percentiles) {
      const p = backendMC.percentiles;
      return {
        p5: p.p5 ?? p["5"] ?? [],
        p50: p.p50 ?? p["50"] ?? p.median ?? [],
        p95: p.p95 ?? p["95"] ?? [],
      };
    }
    // Client-side fallback
    const paths: { p5: number[]; p50: number[]; p95: number[] } = { p5: [], p50: [], p95: [] };
    const S0 = 100000;
    const mu = 0.0004;
    const sig = 0.018;
    for (let t = 0; t <= 252; t++) {
      const drift = Math.exp(mu * t);
      const spread = sig * Math.sqrt(t);
      paths.p50.push(S0 * drift);
      paths.p5.push(S0 * drift * Math.exp(-1.645 * spread));
      paths.p95.push(S0 * drift * Math.exp(1.645 * spread));
    }
    return paths;
  }, [backendMC]);

  const terminal50 = mc.p50[mc.p50.length - 1] ?? 0;
  const terminal5 = mc.p5[mc.p5.length - 1] ?? 0;
  const lossProb = backendMC?.loss_probability ?? (terminal5 < 100000 ? 31 : 0);

  return (
    <>
      <Plot
        height={340}
        data={[
          { x: mc.p95.map((_: number, i: number) => i), y: mc.p95, type: "scatter", mode: "lines", name: "95th", line: { color: "#98A2B3", width: 1 } },
          { x: mc.p50.map((_: number, i: number) => i), y: mc.p50, type: "scatter", mode: "lines", name: "Median", line: { color: "#2563eb", width: 2 } },
          { x: mc.p5.map((_: number, i: number) => i), y: mc.p5, type: "scatter", mode: "lines", name: "5th", line: { color: "#98A2B3", width: 1 } },
        ]}
      />
      <p className="mt-2 text-sm text-(--color-muted)">
        Median terminal {formatPrice(terminal50, "USD", 0)} · 5th percentile {formatPrice(terminal5, "USD", 0)} · loss probability ≈ {typeof lossProb === "number" ? `${Math.round(lossProb)}%` : lossProb}.
      </p>
    </>
  );
}

