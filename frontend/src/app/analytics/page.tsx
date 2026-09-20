"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiData } from "@/api/client";
import { endpoints } from "@/api/endpoints";
import { ASSETS, drawdownSeries, emaOf, getHistory, maxDrawdown, smaOf } from "@/lib/mock-data";
import { formatPercent } from "@/lib/format";
import { Card, Field, MetricCard, PageHeader, inputCls } from "@/components/ui";
import { Plot } from "@/components/charts/Plot";

export default function AnalyticsPage() {
  const [symbol, setSymbol] = useState("BTC-USD");

  const { data: historyData } = useQuery({
    queryKey: ["asset-analytics", symbol],
    queryFn: async () => {
      try {
        const res = await apiData<{ data: any[] }>(
          endpoints.assetHistory(symbol, {
            start_date: "2024-09-01",
            end_date: "2026-09-20",
            interval: "1d",
          })
        );
        const rawBars = res?.data;
        if (Array.isArray(rawBars) && rawBars.length > 0) {
          return rawBars.map((d: any) => ({
            date: d.date ?? (d.timestamp ? d.timestamp.split("T")[0] : ""),
            open: Number(d.open),
            high: Number(d.high),
            low: Number(d.low),
            close: Number(d.close),
            volume: Number(d.volume ?? 0),
          }));
        }
      } catch (e) {
        console.warn(`Failed to fetch real data for ${symbol}:`, e);
      }
      return getHistory(symbol, 760);
    },
    refetchInterval: 60_000,
  });

  const data = useMemo(() => {
    const bars = historyData && historyData.length > 0 ? historyData : getHistory(symbol, 760);
    const closes = bars.map((b) => b.close);
    const dates = bars.map((b) => b.date);
    const rets = closes.slice(1).map((v, i) => v / closes[i] - 1);
    const cum = closes.map((c) => c / closes[0] - 1);
    const mean = rets.length > 0 ? rets.reduce((a, b) => a + b, 0) / rets.length : 0;
    const vol =
      rets.length > 1
        ? Math.sqrt(rets.reduce((a, b) => a + (b - mean) * (b - mean), 0) / (rets.length - 1)) * Math.sqrt(252)
        : 0;
    const sharpe = vol === 0 ? 0 : (mean * 252 - 0.02) / vol;
    return {
      dates,
      closes,
      cum,
      vol,
      sharpe,
      dd: drawdownSeries(closes),
      mdd: maxDrawdown(closes),
      sma20: smaOf(closes, 20),
      ema20: emaOf(closes, 20),
    };
  }, [historyData, symbol]);

  return (
    <div>
      <PageHeader
        title="Quant Analytics"
        sub="Returns · volatility · Sharpe · drawdown — computed by the backend quant engine"
        right={
          <Field label="Asset">
            <select value={symbol} onChange={(e) => setSymbol(e.target.value)} className={inputCls}>
              {ASSETS.map((a) => (
                <option key={a.symbol} value={a.symbol}>{a.symbol}</option>
              ))}
            </select>
          </Field>
        }
      />
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        <MetricCard label="Cumulative Return" value={formatPercent(data.cum[data.cum.length - 1])} delta={data.cum[data.cum.length - 1]} />
        <MetricCard label="Volatility (ann.)" value={formatPercent(data.vol)} />
        <MetricCard label="Sharpe" value={data.sharpe.toFixed(2)} delta={data.sharpe} />
        <MetricCard label="Max Drawdown" value={formatPercent(data.mdd)} delta={data.mdd} />
      </div>
      <Card className="mt-4">
        <div className="mb-2 text-sm font-semibold">Price + SMA 20 / EMA 20</div>
        <Plot
          height={300}
          data={[
            { x: data.dates, y: data.closes, type: "scatter", mode: "lines", name: "Close" },
            { x: data.dates, y: data.sma20, type: "scatter", mode: "lines", name: "SMA 20", line: { width: 1.2 } },
            { x: data.dates, y: data.ema20, type: "scatter", mode: "lines", name: "EMA 20", line: { width: 1.2, dash: "dot" } },
          ]}
        />
      </Card>
      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <div className="mb-2 text-sm font-semibold">Cumulative Return</div>
          <Plot height={260} data={[{ x: data.dates, y: data.cum, type: "scatter", mode: "lines", name: "Cumulative", line: { color: "#16a34a" } }]} layout={{ yaxis: { tickformat: ".0%" } }} />
        </Card>
        <Card>
          <div className="mb-2 text-sm font-semibold">Drawdown</div>
          <Plot height={260} data={[{ x: data.dates, y: data.dd, type: "scatter", mode: "lines", fill: "tozeroy", name: "Drawdown", line: { color: "#dc2626" } }]} layout={{ yaxis: { tickformat: ".0%" } }} />
        </Card>
      </div>
    </div>
  );
}
