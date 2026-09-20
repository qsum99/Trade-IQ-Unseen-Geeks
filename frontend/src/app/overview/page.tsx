"use client";

import Link from "next/link";
import { useMemo } from "react";
import { ASSETS } from "@/lib/mock-data";
import { formatPercent, formatPrice } from "@/lib/format";
import { Badge, Card, MetricCard, PageHeader } from "@/components/ui";
import { Plot } from "@/components/charts/Plot";
import { useOverviewData } from "@/hooks/useOverviewData";
import { WhatsAppRegistrationBox } from "@/components/whatsapp/WhatsAppRegistrationBox";
import type { Bar } from "@/lib/mock-data";

interface AssetStats {
  last: number;
  chg1d: number;
  vol: number;
  cum: number;
  bars: Bar[];
}

function assetStats(bars: Bar[]): AssetStats | null {
  if (!bars || bars.length < 2) return null;
  const closes = bars.map((b) => b.close);
  const last = closes[closes.length - 1];
  const prev = closes[closes.length - 2];
  const rets = closes.slice(1).map((v, i) => v / closes[i] - 1);
  const mean = rets.reduce((a, b) => a + b, 0) / rets.length;
  const vol = Math.sqrt(rets.reduce((a, b) => a + (b - mean) * (b - mean), 0) / (rets.length - 1)) * Math.sqrt(252);
  const cum = closes[closes.length - 1] / closes[0] - 1;
  return { last, chg1d: last / prev - 1, vol, cum, bars };
}

function maxDrawdown(closes: number[]) {
  let peak = -Infinity;
  let maxDD = 0;
  for (const v of closes) {
    if (v > peak) peak = v;
    if (peak > 0) {
      const dd = (v - peak) / peak;
      if (dd < maxDD) maxDD = dd;
    }
  }
  return maxDD;
}

export default function OverviewPage() {
  const { histories, isLoading, error } = useOverviewData();

  const stats = useMemo(() => {
    if (!histories) return null;
    const newStats: Record<string, ReturnType<typeof assetStats>> = {};
    Object.entries(histories).forEach(([symbol, bars]) => {
      newStats[symbol] = assetStats(bars);
    });
    return newStats;
  }, [histories]);

  const perfTraces = useMemo(() => {
    const traceColors: Record<string, string> = {
      "BTC-USD": "#38bdf8",
      "GC=F": "#f97316",
      "NVDA": "#22c55e",
    };

    return ["BTC-USD", "GC=F", "NVDA"].map((s) => {
      const sData = stats?.[s];
      if (!sData || !sData.bars || sData.bars.length === 0) {
        return { x: [], y: [], type: "scatter" as const, mode: "lines" as const, name: s };
      }
      const base = sData.bars[0]?.close ?? 1;
      return {
        x: sData.bars.map((b) => b.date),
        y: sData.bars.map((b) => (b.close / base) * 100),
        type: "scatter" as const,
        mode: "lines" as const,
        name: s,
        line: { color: traceColors[s] ?? "#6366f1", width: 1.8 },
      };
    });
  }, [stats]);

  const best = useMemo(() => {
    const sorted = [...ASSETS].sort((a, b) => (stats?.[b.symbol]?.cum ?? 0) - (stats?.[a.symbol]?.cum ?? 0));
    return sorted[0] ?? ASSETS[0];
  }, [stats]);

  if (isLoading && !stats) {
    return (
      <div>
        <PageHeader title="Quantitative Market Overview" />
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-(--color-info)"></div>
        </div>
      </div>
    );
  }

  if (error && !stats) {
    return (
      <div>
        <PageHeader title="Quantitative Market Overview" />
        <div className="text-center text-(--color-down) py-8">
          Failed to load market data. Please try again later.
        </div>
      </div>
    );
  }

  if (!stats) {
    return null;
  }

  return (
    <div>
      <PageHeader title="Quantitative Market Overview" />
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <MetricCard label="Market Regime" value="High Vol" hint="Confidence 81% · K-Means" />
        <MetricCard
          label="Best Asset (period)"
          value={best.symbol}
          delta={stats[best.symbol]?.cum ?? 0}
          hint={best.name}
        />
        <MetricCard
          label="NIFTY 50"
          value={formatPrice(stats["^NSEI"]?.last ?? 23201, "INR", 0)}
          delta={stats["^NSEI"]?.chg1d ?? 0.008}
          hint="1D change"
        />
      </div>

      <WhatsAppRegistrationBox className="mt-4" />

      <Card className="mt-4">
        <div className="mb-2 text-sm font-semibold">Market Performance (rebased = 100)</div>
        <Plot data={perfTraces} height={300} />
      </Card>

      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <div className="mb-3 text-sm font-semibold">Asset Snapshot</div>
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-(--color-muted)">
                <th className="py-1.5 pr-2">Asset</th>
                <th className="py-1.5 px-3 text-right">Price</th>
                <th className="py-1.5 px-3 text-right">1D</th>
                <th className="py-1.5 pl-3 text-right">Vol (ann.)</th>
              </tr>
            </thead>
            <tbody>
              {ASSETS.map((a) => {
                const s = stats[a.symbol];
                if (!s) return null;
                return (
                  <tr key={a.symbol} className="border-t border-(--color-edge)">
                    <td className="py-2.5 pr-2">
                      <Link href={`/assets/${encodeURIComponent(a.symbol)}`} className="font-medium hover:underline">
                        {a.symbol}
                      </Link>
                      <span className="ml-2 text-xs text-(--color-muted)">{a.name}</span>
                    </td>
                    <td className="tnum px-3 text-right">{formatPrice(s.last, a.currency, a.currency === "INR" ? 0 : 2)}</td>
                    <td className={`tnum px-3 text-right ${s.chg1d >= 0 ? "text-(--color-up)" : "text-(--color-down)"}`}>
                      {formatPercent(s.chg1d)}
                    </td>
                    <td className="tnum pl-3 text-right">{formatPercent(s.vol)}</td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </Card>
        <div className="flex flex-col gap-4">
          <Card>
            <div className="mb-2 flex items-center justify-between">
              <span className="text-sm font-semibold">Market Regime</span>
              <Badge tone="warn">High Volatility</Badge>
            </div>
            <p className="text-sm text-(--color-muted)">
              Current: <span className="font-medium text-(--color-ink)">High Volatility</span> · Confidence 81% ·
              Model K-Means. Max drawdown (BTC, period):{" "}
              <span className="tnum">{formatPercent(maxDrawdown(stats["BTC-USD"]?.bars.map((b) => b.close) ?? []))}</span>
            </p>
            <Link href="/regimes" className="mt-2 inline-block text-sm font-medium text-(--color-info)">
              View regime intelligence →
            </Link>
          </Card>
          <Card>
            <div className="mb-2 text-sm font-semibold">Recent Research</div>
            <ul className="space-y-2 text-sm">
              <li><Link href="/backtesting" className="hover:underline">EMA BTC backtest</Link> <Badge tone="positive">Complete</Badge></li>
              <li><Link href="/backtesting" className="hover:underline">NVDA SMA 20/50 backtest</Link> <Badge tone="positive">Complete</Badge></li>
              <li><Link href="/regimes" className="hover:underline">BTC regime analysis</Link> <Badge tone="info">K-Means</Badge></li>
            </ul>
          </Card>
        </div>
      </div>
      <p className="mt-6 text-xs text-(--color-muted)">
        Research workspace. Historical performance does not guarantee future returns.
      </p>
    </div>
  );
}
