"use client";

import React, { useState, useMemo } from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  ReferenceLine,
} from "recharts";
import { TrendingDown } from "lucide-react";
import { useTheme } from "@/components/providers";
import type { EquityPoint, BenchmarkPoint } from "@/types/paper-trading";

interface EquityChartProps {
  equityCurve: EquityPoint[];
  benchmarkCurve?: BenchmarkPoint[];
  initialCapital: number;
  symbol: string;
  currencySymbol?: string;
}

type ViewMode = "comparison" | "drawdown" | "combined";

interface CustomTooltipProps {
  active?: boolean;
  payload?: Array<{
    name: string;
    value: number;
    color: string;
    dataKey?: string;
  }>;
  label?: string;
  initialCapital: number;
  currencySymbol?: string;
}

const CustomTooltip: React.FC<CustomTooltipProps> = ({
  active,
  payload,
  label,
  initialCapital,
  currencySymbol = "$",
}) => {
  if (active && payload && payload.length) {
    const stratItem = payload.find((p) => p.dataKey === "strategy");
    const benchItem = payload.find((p) => p.dataKey === "benchmark");
    const ddItem = payload.find((p) => p.dataKey === "drawdown");

    const stratVal = stratItem?.value;
    const benchVal = benchItem?.value;
    const ddVal = ddItem?.value;

    const stratReturn = stratVal ? ((stratVal - initialCapital) / (initialCapital || 1)) * 100 : 0;
    const benchReturn = benchVal ? ((benchVal - initialCapital) / (initialCapital || 1)) * 100 : 0;
    const excess = stratReturn - benchReturn;

    return (
      <div className="bg-white/95 dark:bg-slate-950/95 border border-slate-200 dark:border-slate-800 p-3 rounded-lg shadow-xl dark:shadow-2xl backdrop-blur-md font-mono text-xs space-y-1">
        <div className="text-slate-600 dark:text-slate-400 font-semibold pb-1 border-b border-slate-200 dark:border-slate-800 flex justify-between">
          <span>{label}</span>
          {benchVal !== undefined && (
            <span className={excess >= 0 ? "text-emerald-600 dark:text-emerald-400 font-bold" : "text-rose-600 dark:text-rose-400 font-bold"}>
              Alpha: {excess >= 0 ? "+" : ""}
              {excess.toFixed(2)}%
            </span>
          )}
        </div>

        {stratVal !== undefined && (
          <div className="flex items-center justify-between gap-4 py-0.5">
            <span className="text-cyan-600 dark:text-cyan-400 flex items-center gap-1.5 font-medium">
              <span className="h-2 w-2 rounded-full bg-cyan-500 dark:bg-cyan-400" />
              Strategy:
            </span>
            <span className="font-bold text-slate-900 dark:text-white">
              {currencySymbol}
              {stratVal.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              <span className={`ml-1.5 ${stratReturn >= 0 ? "text-emerald-600 dark:text-emerald-400" : "text-rose-600 dark:text-rose-400"}`}>
                ({stratReturn >= 0 ? "+" : ""}
                {stratReturn.toFixed(2)}%)
              </span>
            </span>
          </div>
        )}

        {benchVal !== undefined && (
          <div className="flex items-center justify-between gap-4 py-0.5">
            <span className="text-amber-600 dark:text-amber-400/80 flex items-center gap-1.5 font-medium">
              <span className="h-2 w-2 rounded-full bg-amber-500 dark:bg-amber-400" />
              Benchmark:
            </span>
            <span className="font-medium text-slate-700 dark:text-slate-300">
              {currencySymbol}
              {benchVal.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              <span className={`ml-1.5 ${benchReturn >= 0 ? "text-emerald-600 dark:text-emerald-400" : "text-rose-600 dark:text-rose-400"}`}>
                ({benchReturn >= 0 ? "+" : ""}
                {benchReturn.toFixed(2)}%)
              </span>
            </span>
          </div>
        )}

        {ddVal !== undefined && (
          <div className="flex items-center justify-between gap-4 py-0.5 text-rose-600 dark:text-rose-400 font-medium">
            <span className="flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-rose-500" />
              Drawdown:
            </span>
            <span className="font-bold">{ddVal.toFixed(2)}%</span>
          </div>
        )}
      </div>
    );
  }
  return null;
};

export const EquityChart: React.FC<EquityChartProps> = ({
  equityCurve,
  benchmarkCurve,
  initialCapital,
  symbol,
  currencySymbol = "$",
}) => {
  const { theme } = useTheme();
  const isDark = theme === "dark";
  const [viewMode, setViewMode] = useState<ViewMode>("combined");

  const { combinedData, stats, yDomain, minDrawdown } = useMemo(() => {
    if (!equityCurve || equityCurve.length === 0) {
      return { combinedData: [], stats: null, yDomain: [0, 0], minDrawdown: 0 };
    }

    let peak = initialCapital;
    let maxDd = 0;

    const data = equityCurve.map((ep, idx) => {
      const val = ep.portfolio_value;
      if (val > peak) peak = val;
      const dd = peak > 0 ? ((val - peak) / peak) * 100 : 0;
      if (dd < maxDd) maxDd = dd;

      const bp = benchmarkCurve ? benchmarkCurve[idx] : undefined;
      return {
        date: ep.date,
        strategy: val,
        benchmark: bp ? bp.portfolio_value : undefined,
        drawdown: parseFloat(dd.toFixed(2)),
        highWaterMark: peak,
      };
    });

    const finalStrat = equityCurve[equityCurve.length - 1]?.portfolio_value ?? initialCapital;
    const stratReturn = ((finalStrat - initialCapital) / (initialCapital || 1)) * 100;

    const finalBench =
      benchmarkCurve && benchmarkCurve.length > 0
        ? benchmarkCurve[benchmarkCurve.length - 1]?.portfolio_value ?? initialCapital
        : undefined;
    const benchReturn =
      finalBench !== undefined ? ((finalBench - initialCapital) / (initialCapital || 1)) * 100 : undefined;
    const alpha = benchReturn !== undefined ? stratReturn - benchReturn : undefined;

    const minVal = Math.min(...equityCurve.map((d) => d.portfolio_value));
    const maxVal = Math.max(...equityCurve.map((d) => d.portfolio_value), peak);
    const domain = [Math.floor(minVal * 0.96), Math.ceil(maxVal * 1.04)];

    return {
      combinedData: data,
      stats: {
        finalStrat,
        stratReturn,
        finalBench,
        benchReturn,
        alpha,
        maxDrawdown: maxDd,
        highWaterMark: peak,
      },
      yDomain: domain,
      minDrawdown: Math.min(maxDd * 1.1, -5),
    };
  }, [equityCurve, benchmarkCurve, initialCapital]);

  if (!equityCurve || equityCurve.length === 0) {
    return (
      <div className="h-72 w-full bg-slate-50 dark:bg-slate-900/60 border border-slate-200 dark:border-slate-800 rounded-xl flex items-center justify-center text-slate-500 font-mono text-xs">
        No equity curve data. Run paper trading to generate performance history.
      </div>
    );
  }

  const gridColor = isDark ? "#1e293b" : "#f1f5f9";
  const axisColor = isDark ? "#334155" : "#cbd5e1";
  const tickColor = isDark ? "#64748b" : "#64748b";

  return (
    <div className="bg-white dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm dark:shadow-xl flex flex-col space-y-4">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 pb-3 border-b border-slate-200 dark:border-slate-800">
        <div>
          <div className="flex items-center space-x-2">
            <h3 className="text-sm font-bold tracking-wider text-slate-900 dark:text-white uppercase m-0">
              Equity Trajectory & Benchmark Comparison ({symbol})
            </h3>
            {stats?.alpha !== undefined && (
              <span
                className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold ${
                  stats.alpha >= 0
                    ? "bg-emerald-50 dark:bg-emerald-500/20 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/40"
                    : "bg-rose-50 dark:bg-rose-500/20 text-rose-700 dark:text-rose-400 border border-rose-200 dark:border-rose-500/40"
                }`}
              >
                Alpha: {stats.alpha >= 0 ? "+" : ""}
                {stats.alpha.toFixed(2)}%
              </span>
            )}
          </div>
          <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
            Mark-to-market portfolio value vs Buy & Hold baseline with underwater drawdown analysis
          </p>
        </div>

        <div className="flex items-center space-x-1.5 bg-slate-100 dark:bg-slate-950 p-1 rounded-lg border border-slate-200 dark:border-slate-800 text-xs font-mono">
          <button
            onClick={() => setViewMode("combined")}
            className={`px-2.5 py-1 rounded transition cursor-pointer ${
              viewMode === "combined"
                ? "bg-cyan-50 dark:bg-cyan-500/20 text-cyan-700 dark:text-cyan-300 border border-cyan-200 dark:border-cyan-500/50 font-semibold"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
            }`}
          >
            Combined View
          </button>
          <button
            onClick={() => setViewMode("comparison")}
            className={`px-2.5 py-1 rounded transition cursor-pointer ${
              viewMode === "comparison"
                ? "bg-cyan-50 dark:bg-cyan-500/20 text-cyan-700 dark:text-cyan-300 border border-cyan-200 dark:border-cyan-500/50 font-semibold"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
            }`}
          >
            Equity Only
          </button>
          <button
            onClick={() => setViewMode("drawdown")}
            className={`px-2.5 py-1 rounded transition cursor-pointer ${
              viewMode === "drawdown"
                ? "bg-rose-50 dark:bg-rose-500/20 text-rose-700 dark:text-rose-400 border border-rose-200 dark:border-rose-500/50 font-semibold"
                : "text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-white"
            }`}
          >
            Drawdown (%)
          </button>
        </div>
      </div>

      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2.5 p-3 rounded-lg bg-slate-50 dark:bg-slate-950/70 border border-slate-200 dark:border-slate-800/80 font-mono text-xs">
          <div>
            <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Ending Equity</span>
            <span className="text-sm font-bold text-slate-900 dark:text-white">
              {currencySymbol}
              {stats.finalStrat.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
            </span>
          </div>

          <div>
            <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Strategy Return</span>
            <span
              className={`text-sm font-bold ${
                stats.stratReturn >= 0 ? "text-emerald-600 dark:text-emerald-400" : "text-rose-600 dark:text-rose-400"
              }`}
            >
              {stats.stratReturn >= 0 ? "+" : ""}
              {stats.stratReturn.toFixed(2)}%
            </span>
          </div>

          <div>
            <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Buy & Hold Return</span>
            <span
              className={`text-sm font-bold ${
                (stats.benchReturn ?? 0) >= 0 ? "text-amber-600 dark:text-amber-400" : "text-slate-600 dark:text-slate-300"
              }`}
            >
              {stats.benchReturn !== undefined
                ? `${stats.benchReturn >= 0 ? "+" : ""}${stats.benchReturn.toFixed(2)}%`
                : "--"}
            </span>
          </div>

          <div>
            <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Net Alpha</span>
            <span
              className={`text-sm font-bold ${
                (stats.alpha ?? 0) >= 0 ? "text-emerald-600 dark:text-emerald-400" : "text-rose-600 dark:text-rose-400"
              }`}
            >
              {stats.alpha !== undefined
                ? `${stats.alpha >= 0 ? "+" : ""}${stats.alpha.toFixed(2)}%`
                : "--"}
            </span>
          </div>

          <div>
            <span className="text-[10px] text-slate-500 uppercase tracking-wider block">Max Drawdown</span>
            <span className="text-sm font-bold text-rose-600 dark:text-rose-400">
              {stats.maxDrawdown.toFixed(2)}%
            </span>
          </div>

          <div>
            <span className="text-[10px] text-slate-500 uppercase tracking-wider block">High-Water Mark</span>
            <span className="text-sm font-bold text-cyan-700 dark:text-cyan-300">
              {currencySymbol}
              {stats.highWaterMark.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
            </span>
          </div>
        </div>
      )}

      {(viewMode === "comparison" || viewMode === "combined") && (
        <div className={viewMode === "combined" ? "h-64 w-full" : "h-80 w-full"}>
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={combinedData} margin={{ top: 10, right: 10, left: 10, bottom: 0 }}>
              <defs>
                <linearGradient id="stratGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.4} />
                  <stop offset="95%" stopColor="#06b6d4" stopOpacity={0.0} />
                </linearGradient>
                <linearGradient id="benchGradient" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="5%" stopColor="#f59e0b" stopOpacity={0.2} />
                  <stop offset="95%" stopColor="#f59e0b" stopOpacity={0.0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke={gridColor} vertical={false} />
              <XAxis
                dataKey="date"
                stroke={axisColor}
                tick={{ fontSize: 11, fill: tickColor }}
                tickLine={false}
                axisLine={{ stroke: axisColor }}
                interval="preserveStartEnd"
                minTickGap={40}
              />
              <YAxis
                domain={yDomain}
                stroke={axisColor}
                tick={{ fontSize: 11, fill: tickColor }}
                tickLine={false}
                axisLine={{ stroke: axisColor }}
                tickFormatter={(v) => `${currencySymbol}${(v / 1000).toFixed(0)}k`}
                orientation="right"
              />
              <Tooltip
                content={<CustomTooltip initialCapital={initialCapital} currencySymbol={currencySymbol} />}
              />
              <ReferenceLine
                y={stats?.highWaterMark}
                stroke="#06b6d4"
                strokeDasharray="2 4"
                strokeOpacity={0.5}
              />
              {benchmarkCurve && benchmarkCurve.length > 0 && (
                <Area
                  type="monotone"
                  dataKey="benchmark"
                  stroke="#f59e0b"
                  strokeDasharray="4 4"
                  strokeWidth={1.5}
                  fill="url(#benchGradient)"
                  isAnimationActive={false}
                />
              )}
              <Area
                type="monotone"
                dataKey="strategy"
                stroke="#06b6d4"
                strokeWidth={2.5}
                fill="url(#stratGradient)"
                isAnimationActive={false}
              />
            </AreaChart>
          </ResponsiveContainer>
        </div>
      )}

      {(viewMode === "drawdown" || viewMode === "combined") && (
        <div className="pt-2 border-t border-slate-200 dark:border-slate-800/80">
          <div className="flex items-center justify-between mb-2">
            <span className="text-[11px] font-mono text-slate-600 dark:text-slate-400 flex items-center gap-1.5">
              <TrendingDown className="h-3.5 w-3.5 text-rose-500 dark:text-rose-400" />
              <span>Underwater Drawdown Profile (Peak-to-Trough %)</span>
            </span>
            <span className="text-[10px] font-mono text-rose-600 dark:text-rose-400 font-bold">
              Max: {stats?.maxDrawdown.toFixed(2)}%
            </span>
          </div>
          <div className={viewMode === "combined" ? "h-32 w-full" : "h-72 w-full"}>
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={combinedData} margin={{ top: 5, right: 10, left: 10, bottom: 0 }}>
                <defs>
                  <linearGradient id="drawdownGradient" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.0} />
                    <stop offset="95%" stopColor="#f43f5e" stopOpacity={0.35} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke={gridColor} vertical={false} />
                <XAxis
                  dataKey="date"
                  stroke={axisColor}
                  tick={{ fontSize: 10, fill: tickColor }}
                  tickLine={false}
                  axisLine={{ stroke: axisColor }}
                  interval="preserveStartEnd"
                  minTickGap={40}
                />
                <YAxis
                  domain={[minDrawdown, 0]}
                  stroke={axisColor}
                  tick={{ fontSize: 10, fill: tickColor }}
                  tickLine={false}
                  axisLine={{ stroke: axisColor }}
                  tickFormatter={(v) => `${v.toFixed(0)}%`}
                  orientation="right"
                />
                <Tooltip
                  content={<CustomTooltip initialCapital={initialCapital} currencySymbol={currencySymbol} />}
                />
                <Area
                  type="monotone"
                  dataKey="drawdown"
                  stroke="#f43f5e"
                  strokeWidth={1.5}
                  fill="url(#drawdownGradient)"
                  isAnimationActive={false}
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  );
};

