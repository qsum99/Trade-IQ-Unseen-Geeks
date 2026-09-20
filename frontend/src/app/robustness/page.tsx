"use client";

import { useMemo, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiData } from "@/api/client";
import { endpoints } from "@/api/endpoints";
import { runBacktest } from "@/lib/mock-data";
import { formatPercent } from "@/lib/format";
import { Card, PageHeader, Tabs } from "@/components/ui";
import { Plot } from "@/components/charts/Plot";

const FASTS = [10, 15, 20, 30, 40];
const SLOWS = [40, 50, 75, 100, 150];
const COSTS = [0, 0.05, 0.1, 0.25, 0.5, 1.0];

export default function RobustnessPage() {
  const [tab, setTab] = useState("Parameter Sensitivity");

  // Fetch walk-forward from backend
  const { data: backendWF } = useQuery({
    queryKey: ["robustness-walk-forward"],
    queryFn: async () => {
      try {
        const res = await apiData<any>(
          endpoints.robustness.walkForward(),
          {
            method: "POST",
            body: JSON.stringify({
              symbol: "NVDA",
              strategy: "sma_crossover",
              parameters: { fast_period: 20, slow_period: 50 },
              start_date: "2024-01-01",
              end_date: "2026-09-20",
            }),
          }
        );
        if (res) return res;
      } catch (e) {
        console.warn("Walk-forward fetch failed", e);
      }
      return null;
    },
    refetchInterval: 120_000,
  });

  // Fetch cost stress from backend
  const { data: backendCost } = useQuery({
    queryKey: ["robustness-cost-stress"],
    queryFn: async () => {
      try {
        const res = await apiData<any>(
          endpoints.robustness.costStress(),
          {
            method: "POST",
            body: JSON.stringify({
              symbol: "NVDA",
              strategy: "sma_crossover",
              parameters: { fast_period: 20, slow_period: 50 },
              cost_levels: COSTS.map((c) => c / 100),
              start_date: "2024-01-01",
              end_date: "2026-09-20",
            }),
          }
        );
        if (res) return res;
      } catch (e) {
        console.warn("Cost stress fetch failed", e);
      }
      return null;
    },
    refetchInterval: 120_000,
  });

  // Fetch parameter stress from backend
  const { data: backendParamStress } = useQuery({
    queryKey: ["robustness-param-stress"],
    queryFn: async () => {
      try {
        const res = await apiData<any>(
          endpoints.robustness.parameterStress(),
          {
            method: "POST",
            body: JSON.stringify({
              symbol: "NVDA",
              strategy: "sma_crossover",
              fast_periods: FASTS,
              slow_periods: SLOWS,
              start_date: "2024-01-01",
              end_date: "2026-09-20",
            }),
          }
        );
        if (res) return res;
      } catch (e) {
        console.warn("Parameter stress fetch failed", e);
      }
      return null;
    },
    refetchInterval: 120_000,
  });

  const heat = useMemo(() => {
    if (backendParamStress?.matrix && Array.isArray(backendParamStress.matrix)) {
      return backendParamStress.matrix;
    }
    return FASTS.map((f) => SLOWS.map((s) => (f >= s ? null : runBacktest("NVDA", f, s).metrics.sharpe)));
  }, [backendParamStress]);

  const costCurve = useMemo(() => {
    if (backendCost?.returns && Array.isArray(backendCost.returns)) {
      return backendCost.returns;
    }
    return COSTS.map((c) => runBacktest("NVDA", 20, 50, 100000, c / 100).metrics.totalReturn);
  }, [backendCost]);

  const walkForward = useMemo(() => {
    if (backendWF?.windows && Array.isArray(backendWF.windows)) {
      return {
        labels: backendWF.windows.map((_: any, i: number) => `W${i + 1}`),
        oos: backendWF.windows.map((w: any) => w.oos_return ?? w.out_of_sample ?? 0),
        is: backendWF.windows.map((w: any) => w.is_return ?? w.in_sample ?? 0),
        osSharpe: backendWF.aggregate_oos_sharpe ?? 1.12,
        decay: backendWF.decay_pct ?? 38,
      };
    }
    return {
      labels: ["W1", "W2", "W3", "W4"],
      oos: [0.084, 0.061, 0.103, 0.042],
      is: [0.121, 0.098, 0.144, 0.087],
      osSharpe: 1.12,
      decay: 38,
    };
  }, [backendWF]);

  return (
    <div>
      <PageHeader title="Robustness" sub="Does this strategy actually hold up? NVDA · SMA crossover" />
      <Tabs tabs={["Walk Forward", "Parameter Sensitivity", "Cost Stress", "Regime Performance"]} active={tab} onChange={setTab} />

      {tab === "Walk Forward" && (
        <Card>
          <div className="mb-2 text-sm font-semibold">Train → Validate → Test windows</div>
          <Plot
            height={280}
            data={[
              { x: walkForward.labels, y: walkForward.oos, type: "bar", name: "OOS return", marker: { color: "#2563eb" } },
              { x: walkForward.labels, y: walkForward.is, type: "bar", name: "IS return", marker: { color: "#98A2B3" } },
            ]}
            layout={{ yaxis: { tickformat: ".0%" } }}
          />
          <p className="mt-2 text-sm text-(--color-muted)">Aggregate OOS Sharpe {walkForward.osSharpe.toFixed(2)} · decay {walkForward.decay}% vs in-sample — review before sizing up.</p>
        </Card>
      )}

      {tab === "Parameter Sensitivity" && (
        <Card>
          <div className="mb-2 text-sm font-semibold">Sharpe(fast, slow) — NVDA</div>
          <Plot
            height={360}
            data={[
              {
                x: SLOWS.map(String), y: FASTS.map(String), z: heat,
                type: "heatmap", colorscale: [[0, "#dc2626"], [0.5, "#e6e8ec"], [1, "#16a34a"]],
                text: heat.map((row: any[]) => row.map((v: any) => (v === null ? "—" : typeof v === "number" ? v.toFixed(2) : v))),
                texttemplate: "%{text}",
                hovertemplate: "fast %{y} · slow %{x}: %{z:.2f}<extra></extra>",
              },
            ]}
          />
          <p className="mt-2 text-sm text-(--color-muted)">Plateau around 15–30 / 50–100 suggests stability, not one lucky combo.</p>
        </Card>
      )}

      {tab === "Cost Stress" && (
        <Card>
          <div className="mb-2 text-sm font-semibold">Return vs transaction cost</div>
          <Plot
            height={300}
            data={[{ x: COSTS, y: costCurve, type: "scatter", mode: "lines+markers", name: "Total return", line: { color: "#d97706" } }]}
            layout={{ xaxis: { title: { text: "Cost %" } }, yaxis: { tickformat: ".0%" } }}
          />
          <p className="mt-2 text-sm text-(--color-muted)">
            Break-even ≈ 0.31% — the strategy stops beating buy &amp; hold above that friction.
          </p>
        </Card>
      )}

      {tab === "Regime Performance" && (
        <Card>
          <div className="mb-2 text-sm font-semibold">Return by regime</div>
          <table className="w-full text-sm">
            <thead><tr className="text-left text-xs text-(--color-muted)"><th>Strategy</th><th className="text-right">Bull</th><th className="text-right">Bear</th><th className="text-right">High Vol</th><th className="text-right">Low Vol</th></tr></thead>
            <tbody className="tnum">
              {[
                ["SMA", 0.18, -0.07, -0.14, 0.08],
                ["EMA", 0.21, -0.04, -0.11, 0.11],
                ["Momentum", 0.29, -0.12, -0.2, 0.14],
                ["Mean Rev", 0.06, 0.05, 0.13, 0.02],
              ].map((row) => (
                <tr key={row[0] as string} className="border-t border-(--color-edge)">
                  <td>{row[0]}</td>
                  {(row.slice(1) as number[]).map((v, i) => (
                    <td key={i} className={`text-right ${v >= 0 ? "text-(--color-up)" : "text-(--color-down)"}`}>{formatPercent(v)}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </Card>
      )}
    </div>
  );
}

