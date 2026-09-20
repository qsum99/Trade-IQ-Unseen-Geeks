"use client";

import { Suspense, useEffect, useMemo, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import { apiData } from "@/api/client";
import { endpoints } from "@/api/endpoints";
import { ASSETS, runBacktest } from "@/lib/mock-data";
import { formatPercent, formatPrice } from "@/lib/format";
import { Badge, Card, EmptyState, Field, MetricCard, PageHeader, Skeleton, inputCls } from "@/components/ui";
import { Plot } from "@/components/charts/Plot";

const STEPS = ["Loading historical data", "Generating signals", "Running execution", "Calculating metrics", "Generating report"];
const STRATEGY_OPTIONS = ["sma_crossover", "ema_trend", "momentum", "mean_reversion"];

function BacktestingInner() {
  const sp = useSearchParams();
  const btId = sp.get("bt");
  const [symbol, setSymbol] = useState(sp.get("symbol") ?? "NVDA");
  const [strategy, setStrategy] = useState(
    STRATEGY_OPTIONS.includes(sp.get("strategy") ?? "") ? (sp.get("strategy") as string) : "sma_crossover",
  );
  const [fast, setFast] = useState(20);
  const [slow, setSlow] = useState(50);
  const [capital, setCapital] = useState(100000);
  const [cost, setCost] = useState(0.1);
  const [slip, setSlip] = useState(0.05);
  const [phase, setPhase] = useState<"idle" | "running" | "done">("idle");
  const [step, setStep] = useState(0);
  const [backendJobId, setBackendJobId] = useState<string | null>(btId);
  const [backendData, setBackendData] = useState<any>(null);
  const autoRan = useRef(false);

  const localResult = useMemo(
    () => runBacktest(symbol, fast, slow, capital, cost / 100, slip / 100),
    [symbol, fast, slow, capital, cost, slip],
  );

  const result = useMemo(() => {
    if (backendData) {
      const rawMetrics = backendData.metrics ?? {};
      const compare = backendData.compare ?? {};
      const rawTrades = Array.isArray(backendData.trades) ? backendData.trades : [];
      const rawEquity = Array.isArray(backendData.equity) ? backendData.equity : [];

      return {
        metrics: {
          totalReturn: rawMetrics.total_return ?? compare.strategy_return ?? localResult.metrics.totalReturn,
          sharpe: rawMetrics.sharpe ?? compare.strategy_sharpe ?? localResult.metrics.sharpe,
          volatility: rawMetrics.volatility ?? localResult.metrics.volatility,
          maxDD: rawMetrics.max_drawdown ?? compare.strategy_mdd ?? localResult.metrics.maxDD,
          benchReturn: compare.benchmark_return ?? localResult.metrics.benchReturn,
          benchSharpe: compare.benchmark_sharpe ?? localResult.metrics.benchSharpe,
          benchDD: compare.benchmark_mdd ?? localResult.metrics.benchDD,
          numTrades: rawTrades.length || rawMetrics.total_trades || localResult.metrics.numTrades,
          winRate: rawMetrics.win_rate ?? localResult.metrics.winRate,
          finalValue: capital * (1 + (rawMetrics.total_return ?? compare.strategy_return ?? 0)),
        },
        equity:
          rawEquity.length > 0
            ? rawEquity.map((e: any) => ({
                date: (e.date ?? "").split("T")[0],
                value: Number(e.portfolio_value ?? 0),
                benchmark: Number(e.benchmark_value ?? 0),
              }))
            : localResult.equity,
        trades:
          rawTrades.length > 0
            ? rawTrades.map((t: any, idx: number) => ({
                id: t.id ?? idx + 1,
                date: (t.date ?? t.timestamp ?? "").split("T")[0],
                side: (t.side ?? t.action ?? "BUY").toUpperCase() as "BUY" | "SELL",
                price: Math.round(Number(t.price ?? 0) * 100) / 100,
                quantity: Math.round(Number(t.quantity ?? t.size ?? 0) * 1000) / 1000,
                cost: Math.round(Number(t.transaction_cost ?? t.fee ?? t.cost ?? 0) * 100) / 100,
              }))
            : localResult.trades,
        signals: localResult.signals,
      };
    }
    return localResult;
  }, [backendData, localResult, capital]);

  const run = async () => {
    setPhase("running");
    setStep(0);
    let currentStep = 0;
    const timer = setInterval(() => {
      currentStep = Math.min(currentStep + 1, STEPS.length - 1);
      setStep(currentStep);
    }, 350);

    try {
      const res = await apiData<any>(endpoints.backtests(), {
        method: "POST",
        body: JSON.stringify({
          strategy_id: strategy,
          symbol,
          parameters: {
            fast_period: fast,
            slow_period: slow,
          },
          capital,
          cost_bps: Math.round(cost * 100),
          slippage_bps: Math.round(slip * 100),
          period: {
            start_date: "2024-09-01",
            end_date: "2026-09-20",
          },
        }),
      });

      if (res && res.backtest_id) {
        setBackendJobId(res.backtest_id);
        setBackendData(res);
      }
    } catch (e) {
      console.warn("Backend backtest failed, using local simulation fallback", e);
    } finally {
      clearInterval(timer);
      setStep(STEPS.length);
      setPhase("done");
    }
  };

  // Auto-run when launched from the Strategies page modal (?symbol=…&strategy=…)
  useEffect(() => {
    if (!autoRan.current && sp.get("symbol")) {
      autoRan.current = true;
      run();
    } else if (btId && !backendData) {
      apiData<any>(endpoints.backtest(btId))
        .then((res) => {
          if (res) {
            setBackendJobId(btId);
            setBackendData(res);
            setPhase("done");
          }
        })
        .catch(() => {});
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [btId]);

  const m = result.metrics;
  const meta = ASSETS.find((a) => a.symbol === symbol);

  return (
    <div>
      <PageHeader
        title="Backtesting"
        sub="Research workspace — signals at T execute at T+1 with costs and slippage"
        right={backendJobId ? <Badge tone="positive">Backend job {backendJobId}</Badge> : <Badge tone="warn">Mock engine</Badge>}
      />
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-[300px_1fr]">
        <Card>
          <div className="mb-3 text-sm font-semibold">Configuration</div>
          <div className="space-y-3">
            <Field label="Asset">
              <select value={symbol} onChange={(e) => setSymbol(e.target.value)} className={inputCls}>
                {ASSETS.map((a) => (
                  <option key={a.symbol} value={a.symbol}>{a.symbol} — {a.name}</option>
                ))}
              </select>
            </Field>
            <Field label="Strategy">
              <select value={strategy} onChange={(e) => setStrategy(e.target.value)} className={inputCls}>
                <option value="sma_crossover">SMA Crossover</option>
                <option value="ema_trend">EMA Trend</option>
                <option value="momentum">Momentum</option>
                <option value="mean_reversion">Mean Reversion</option>
              </select>
            </Field>
            <div className="grid grid-cols-2 gap-3">
              <Field label="Fast window">
                <input type="number" value={fast} onChange={(e) => setFast(Number(e.target.value))} className={inputCls} />
              </Field>
              <Field label="Slow window">
                <input type="number" value={slow} onChange={(e) => setSlow(Number(e.target.value))} className={inputCls} />
              </Field>
            </div>
            <Field label="Initial capital">
              <input type="number" value={capital} onChange={(e) => setCapital(Number(e.target.value))} className={inputCls} />
            </Field>
            <div className="grid grid-cols-2 gap-3">
              <Field label="Cost %">
                <input type="number" step="0.05" value={cost} onChange={(e) => setCost(Number(e.target.value))} className={inputCls} />
              </Field>
              <Field label="Slippage %">
                <input type="number" step="0.01" value={slip} onChange={(e) => setSlip(Number(e.target.value))} className={inputCls} />
              </Field>
            </div>
            <Field label="Execution">
              <select className={inputCls} defaultValue="next_open">
                <option value="next_open">Next bar</option>
                <option value="same_close">Same close (unrealistic)</option>
              </select>
            </Field>
            <button onClick={run} className="w-full rounded-lg bg-(--color-ink) py-2 text-sm font-semibold text-(--color-elev)">
              {phase === "running" ? "Running…" : "Run backtest"}
            </button>
          </div>
        </Card>

        <div>
          {phase === "idle" && (
            <EmptyState
              title="Configure your experiment"
              body="Pick an asset and strategy, set capital and costs, then run the backtest to see equity, benchmark comparison and trades."
              action={<button onClick={run} className="rounded-lg bg-(--color-ink) px-4 py-2 text-sm font-semibold text-(--color-elev)">Run your first backtest</button>}
            />
          )}
          {phase === "running" && (
            <Card>
              <div className="mb-2 text-sm font-semibold">Running backtest…</div>
              {STEPS.map((s, i) => (
                <div key={s} className="flex items-center gap-2 py-1 text-sm">
                  <span>{i < step ? "✓" : i === step ? "●" : "○"}</span>
                  <span className={i <= step ? "" : "text-(--color-muted)"}>{s}</span>
                </div>
              ))}
            </Card>
          )}
          {phase === "done" && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
                <MetricCard label="Return" value={formatPercent(m.totalReturn)} delta={m.totalReturn} />
                <MetricCard label="Sharpe" value={m.sharpe.toFixed(2)} delta={m.sharpe} />
                <MetricCard label="Volatility" value={formatPercent(m.volatility)} />
                <MetricCard label="Max Drawdown" value={formatPercent(m.maxDD)} delta={m.maxDD} />
              </div>
              <Card>
                <div className="mb-2 text-sm font-semibold">Equity Curve — {symbol} SMA {fast}/{slow}</div>
                <Plot
                  height={300}
                  data={[
                    { x: result.equity.map((e: any) => e.date), y: result.equity.map((e: any) => e.value), type: "scatter", mode: "lines", name: "Strategy", line: { color: "#2563eb" } },
                    { x: result.equity.map((e: any) => e.date), y: result.equity.map((e: any) => e.benchmark), type: "scatter", mode: "lines", name: "Buy & Hold", line: { color: "#98A2B3", dash: "dash" } },
                  ]}
                />
              </Card>
              <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
                <Card>
                  <div className="mb-2 text-sm font-semibold">Strategy vs Benchmark</div>
                  <table className="w-full text-sm">
                    <thead><tr className="text-left text-xs text-(--color-muted)"><th>Metric</th><th className="text-right">Strategy</th><th className="text-right">Buy & Hold</th></tr></thead>
                    <tbody className="tnum">
                      <tr className="border-t border-(--color-edge)"><td>Return</td><td className="text-right">{formatPercent(m.totalReturn)}</td><td className="text-right">{formatPercent(m.benchReturn)}</td></tr>
                      <tr className="border-t border-(--color-edge)"><td>Sharpe</td><td className="text-right">{m.sharpe.toFixed(2)}</td><td className="text-right">{m.benchSharpe.toFixed(2)}</td></tr>
                      <tr className="border-t border-(--color-edge)"><td>Max DD</td><td className="text-right">{formatPercent(m.maxDD)}</td><td className="text-right">{formatPercent(m.benchDD)}</td></tr>
                      <tr className="border-t border-(--color-edge)"><td>Trades</td><td className="text-right">{m.numTrades}</td><td className="text-right">1</td></tr>
                      <tr className="border-t border-(--color-edge)"><td>Win rate</td><td className="text-right">{formatPercent(m.winRate)}</td><td className="text-right">—</td></tr>
                    </tbody>
                  </table>
                </Card>
                <Card>
                  <div className="mb-2 text-sm font-semibold">Backtest Trust</div>
                  <ul className="space-y-1.5 text-sm">
                    <li>✓ No look-ahead <span className="text-(--color-muted)">(T+1 execution)</span></li>
                    <li>✓ Transaction costs applied ({cost.toFixed(2)}%)</li>
                    <li>✓ Slippage applied ({slip.toFixed(2)}%)</li>
                    <li>✓ Next-bar execution model</li>
                    <li><Badge tone="warn">⚠ Limited out-of-sample validation</Badge></li>
                  </ul>
                  <p className="mt-3 text-xs text-(--color-muted)">
                    Final value {formatPrice(m.finalValue, meta?.currency ?? "USD", 0)} on {formatPrice(capital, meta?.currency ?? "USD", 0)} initial.
                    Past performance does not predict future returns.
                  </p>
                </Card>
              </div>
              <Card>
                <div className="mb-2 text-sm font-semibold">Trades ({result.trades.length})</div>
                <div className="max-h-64 overflow-y-auto">
                  <table className="w-full text-sm">
                    <thead className="sticky top-0 bg-(--color-surface)">
                      <tr className="text-left text-xs text-(--color-muted)"><th>#</th><th>Date</th><th>Side</th><th className="text-right">Price</th><th className="text-right">Qty</th><th className="text-right">Cost</th></tr>
                    </thead>
                    <tbody className="tnum">
                      {result.trades.map((t: any) => (
                        <tr key={t.id} className="border-t border-(--color-edge)">
                          <td>{t.id}</td><td>{t.date}</td>
                          <td><Badge tone={t.side === "BUY" ? "positive" : "negative"}>{t.side}</Badge></td>
                          <td className="text-right">{t.price.toLocaleString()}</td>
                          <td className="text-right">{t.quantity.toLocaleString()}</td>
                          <td className="text-right">{t.cost.toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Card>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function BacktestingPage() {
  return (
    <Suspense fallback={<Skeleton className="h-96" />}>
      <BacktestingInner />
    </Suspense>
  );
}
