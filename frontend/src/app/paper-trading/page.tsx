"use client";

import { useState, useEffect, useCallback, useMemo, useRef } from "react";
import {
  Wallet,
  Percent,
  Award,
  TrendingDown,
  Activity,
  CheckCircle2,
  Receipt,
  Scale,
  AlertCircle,
  ShieldCheck,
  Zap,
} from "lucide-react";

import { PageHeader, Badge, Card } from "@/components/ui";
import { CandlestickChart, type CandlestickChartHandle, type TradeMarker } from "@/components/charts/CandlestickChart";
import { EquityChart } from "@/components/charts/EquityChart";
import { TradesBlotter } from "@/components/paper-trading/TradesBlotter";
import { TrustReportModal } from "@/components/paper-trading/TrustReportModal";
import { StrategyControls } from "@/components/paper-trading/StrategyControls";
import { KpiCard } from "@/components/paper-trading/KpiCard";

import type { Strategy, PaperTradeResult, TrustReport, PaperTradeRequest } from "@/types/paper-trading";

const FALLBACK_STRATEGIES: Strategy[] = [
  {
    id: "sma_crossover",
    name: "SMA Crossover",
    description: "Generates signals using fast and slow Simple Moving Averages",
    parameters: [
      { name: "fast_period", type: "integer", default: 20, description: "Fast SMA period (bars)" },
      { name: "slow_period", type: "integer", default: 50, description: "Slow SMA period (bars)" },
    ],
  },
  {
    id: "ema_trend",
    name: "EMA Trend",
    description: "EMA20 > EMA50 -> Trend following momentum",
    parameters: [
      { name: "fast_period", type: "integer", default: 20, description: "Fast EMA period" },
      { name: "slow_period", type: "integer", default: 50, description: "Slow EMA period" },
    ],
  },
  {
    id: "momentum",
    name: "Momentum",
    description: "20d return exceeding threshold -> BUY",
    parameters: [
      { name: "lookback", type: "integer", default: 20, description: "Lookback window" },
      { name: "threshold", type: "number", default: 0.02, description: "Threshold return fraction" },
    ],
  },
  {
    id: "mean_reversion",
    name: "Mean Reversion",
    description: "Statistical Z-score reversal around rolling mean",
    parameters: [
      { name: "lookback", type: "integer", default: 20, description: "Z-score window" },
      { name: "entry_z", type: "number", default: 2.0, description: "Entry threshold (+/- Z)" },
    ],
  },
  {
    id: "regime_adaptive",
    name: "Regime Adaptive",
    description: "Dynamic Bull/Bear/Volatility regime-mapped allocation",
    parameters: [
      { name: "regime_model", type: "string", default: "rule_based", description: "Regime detector model" },
    ],
  },
];

const PERIODS = ["5d", "1mo", "3mo", "6mo", "1y", "2y"] as const;
type Period = typeof PERIODS[number];

const INTERVALS = ["15m", "1h", "1d", "1wk"] as const;
type Interval = typeof INTERVALS[number];

const PRESETS = [
  { label: "BTC-USD", desc: "24/7 Crypto", value: "BTC-USD" },
  { label: "ETH-USD", desc: "24/7 Crypto", value: "ETH-USD" },
  { label: "SOL-USD", desc: "24/7 Crypto", value: "SOL-USD" },
  { label: "RELIANCE.NS", desc: "NSE India", value: "RELIANCE.NS" },
  { label: "NVDA", desc: "US Tech", value: "NVDA" },
];

export default function PaperTradingPage() {
  const [strategies, setStrategies] = useState<Strategy[]>(FALLBACK_STRATEGIES);

  const [symbol, setSymbol] = useState<string>("BTC-USD");
  const [selectedStrategyId, setSelectedStrategyId] = useState<string>("sma_crossover");
  const [strategyParams, setStrategyParams] = useState<Record<string, unknown>>({
    fast_period: 20,
    slow_period: 50,
  });
  const [initialCapital, setInitialCapital] = useState<number>(100000);
  const [slippage, setSlippage] = useState<number>(0.0005);
  const [executionPrice, setExecutionPrice] = useState<"next_open" | "next_close">("next_open");

  const [chartPeriod, setChartPeriod] = useState<Period>("1mo");
  const [chartInterval, setChartInterval] = useState<Interval>("1h");
  const [liveStream, setLiveStream] = useState<boolean>(true);

  const [result, setResult] = useState<PaperTradeResult | null>(null);
  const [trustReport, setTrustReport] = useState<TrustReport | null>(null);
  const [isTrustReportOpen, setIsTrustReportOpen] = useState<boolean>(false);
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [notification, setNotification] = useState<string | null>(null);

  const candleChartRef = useRef<CandlestickChartHandle>(null);

  useEffect(() => {
    let mounted = true;
    async function loadStrategies() {
      try {
        const res = await fetch("/api/v1/strategies");
        if (res.ok) {
          const envelope = await res.json();
          if (mounted && envelope.success && Array.isArray(envelope.data) && envelope.data.length > 0) {
            setStrategies(envelope.data);
          }
        }
      } catch {
        // Keep fallback
      }
    }
    loadStrategies();
    return () => {
      mounted = false;
    };
  }, []);

  const handleExecute = useCallback(async () => {
    setIsLoading(true);
    setErrorMsg(null);
    setNotification(null);
    try {
      const payload: PaperTradeRequest = {
        symbol,
        strategy: selectedStrategyId,
        parameters: strategyParams,
        initial_capital: initialCapital,
        slippage,
        execution_price: executionPrice,
        interval: chartInterval,
      };

      const res = await fetch("/api/v1/paper-trade", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!res.ok) {
        const errJson = await res.json().catch(() => null);
        throw new Error(errJson?.error?.message || errJson?.detail || `HTTP Error ${res.status}`);
      }

      const envelope = await res.json();
      if (!envelope.success || !envelope.data) {
        throw new Error(envelope.error?.message || "Paper trade execution error");
      }

      const tradeResult = envelope.data as PaperTradeResult;
      setResult(tradeResult);

      if (tradeResult.backtest_id) {
        try {
          const trRes = await fetch(`/api/v1/backtests/${encodeURIComponent(tradeResult.backtest_id)}/trust-report`);
          if (trRes.ok) {
            const trEnv = await trRes.json();
            if (trEnv.success && trEnv.data) {
              setTrustReport(trEnv.data as TrustReport);
            }
          }
        } catch {
          // Non-critical
        }
      }

      setNotification(
        `Executed on ${tradeResult.symbol} (${chartInterval}) — ${tradeResult.trades.length} fills, Total Return: ${(tradeResult.total_return * 100).toFixed(2)}%`,
      );
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : "Paper trade execution failed.");
    } finally {
      setIsLoading(false);
    }
  }, [symbol, selectedStrategyId, strategyParams, initialCapital, slippage, executionPrice, chartInterval]);

  useEffect(() => {
    handleExecute();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const handleSimulateTick = () => {
    if (!result) return;
    const last = result.equity_curve[result.equity_curve.length - 1];
    const prevVal = last ? last.portfolio_value : initialCapital;
    const delta = (Math.random() - 0.47) * 0.018;
    const newVal = Math.round(prevVal * (1 + delta) * 100) / 100;
    const today = new Date().toISOString().slice(0, 10);

    const updatedTrades = [...result.trades];
    if (Math.random() > 0.6) {
      const side = Math.random() > 0.5 ? "BUY" : "SELL";
      const simPrice = Math.round((1200 + Math.random() * 80) * 100) / 100;
      updatedTrades.push({
        id: updatedTrades.length + 1,
        date: today,
        side,
        price: simPrice,
        quantity: 25,
        transaction_cost: Math.round(simPrice * 25 * slippage * 100) / 100,
        order_type: "MARKET (T+1)",
      });
    }

    const newCurve = [...result.equity_curve, { date: today, portfolio_value: newVal }];
    setResult({
      ...result,
      final_value: newVal,
      total_return: (newVal - initialCapital) / initialCapital,
      equity_curve: newCurve,
      equity: newCurve.map((p) => p.portfolio_value),
      trades: updatedTrades,
      total_trades: updatedTrades.length,
    });
    setNotification(`Simulated live bar: $${newVal.toLocaleString()} (${delta >= 0 ? "+" : ""}${(delta * 100).toFixed(2)}%)`);
  };

  const handleReset = () => {
    setResult(null);
    setTrustReport(null);
    setNotification(null);
    setErrorMsg(null);
  };

  const tradeMarkers: TradeMarker[] = useMemo(() => {
    return (result?.trades ?? []).map((t) => ({
      date: t.date,
      side: t.side as "BUY" | "SELL",
      price: t.price,
    }));
  }, [result?.trades]);

  const isUSD =
    symbol.includes("USD") ||
    symbol.includes("USDT") ||
    (!symbol.includes(".NS") && !symbol.includes(".BO"));
  const currSym = isUSD ? "$" : "₹";
  const totalReturnPct = result ? (result.total_return * 100).toFixed(2) : "0.00";
  const sharpeStr = result ? result.sharpe.toFixed(2) : "0.00";
  const volPct = result ? (result.volatility * 100).toFixed(2) : "0.00";
  const maxDdPct = result ? (Math.abs(result.max_drawdown) * 100).toFixed(2) : "0.00";
  const winRatePct = result ? (result.win_rate * 100).toFixed(1) : "0.0";
  const pfStr = result ? result.profit_factor.toFixed(2) : "0.00";
  const avgTradeStr = result ? `${currSym}${result.average_trade.toFixed(2)}` : `${currSym}0.00`;

  return (
    <div className="space-y-6">
      {/* Top Header Bar */}
      <PageHeader
        title="Paper Trading & Execution Engine"
        sub="Simulate quantitative strategies against real-time 24/7 crypto and equity feeds with zero financial risk and deterministic T+1 fill semantics."
        right={
          <div className="flex flex-wrap items-center gap-2">
            {PRESETS.map((p) => (
              <button
                key={p.value}
                onClick={() => setSymbol(p.value)}
                className={`px-3 py-1.5 rounded-lg text-xs font-mono transition border cursor-pointer ${
                  symbol === p.value
                    ? "bg-cyan-500/15 text-cyan-600 dark:text-cyan-300 border-cyan-500/60 font-bold shadow-xs"
                    : "bg-(--color-surface) text-(--color-muted) border-(--color-edge) hover:text-(--color-ink) hover:bg-(--color-elev)"
                }`}
              >
                {p.label}
              </button>
            ))}

            {trustReport && (
              <button
                onClick={() => setIsTrustReportOpen(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-500/15 text-indigo-600 dark:text-indigo-300 border border-indigo-500/30 text-xs font-semibold hover:bg-indigo-500/25 transition cursor-pointer ml-1 shadow-xs"
              >
                <ShieldCheck className="h-3.5 w-3.5" />
                <span>Trust Audit</span>
              </button>
            )}
          </div>
        }
      />


      {/* Notifications & Error Alerts */}
      {errorMsg && (
        <div className="p-3.5 rounded-xl bg-rose-500/10 border border-rose-500/30 text-rose-600 dark:text-rose-300 text-xs flex items-center gap-2 shadow-xs">
          <AlertCircle className="h-4 w-4 text-rose-500 dark:text-rose-400 shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}
      {notification && !errorMsg && (
        <div className="p-3 rounded-xl bg-cyan-500/10 border border-cyan-500/30 text-cyan-700 dark:text-cyan-300 text-xs flex items-center justify-between shadow-xs">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-cyan-600 dark:text-cyan-400 shrink-0" />
            <span>{notification}</span>
          </div>
          <button
            onClick={() => setNotification(null)}
            className="text-cyan-600 dark:text-cyan-400/60 hover:text-cyan-800 dark:hover:text-cyan-200 font-mono text-xs cursor-pointer"
          >
            dismiss
          </button>
        </div>
      )}

      {/* Strategy Execution Controls */}
      <StrategyControls
        symbol={symbol}
        setSymbol={setSymbol}
        strategies={strategies}
        selectedStrategyId={selectedStrategyId}
        setSelectedStrategyId={setSelectedStrategyId}
        strategyParams={strategyParams}
        setStrategyParams={setStrategyParams}
        initialCapital={initialCapital}
        setInitialCapital={setInitialCapital}
        slippage={slippage}
        setSlippage={setSlippage}
        executionPrice={executionPrice}
        setExecutionPrice={setExecutionPrice}
        onExecute={handleExecute}
        onSimulateTick={handleSimulateTick}
        onReset={handleReset}
        isLoading={isLoading}
      />

      {/* Real-Time Candlestick Chart Section */}
      <div className="space-y-3">
        <div className="flex flex-wrap items-center justify-between gap-3 px-1">
          <div className="flex items-center gap-2">
            <Zap className="h-4 w-4 text-cyan-600 dark:text-cyan-400" />
            <h3 className="text-sm font-semibold tracking-wider text-(--color-ink) uppercase m-0">
              Live Candlestick Feed & Signal Markers
            </h3>
          </div>

          <div className="flex flex-wrap items-center gap-2">
            {/* Interval buttons */}
            <div className="flex items-center bg-(--color-surface) border border-(--color-edge) rounded-lg p-0.5 shadow-xs">
              {INTERVALS.map((iv) => (
                <button
                  key={iv}
                  onClick={() => setChartInterval(iv)}
                  className={`px-2 py-0.5 rounded text-[11px] font-mono transition cursor-pointer ${
                    chartInterval === iv
                      ? "bg-cyan-500/20 text-cyan-600 dark:text-cyan-300 font-bold"
                      : "text-(--color-muted) hover:text-(--color-ink)"
                  }`}
                >
                  {iv}
                </button>
              ))}
            </div>

            {/* Period buttons */}
            <div className="flex items-center bg-(--color-surface) border border-(--color-edge) rounded-lg p-0.5 shadow-xs">
              {PERIODS.map((p) => (
                <button
                  key={p}
                  onClick={() => setChartPeriod(p)}
                  className={`px-2 py-0.5 rounded text-[11px] font-mono transition cursor-pointer ${
                    chartPeriod === p
                      ? "bg-cyan-500/20 text-cyan-600 dark:text-cyan-300 font-bold"
                      : "text-(--color-muted) hover:text-(--color-ink)"
                  }`}
                >
                  {p}
                </button>
              ))}
            </div>

            {/* Live streaming toggle */}
            <button
              onClick={() => setLiveStream((v) => !v)}
              className={`px-2.5 py-1 rounded-lg text-xs font-mono transition border cursor-pointer ${
                liveStream
                  ? "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border-emerald-500/30 font-semibold"
                  : "bg-(--color-surface) text-(--color-muted) border-(--color-edge) hover:bg-(--color-elev)"
              }`}
            >
              {liveStream ? "● Live Auto-Poll" : "○ Stream Paused"}
            </button>
          </div>
        </div>

        <CandlestickChart
          ref={candleChartRef}
          symbol={symbol}
          period={chartPeriod}
          interval={chartInterval}
          liveStream={liveStream}
          tradeMarkers={tradeMarkers}
        />
      </div>

      {/* KPI Performance Summary Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
        <KpiCard
          title="Total Return"
          value={`${Number(totalReturnPct) >= 0 ? "+" : ""}${totalReturnPct}%`}
          subtitle="Net Strategy PnL"
          icon={Percent}
          trend={Number(totalReturnPct) >= 0 ? "up" : "down"}
          tone={Number(totalReturnPct) >= 0 ? "emerald" : "rose"}
        />
        <KpiCard
          title="Ending Equity"
          value={
            result
              ? `${currSym}${result.final_value.toLocaleString("en-US", {
                  maximumFractionDigits: 0,
                })}`
              : `${currSym}${initialCapital.toLocaleString("en-US")}`
          }
          subtitle={`Ledger Capital: ${currSym}${initialCapital.toLocaleString("en-US")}`}
          icon={Wallet}
          tone="cyan"
        />
        <KpiCard
          title="Sharpe Ratio"
          value={sharpeStr}
          subtitle={`Vol: ${volPct}%`}
          icon={Award}
          tone={Number(sharpeStr) > 1.0 ? "emerald" : "blue"}
        />
        <KpiCard
          title="Max Drawdown"
          value={`-${maxDdPct}%`}
          subtitle="Peak-to-trough"
          icon={TrendingDown}
          tone="rose"
        />
        <KpiCard
          title="Win Rate"
          value={`${winRatePct}%`}
          subtitle={`Profit Factor: ${pfStr}`}
          icon={Scale}
          tone={Number(winRatePct) >= 50 ? "emerald" : "amber"}
        />
        <KpiCard
          title="Total Trades"
          value={result ? result.total_trades : 0}
          subtitle={`Avg Trade: ${avgTradeStr}`}
          icon={Receipt}
          tone="slate"
        />
      </div>

      {/* Equity Curve & Benchmark Comparison */}
      <EquityChart
        equityCurve={result?.equity_curve || []}
        benchmarkCurve={result?.benchmark?.curve}
        initialCapital={initialCapital}
        symbol={symbol}
        currencySymbol={currSym}
      />

      {/* Institutional Trades Blotter */}
      <TradesBlotter trades={result?.trades || []} currencySymbol={currSym} />

      {/* Trust & Audit Modal */}
      <TrustReportModal
        isOpen={isTrustReportOpen}
        onClose={() => setIsTrustReportOpen(false)}
        report={trustReport}
      />
    </div>
  );
}
