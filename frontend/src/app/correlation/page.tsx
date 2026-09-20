"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiData } from "@/api/client";
import { endpoints } from "@/api/endpoints";
import { corrMatrix, rollingCorr } from "@/lib/mock-data";
import { AssetSearch } from "@/components/AssetSearch";
import { Badge, Card, Field, PageHeader, inputCls } from "@/components/ui";
import { Plot } from "@/components/charts/Plot";

const DEFAULT_SYMS = ["BTC-USD", "GC=F", "NVDA", "^NSEI"];

export default function CorrelationPage() {
  const [window, setWindow] = useState(60);
  const [symbols, setSymbols] = useState<string[]>(DEFAULT_SYMS);

  const { data: backendMatrix } = useQuery({
    queryKey: ["corr-matrix", symbols],
    queryFn: async () => {
      try {
        const res = await apiData<{ symbols: string[]; matrix: number[][] }>(
          endpoints.correlation.matrix(),
          {
            method: "POST",
            body: JSON.stringify({
              symbols,
              start_date: "2024-09-01",
              end_date: "2026-09-20",
            }),
          }
        );
        if (res?.matrix && Array.isArray(res.matrix)) {
          return res;
        }
      } catch (err) {
        console.warn("Backend correlation matrix failed, using fallback", err);
      }
      return null;
    },
    refetchInterval: 60_000,
  });

  const { data: backendRoll1 } = useQuery({
    queryKey: ["corr-rolling-btc-gold", window],
    queryFn: async () => {
      try {
        const res = await apiData<{ series: Array<{ date: string; [k: string]: any }> }>(
          endpoints.correlation.rolling(),
          {
            method: "POST",
            body: JSON.stringify({
              symbols: ["BTC-USD", "GC=F"],
              window,
              start_date: "2024-09-01",
              end_date: "2026-09-20",
            }),
          }
        );
        if (res?.series && Array.isArray(res.series)) {
          return res.series.map((s) => ({
            date: s.date,
            value: Number(s["BTC-USD__GC=F"] ?? s["BTC-USD_GC=F"] ?? Object.values(s).find((v) => typeof v === "number") ?? 0),
          }));
        }
      } catch (e) {
        console.warn("Rolling BTC-GC failed, using fallback", e);
      }
      return null;
    },
    refetchInterval: 60_000,
  });

  const { data: backendRoll2 } = useQuery({
    queryKey: ["corr-rolling-btc-nvda", window],
    queryFn: async () => {
      try {
        const res = await apiData<{ series: Array<{ date: string; [k: string]: any }> }>(
          endpoints.correlation.rolling(),
          {
            method: "POST",
            body: JSON.stringify({
              symbols: ["BTC-USD", "NVDA"],
              window,
              start_date: "2024-09-01",
              end_date: "2026-09-20",
            }),
          }
        );
        if (res?.series && Array.isArray(res.series)) {
          return res.series.map((s) => ({
            date: s.date,
            value: Number(s["BTC-USD__NVDA"] ?? s["BTC-USD_NVDA"] ?? Object.values(s).find((v) => typeof v === "number") ?? 0),
          }));
        }
      } catch (e) {
        console.warn("Rolling BTC-NVDA failed, using fallback", e);
      }
      return null;
    },
    refetchInterval: 60_000,
  });

  const matrix = useMemo(() => {
    if (backendMatrix) return backendMatrix;
    return corrMatrix(symbols);
  }, [backendMatrix, symbols]);

  const roll1 = useMemo(() => {
    if (backendRoll1 && backendRoll1.length > 0) return backendRoll1;
    return rollingCorr("BTC-USD", "GC=F", window);
  }, [backendRoll1, window]);

  const roll2 = useMemo(() => {
    if (backendRoll2 && backendRoll2.length > 0) return backendRoll2;
    return rollingCorr("BTC-USD", "NVDA", window);
  }, [backendRoll2, window]);

  const add = (s: string) => setSymbols((prev) => (prev.includes(s) ? prev : [...prev, s].slice(0, 8)));
  const remove = (s: string) => setSymbols((prev) => (prev.length <= 2 ? prev : prev.filter((x) => x !== s)));

  return (
    <div>
      <PageHeader
        title="Correlation"
        sub="Cross-asset relationships and how they drift over time"
        right={
          <div className="flex items-end gap-3">
            <AssetSearch label="Assets" onAdd={add} exclude={symbols} />
            <Field label="Rolling window (days)">
              <select value={window} onChange={(e) => setWindow(Number(e.target.value))} className={inputCls}>
                {[30, 60, 90, 120].map((w) => (
                  <option key={w} value={w}>{w}</option>
                ))}
              </select>
            </Field>
          </div>
        }
      />

      <div className="mb-3 flex flex-wrap gap-2">
        {symbols.map((s) => (
          <button
            key={s}
            onClick={() => remove(s)}
            title={symbols.length > 2 ? "Remove from matrix" : "Keep at least 2 assets"}
            className="inline-flex items-center gap-1.5 rounded-full bg-(--color-surface) border border-(--color-edge) px-3 py-1 text-xs font-medium hover:border-(--color-down)"
          >
            {s} <span className="text-(--color-muted)">×</span>
          </button>
        ))}
        <span className="self-center text-xs text-(--color-muted)">Matrix: {symbols.length} assets · click × to remove (min 2, max 8)</span>
      </div>

      <Card>
        <div className="mb-2 flex items-center justify-between">
          <span className="text-sm font-semibold">Correlation Matrix (daily returns, 1Y)</span>
          <Badge tone="info">{symbols.length}×{symbols.length}</Badge>
        </div>
        <Plot
          height={Math.max(320, 120 + symbols.length * 56)}
          data={[
            {
              x: matrix.symbols,
              y: matrix.symbols,
              z: matrix.matrix,
              type: "heatmap",
              colorscale: [
                [0, "#dc2626"],
                [0.5, "#e6e8ec"],
                [1, "#16a34a"],
              ],
              zmin: -1,
              zmax: 1,
              text: matrix.matrix.map((row) => row.map((v) => v.toFixed(2))),
              texttemplate: "%{text}",
              hovertemplate: "%{y} ↔ %{x}: %{z:.2f}<extra></extra>",
            },
          ]}
          layout={{ xaxis: { automargin: true }, yaxis: { automargin: true } }}
        />
      </Card>
      <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card>
          <div className="mb-2 text-sm font-semibold">BTC ↔ GOLD (rolling)</div>
          <Plot height={260} data={[{ x: roll1.map((r) => r.date), y: roll1.map((r) => r.value), type: "scatter", mode: "lines", name: "BTC–GOLD", line: { color: "#d4af37" } }]} />
        </Card>
        <Card>
          <div className="mb-2 text-sm font-semibold">BTC ↔ NVDA (rolling)</div>
          <Plot height={260} data={[{ x: roll2.map((r) => r.date), y: roll2.map((r) => r.value), type: "scatter", mode: "lines", name: "BTC–NVDA", line: { color: "#76b900" } }]} />
        </Card>
      </div>
    </div>
  );
}
