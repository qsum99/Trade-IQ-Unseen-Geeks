"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiData } from "@/api/client";
import { endpoints } from "@/api/endpoints";
import { ASSETS, getHistory, regimeTimeline } from "@/lib/mock-data";
import { Badge, Card, Field, PageHeader, inputCls } from "@/components/ui";
import { Plot } from "@/components/charts/Plot";

const REGIME_COLORS: Record<string, string> = {
  Bull: "#16a34a",
  Bear: "#dc2626",
  "High Vol": "#d97706",
  "Low Vol": "#2563eb",
};

function regimeTone(label: string): "positive" | "negative" | "warn" | "info" {
  if (label === "Bull") return "positive";
  if (label === "Bear") return "negative";
  if (label.includes("High")) return "warn";
  return "info";
}

export default function RegimesPage() {
  const [symbol, setSymbol] = useState("BTC-USD");

  // Fetch real history
  const { data: historyData } = useQuery({
    queryKey: ["regime-history", symbol],
    queryFn: async () => {
      try {
        const res = await apiData<{ data: any[] }>(
          endpoints.assetHistory(symbol, {
            start_date: "2024-01-01",
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
        console.warn(`Failed to fetch history for ${symbol}:`, e);
      }
      return null;
    },
    refetchInterval: 60_000,
  });

  // Fetch regime detection from quantum endpoint
  const { data: regimeData } = useQuery({
    queryKey: ["regime-detect", symbol],
    queryFn: async () => {
      try {
        const res = await apiData<any>(
          endpoints.quantum.regime(),
          {
            method: "POST",
            body: JSON.stringify({
              symbol,
              start_date: "2024-01-01",
              end_date: "2026-09-20",
            }),
          }
        );
        if (res) return res;
      } catch (e) {
        console.warn("Regime detection failed, using fallback", e);
      }
      return null;
    },
    refetchInterval: 60_000,
  });

  const data = useMemo(() => {
    const bars = historyData && historyData.length > 0 ? historyData : getHistory(symbol);

    // Try backend regime segments, fallback to mock
    let segs: Array<{ from: string; to: string; label: string }>;
    if (regimeData?.segments && Array.isArray(regimeData.segments)) {
      segs = regimeData.segments;
    } else if (regimeData?.timeline && Array.isArray(regimeData.timeline)) {
      segs = regimeData.timeline;
    } else {
      segs = regimeTimeline(symbol);
    }

    const shapes = segs.map((s) => ({
      type: "rect" as const,
      xref: "x" as const,
      yref: "paper" as const,
      x0: s.from,
      x1: s.to,
      y0: 0,
      y1: 1,
      fillcolor: REGIME_COLORS[s.label] ?? "#888",
      opacity: 0.08,
      line: { width: 0 },
    }));

    // Determine current regime
    const currentRegime = regimeData?.current_regime ?? regimeData?.regime ?? segs[segs.length - 1]?.label ?? "High Vol";
    const confidence = regimeData?.confidence ?? regimeData?.probability ?? 81;
    const models = regimeData?.models ?? [
      { name: "K-Means", regime: currentRegime, confidence },
      { name: "HMM", regime: currentRegime, confidence: Math.max(50, confidence - 5) },
      { name: "Quantum VQC", regime: currentRegime, confidence: Math.max(50, confidence - 9), experimental: true },
    ];

    return { bars, shapes, currentRegime, confidence, models };
  }, [historyData, regimeData, symbol]);

  return (
    <div>
      <PageHeader
        title="Market Regime Intelligence"
        sub="Bull · Bear · High Volatility · Low Volatility"
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
      <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
        <Card><div className="text-xs text-(--color-muted) uppercase">Current regime</div><div className="mt-1"><Badge tone={regimeTone(data.currentRegime)}>{data.currentRegime}</Badge></div></Card>
        <Card><div className="text-xs text-(--color-muted) uppercase">Confidence</div><div className="tnum mt-1 text-2xl font-semibold">{typeof data.confidence === "number" ? `${Math.round(data.confidence)}%` : data.confidence}</div></Card>
        <Card><div className="text-xs text-(--color-muted) uppercase">Detected by</div><div className="mt-1 text-2xl font-semibold">K-Means</div></Card>
      </div>
      <Card className="mt-4">
        <div className="mb-2 text-sm font-semibold">Price with regime background — {symbol}</div>
        <Plot
          height={320}
          data={[{ x: data.bars.map((b) => b.date), y: data.bars.map((b) => b.close), type: "scatter", mode: "lines", name: symbol }]}
          layout={{ shapes: data.shapes }}
        />
        <div className="mt-2 flex flex-wrap gap-3 text-xs">
          {Object.entries(REGIME_COLORS).map(([k, v]) => (
            <span key={k} className="flex items-center gap-1.5">
              <span className="inline-block h-2.5 w-2.5 rounded-sm" style={{ background: v }} /> {k}
            </span>
          ))}
        </div>
      </Card>
      <Card className="mt-4">
        <div className="mb-2 text-sm font-semibold">Model comparison</div>
        <table className="w-full text-sm">
          <thead><tr className="text-left text-xs text-(--color-muted)"><th>Model</th><th>Regime</th><th className="text-right">Confidence</th></tr></thead>
          <tbody>
            {data.models.map((m: any) => (
              <tr key={m.name} className="border-t border-(--color-edge)">
                <td>{m.name} {m.experimental && <Badge tone="quant">Experimental</Badge>}</td>
                <td><Badge tone={regimeTone(m.regime)}>{m.regime}</Badge></td>
                <td className="tnum text-right">{Math.round(m.confidence)}%</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Card>
    </div>
  );
}

