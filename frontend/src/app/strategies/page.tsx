"use client";

import Link from "next/link";
import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { apiData } from "@/api/client";
import { endpoints } from "@/api/endpoints";
import { ASSETS, runBacktest } from "@/lib/mock-data";
import { formatPercent } from "@/lib/format";
import { Badge, Card, PageHeader } from "@/components/ui";
import { BacktestModal } from "@/components/BacktestModal";

const FALLBACK_STRATEGIES = [
  { id: "sma_crossover", name: "SMA Crossover", desc: "Fast SMA crossing above slow SMA → long, cross below → flat.", params: "Fast 20 · Slow 50" },
  { id: "ema_trend", name: "EMA Trend", desc: "Price above EMA-50 with rising slope → long.", params: "EMA 50 · Slope 5d" },
  { id: "momentum", name: "Momentum", desc: "20-day return above threshold → long.", params: "Lookback 20d · Threshold 2%" },
  { id: "mean_reversion", name: "Mean Reversion", desc: "Z-score below −2 → long, above +2 → flat.", params: "Window 20 · |Z| 2.0" },
  { id: "buy_and_hold", name: "Buy & Hold", desc: "Benchmark: buy at start, hold to end.", params: "—" },
  { id: "regime_adaptive", name: "Regime Adaptive", desc: "Momentum in bull, mean reversion in high-vol.", params: "Model K-Means" },
];

export default function StrategiesPage() {
  const [modal, setModal] = useState<{ id: string; name: string } | null>(null);

  // Fetch strategies from backend
  const { data: backendStrategies } = useQuery({
    queryKey: ["strategies-list"],
    queryFn: async () => {
      try {
        const res = await apiData<any[]>(endpoints.strategies());
        if (Array.isArray(res) && res.length > 0) {
          return res.map((s: any) => ({
            id: s.id,
            name: s.name,
            desc: s.description ?? s.desc ?? "",
            params: s.parameters
              ? s.parameters.map((p: any) => `${p.name}: ${p.default}`).join(" · ")
              : "—",
          }));
        }
      } catch (e) {
        console.warn("Failed to fetch strategies, using fallback", e);
      }
      return null;
    },
    refetchInterval: 120_000,
  });

  const strategies = backendStrategies ?? FALLBACK_STRATEGIES;

  return (
    <div>
      <PageHeader title="Strategies" sub="Signal library — every card can be launched into the backtester" />
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {strategies.map((s) => {
          const bt = runBacktest("NVDA", 20, 50);
          return (
            <Card key={s.id}>
              <div className="flex items-center justify-between">
                <span className="font-semibold">{s.name}</span>
                <Badge tone="info">NVDA {formatPercent(bt.metrics.totalReturn)}</Badge>
              </div>
              <p className="mt-1 text-sm text-(--color-muted)">{s.desc}</p>
              <div className="mt-2 text-xs text-(--color-muted)">{s.params}</div>
              <div className="mt-3 flex gap-2">
                <button
                  onClick={() => setModal({ id: s.id, name: s.name })}
                  className="rounded-lg bg-(--color-ink) px-3 py-1.5 text-xs font-medium text-(--color-elev)"
                >
                  Backtest
                </button>
                <Link href="/assets/NVDA" className="rounded-lg border border-(--color-edge) px-3 py-1.5 text-xs font-medium">
                  View asset
                </Link>
              </div>
            </Card>
          );
        })}
      </div>
      <p className="mt-4 text-xs text-(--color-muted)">
        Backtest opens an index prompt and POSTs to the backend (`POST /backtests`). Assets: {ASSETS.length} connected.
        {backendStrategies ? " ✓ Real-time data" : " ⚠ Using fallback data"}
      </p>

      {modal && (
        <BacktestModal
          strategyId={modal.id}
          strategyName={modal.name}
          onClose={() => setModal(null)}
        />
      )}
    </div>
  );
}

