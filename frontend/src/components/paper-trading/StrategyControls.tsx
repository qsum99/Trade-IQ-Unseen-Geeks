"use client";

import React from "react";
import { Play, RotateCcw, Sliders, DollarSign, ArrowRightLeft, Radio } from "lucide-react";
import type { Strategy } from "@/types/paper-trading";

interface StrategyControlsProps {
  symbol: string;
  setSymbol: (s: string) => void;
  strategies: Strategy[];
  selectedStrategyId: string;
  setSelectedStrategyId: (s: string) => void;
  strategyParams: Record<string, unknown>;
  setStrategyParams: (p: Record<string, unknown>) => void;
  initialCapital: number;
  setInitialCapital: (c: number) => void;
  slippage: number;
  setSlippage: (s: number) => void;
  executionPrice: "next_open" | "next_close";
  setExecutionPrice: (p: "next_open" | "next_close") => void;
  onExecute: () => void;
  onSimulateTick: () => void;
  onReset: () => void;
  isLoading: boolean;
}

export const StrategyControls: React.FC<StrategyControlsProps> = ({
  symbol,
  setSymbol,
  strategies,
  selectedStrategyId,
  setSelectedStrategyId,
  strategyParams,
  setStrategyParams,
  initialCapital,
  setInitialCapital,
  slippage,
  setSlippage,
  executionPrice,
  setExecutionPrice,
  onExecute,
  onSimulateTick,
  onReset,
  isLoading,
}) => {
  const currentStrategy = strategies.find((s) => s.id === selectedStrategyId) || strategies[0];

  const handleParamChange = (name: string, value: string | number) => {
    setStrategyParams({
      ...strategyParams,
      [name]: value,
    });
  };

  return (
    <div className="bg-white dark:bg-slate-900/80 border border-slate-200 dark:border-slate-800 rounded-xl p-5 shadow-sm dark:shadow-xl flex flex-col gap-4">
      <div className="flex items-center justify-between pb-3 border-b border-slate-200 dark:border-slate-800">
        <div className="flex items-center space-x-2">
          <Sliders className="h-4 w-4 text-cyan-600 dark:text-cyan-400" />
          <h2 className="text-sm font-semibold tracking-wider text-slate-900 dark:text-slate-200 uppercase m-0">
            Execution Parameters
          </h2>
        </div>
        <span className="text-xs font-mono text-cyan-700 dark:text-cyan-400/80 bg-cyan-50 dark:bg-cyan-950/60 px-2 py-0.5 rounded border border-cyan-200 dark:border-cyan-800/40 font-medium">
          T+1 Safe · Deterministic
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Symbol Input */}
        <div>
          <label className="block text-xs font-medium text-slate-700 dark:text-slate-400 mb-1">
            Asset Symbol (Crypto / Yahoo / NSE)
          </label>
          <div className="relative">
            <input
              type="text"
              value={symbol}
              onChange={(e) => setSymbol(e.target.value.toUpperCase())}
              placeholder="e.g. BTC-USD, RELIANCE.NS, NVDA"
              className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-900 dark:text-white font-mono focus:outline-none focus:border-cyan-500 transition shadow-inner"
            />
          </div>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
            Crypto 24/7 (BTC-USD, ETH-USD) or Equities
          </p>
        </div>

        {/* Strategy Selector */}
        <div>
          <label className="block text-xs font-medium text-slate-700 dark:text-slate-400 mb-1">
            Strategy Model
          </label>
          <select
            value={selectedStrategyId}
            onChange={(e) => {
              const newId = e.target.value;
              setSelectedStrategyId(newId);
              const found = strategies.find((s) => s.id === newId);
              if (found && found.parameters) {
                const defaults: Record<string, unknown> = {};
                found.parameters.forEach((p) => {
                  defaults[p.name] = p.default;
                });
                setStrategyParams(defaults);
              }
            }}
            className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-lg px-3 py-2 text-sm text-slate-900 dark:text-white focus:outline-none focus:border-cyan-500 transition cursor-pointer shadow-xs"
          >
            {strategies.map((strat) => (
              <option key={strat.id} value={strat.id} className="bg-white dark:bg-slate-900 text-slate-900 dark:text-white">
                {strat.name}
              </option>
            ))}
          </select>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 truncate mt-1">
            {currentStrategy?.description}
          </p>
        </div>

        {/* Initial Capital */}
        <div>
          <label className="block text-xs font-medium text-slate-700 dark:text-slate-400 mb-1">
            Initial Capital
          </label>
          <div className="relative">
            <DollarSign className="absolute left-2.5 top-2.5 h-4 w-4 text-slate-400 dark:text-slate-500" />
            <input
              type="number"
              step="1000"
              value={initialCapital}
              onChange={(e) => setInitialCapital(Number(e.target.value))}
              className="w-full bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-lg pl-8 pr-3 py-2 text-sm text-slate-900 dark:text-white font-mono focus:outline-none focus:border-cyan-500 transition shadow-inner"
            />
          </div>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
            Paper ledger cash balance
          </p>
        </div>

        {/* Slippage & Execution Timing */}
        <div>
          <label className="block text-xs font-medium text-slate-700 dark:text-slate-400 mb-1">
            Execution Rule & Slippage
          </label>
          <div className="flex gap-2">
            <select
              value={executionPrice}
              onChange={(e) => setExecutionPrice(e.target.value as "next_open" | "next_close")}
              className="w-1/2 bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-lg px-2 py-2 text-xs text-slate-900 dark:text-white focus:outline-none focus:border-cyan-500 transition cursor-pointer shadow-xs"
            >
              <option value="next_open" className="bg-white dark:bg-slate-900 text-slate-900 dark:text-white">Next Open (T+1)</option>
              <option value="next_close" className="bg-white dark:bg-slate-900 text-slate-900 dark:text-white">Next Close (T+1)</option>
            </select>
            <input
              type="number"
              step="0.0001"
              value={slippage}
              onChange={(e) => setSlippage(Number(e.target.value))}
              title="Slippage fraction (e.g. 0.0005 = 5 bps)"
              className="w-1/2 bg-slate-50 dark:bg-slate-950 border border-slate-300 dark:border-slate-800 rounded-lg px-2 py-2 text-xs text-slate-900 dark:text-white font-mono focus:outline-none focus:border-cyan-500 transition shadow-inner"
            />
          </div>
          <p className="text-[11px] text-slate-500 dark:text-slate-400 mt-1">
            Mode: {executionPrice} | Slip: {(slippage * 100).toFixed(2)}%
          </p>
        </div>
      </div>

      {/* Dynamic Strategy Parameters */}
      {currentStrategy?.parameters && currentStrategy.parameters.length > 0 && (
        <div className="p-3 bg-slate-50/80 dark:bg-slate-950/60 rounded-lg border border-slate-200 dark:border-slate-800/80 mt-1">
          <div className="text-xs font-semibold text-slate-700 dark:text-slate-400 mb-2 uppercase tracking-wider flex items-center gap-1.5">
            <ArrowRightLeft className="h-3 w-3 text-cyan-600 dark:text-cyan-400" />
            Strategy Tunables ({currentStrategy.name})
          </div>
          <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
            {currentStrategy.parameters.map((param) => (
              <div key={param.name}>
                <label className="block text-[11px] text-slate-600 dark:text-slate-400 mb-1 font-mono">
                  {param.name}
                </label>
                <input
                  type={param.type === "integer" || param.type === "number" ? "number" : "text"}
                  step={param.type === "number" ? "0.01" : "1"}
                  value={
                    strategyParams[param.name] !== undefined
                      ? (strategyParams[param.name] as string | number)
                      : (param.default as string | number)
                  }
                  onChange={(e) =>
                    handleParamChange(
                      param.name,
                      param.type === "integer" || param.type === "number"
                        ? Number(e.target.value)
                        : e.target.value,
                    )
                  }
                  className="w-full bg-white dark:bg-slate-900 border border-slate-300 dark:border-slate-800 rounded px-2 py-1.5 text-xs text-slate-900 dark:text-white font-mono focus:outline-none focus:border-cyan-500 shadow-inner"
                />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
        <div className="flex items-center space-x-2">
          <button
            onClick={onExecute}
            disabled={isLoading}
            className="flex items-center space-x-2 px-5 py-2.5 rounded-lg bg-gradient-to-r from-cyan-600 to-blue-600 hover:from-cyan-500 hover:to-blue-500 text-white font-semibold text-sm shadow-md shadow-cyan-600/30 transition cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Play className={`h-4 w-4 fill-white ${isLoading ? "animate-pulse" : ""}`} />
            <span>{isLoading ? "Executing Paper Engine..." : "Run Paper Trade"}</span>
          </button>

          <button
            onClick={onSimulateTick}
            disabled={isLoading}
            className="flex items-center space-x-1.5 px-4 py-2.5 rounded-lg bg-slate-100 hover:bg-slate-200 dark:bg-slate-800 dark:hover:bg-slate-700 text-slate-800 dark:text-slate-200 text-sm font-medium border border-slate-300 dark:border-slate-700 transition cursor-pointer disabled:opacity-50 shadow-xs"
            title="Simulate incoming real-time market candle tick"
          >
            <Radio className="h-4 w-4 text-emerald-600 dark:text-emerald-400 animate-pulse" />
            <span>Simulate Live Bar</span>
          </button>
        </div>

        <button
          onClick={onReset}
          disabled={isLoading}
          className="flex items-center space-x-1 px-3 py-2 rounded-lg bg-white hover:bg-slate-100 dark:bg-slate-950 dark:hover:bg-slate-800 text-slate-600 dark:text-slate-400 hover:text-slate-900 dark:hover:text-slate-200 text-xs font-medium border border-slate-300 dark:border-slate-800 transition cursor-pointer shadow-xs"
        >
          <RotateCcw className="h-3.5 w-3.5" />
          <span>Reset</span>
        </button>
      </div>
    </div>
  );
};
