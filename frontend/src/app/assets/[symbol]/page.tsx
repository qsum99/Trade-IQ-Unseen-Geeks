"use client";

import { useMemo, useState } from "react";
import { useParams } from "next/navigation";
import { ASSETS } from "@/lib/mock-data";
import { formatPercent, formatPrice } from "@/lib/format";
import { Card, MetricCard, PageHeader, Tabs } from "@/components/ui";
import { Plot } from "@/components/charts/Plot";
import { useQuery } from "@tanstack/react-query";
import { apiData } from "@/api/client";
import { endpoints } from "@/api/endpoints";
import type { Bar } from "@/lib/mock-data";

const RANGES = [90, 180, 365, 760];

interface AssetHistoryResponse {
  symbol: string;
  interval: string;
  currency: string;
  data: Array<{
    timestamp: string;
    open: number;
    high: number;
    low: number;
    close: number;
    adjusted_close: number | null;
    volume: number | null;
    currency: string;
    exchange: string;
    provider: string;
    interval: string;
  }>;
}

function drawdownSeries(closes: number[]) {
  let peak = -Infinity;
  const dd: number[] = [];
  for (const v of closes) {
    if (v > peak) peak = v;
    dd.push(peak > 0 ? (v - peak) / peak : 0);
  }
  return dd;
}

function smaOf(values: number[], period: number) {
  const out: (number | null)[] = [];
  for (let i = 0; i < values.length; i++) {
    if (i < period - 1) {
      out.push(null);
    } else {
      let sum = 0;
      for (let j = i - period + 1; j <= i; j++) sum += values[j];
      out.push(sum / period);
    }
  }
  return out;
}

function emaOf(values: number[], period: number) {
  const k = 2 / (period + 1);
  const out: (number | null)[] = [];
  let ema: number | null = null;
  for (let i = 0; i < values.length; i++) {
    if (ema === null) {
      ema = values[i];
    } else {
      ema = values[i] * k + ema * (1 - k);
    }
    out.push(ema);
  }
  return out;
}

export default function AssetDetailPage() {
  const params = useParams();
  const symbol = decodeURIComponent((params.symbol as string) ?? "NVDA");
  const meta = ASSETS.find((a) => a.symbol === symbol) ?? ASSETS[3];
  const [range, setRange] = useState(365);
  const [tab, setTab] = useState("Overview");

const { data: historyData, isLoading, error } = useQuery({
    queryKey: ["asset-history", symbol, range],
    queryFn: async () => {
      const response = await fetch(
        `/api/v1/assets/${encodeURIComponent(symbol)}/history?start_date=${new Date(Date.now() - range * 24 * 60 * 60 * 1000).toISOString().split('T')[0]}&end_date=${new Date().toISOString().split('T')[0]}&interval=1d`
      );
      const data = await response.json();
      if (!data.success) throw new Error(data.error?.message || "Failed to fetch history");
      return data.data;
    },
    enabled: !!symbol,
  });

  const data = useMemo(() => {
    if (!historyData || !Array.isArray(historyData.data)) return null;
    const bars: Bar[] = historyData.data.map((d: any) => ({
      date: d.date ?? (d.timestamp ? d.timestamp.split("T")[0] : ""),
      open: Number(d.open),
      high: Number(d.high),
      low: Number(d.low),
      close: Number(d.close),
      volume: Number(d.volume ?? 0),
    }));
    const closes = bars.map((b: Bar) => b.close);
    const sma20 = smaOf(closes, 20);
    const sma100 = smaOf(closes, 100);
    const rets: number[] = closes.slice(1).map((v: number, i: number): number => v / closes[i] - 1);
    const mean = rets.reduce((a: number, b: number): number => a + b, 0) / rets.length;
    const vol = Math.sqrt(rets.reduce((a: number, b: number): number => a + (b - mean) * (b - mean), 0) / (rets.length - 1)) * Math.sqrt(252);
    const cum = closes[closes.length - 1] / closes[0] - 1;
    const dd = drawdownSeries(closes);
    const rvol: (number | null)[] = closes.map((_: number, i: number): number | null => {
      if (i < 31) return null;
      const w = rets.slice(i - 30, i);
      const m = w.reduce((a: number, b: number): number => a + b, 0) / w.length;
      return Math.sqrt(w.reduce((a: number, b: number): number => a + (b - m) * (b - m), 0) / (w.length - 1)) * Math.sqrt(252);
    });
    return { bars, closes, sma20, sma100, rets, vol, cum, dd, rvol };
  }, [historyData, range]);

  const last = data?.closes[data.closes.length - 1];
  const chg = last && data?.closes.length > 1 ? last / data.closes[data.closes.length - 2] - 1 : 0;
  const dates = data?.bars.map((b: Bar) => b.date) ?? [];

  if (isLoading) {
    return (
      <div>
        <PageHeader
          title={`${meta.symbol} / ${meta.currency}`}
          sub={`${meta.name} · ${meta.exchange} · Source: ${meta.provider}`}
        />
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-(--color-info)"></div>
        </div>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div>
        <PageHeader
          title={`${meta.symbol} / ${meta.currency}`}
          sub={`${meta.name} · ${meta.exchange} · Source: ${meta.provider}`}
        />
        <div className="text-center text-(--color-down) py-8">
          Failed to load asset data. Please try again later.
        </div>
      </div>
    );
  }

  return (
    <div>
      <PageHeader
        title={`${meta.symbol} / ${meta.currency}`}
        sub={`${meta.name} · ${meta.exchange} · Source: ${meta.provider}`}
        right={
          <div className="flex gap-1">
            {RANGES.map((r) => (
              <button
                key={r}
                onClick={() => setRange(r)}
                className={`rounded-lg px-2.5 py-1 text-xs font-medium ${range === r ? "bg-(--color-ink) text-(--color-elev)" : "bg-(--color-elev) text-(--color-muted)"}`}
              >
                {r >= 760 ? "MAX" : r >= 365 ? "1Y" : r >= 180 ? "6M" : "3M"}
              </button>
            ))}
          </div>
        }
      />
      <div className="mb-4 flex items-baseline gap-3">
        <span className="tnum text-3xl font-semibold">{formatPrice(last, meta.currency, meta.currency === "INR" ? 0 : 2)}</span>
        <span className={`tnum text-lg ${chg >= 0 ? "text-(--color-up)" : "text-(--color-down)"}`}>{formatPercent(chg)}</span>
      </div>

      <Tabs tabs={["Overview", "Returns", "Volatility", "Drawdown"]} active={tab} onChange={setTab} />

      {tab === "Overview" && (
        <Card>
          <Plot
            height={380}
            data={[
              {
                x: dates, open: data.bars.map((b: Bar) => b.open), high: data.bars.map((b: Bar) => b.high),
                low: data.bars.map((b: Bar) => b.low), close: data.closes, type: "candlestick", name: meta.symbol,
              },
              { x: dates, y: data.sma20, type: "scatter", mode: "lines", name: "SMA 20", line: { width: 1.2, color: "#2563eb" } },
              { x: dates, y: data.sma100, type: "scatter", mode: "lines", name: "SMA 100", line: { width: 1.2, color: "#d97706" } },
            ]}
            layout={{ xaxis: { rangeslider: { visible: false } } }}
          />
        </Card>
      )}
      {tab === "Returns" && (
        <Card>
          <Plot
            height={320}
            data={[{ x: dates.slice(1), y: data.rets, type: "bar", name: "Daily return", marker: { color: "#2563eb" } }]}
          />
        </Card>
      )}
      {tab === "Volatility" && (
        <Card>
          <Plot
            height={320}
            data={[{ x: dates, y: data.rvol, type: "scatter", mode: "lines", name: "30D rolling vol (ann.)", line: { color: "#7c3aed" } }]}
            layout={{ yaxis: { tickformat: ".0%" } }}
          />
        </Card>
      )}
      {tab === "Drawdown" && (
        <Card>
          <Plot
            height={320}
            data={[{ x: dates, y: data.dd, type: "scatter", mode: "lines", fill: "tozeroy", name: "Drawdown", line: { color: "#dc2626" } }]}
            layout={{ yaxis: { tickformat: ".0%" } }}
          />
        </Card>
      )}

      <div className="mt-4 grid grid-cols-2 gap-4 lg:grid-cols-4">
        <MetricCard label="Cumulative" value={formatPercent(data.cum)} delta={data.cum} />
        <MetricCard label="Volatility (ann.)" value={formatPercent(data.vol)} />
        <MetricCard label="Max Drawdown" value={formatPercent(Math.min(...data.dd))} delta={Math.min(...data.dd)} />
        <MetricCard label="EMA-20 last" value={formatPrice(emaOf(data.closes, 20).filter(Boolean).pop() as number, meta.currency, 2)} />
      </div>
    </div>
  );
}