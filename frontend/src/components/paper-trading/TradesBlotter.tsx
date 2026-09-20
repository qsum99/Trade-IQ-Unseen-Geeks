"use client";

import React, { useState, useMemo } from "react";
import {
  ListOrdered,
  ArrowDownRight,
  ArrowUpRight,
  Download,
  Filter,
  CheckCircle,
  XCircle,
  Clock,
  Search,
} from "lucide-react";
import type { Trade } from "@/types/paper-trading";

interface TradesBlotterProps {
  trades: Trade[];
  currencySymbol?: string;
}

type FilterType = "ALL" | "BUY" | "SELL" | "WINNERS" | "LOSERS";

export const TradesBlotter: React.FC<TradesBlotterProps> = ({ trades, currencySymbol = "$" }) => {
  const [filter, setFilter] = useState<FilterType>("ALL");
  const [searchQuery, setSearchQuery] = useState("");

  const stats = useMemo(() => {
    let totalRealizedPnl = 0;
    let totalFees = 0;
    let winCount = 0;
    let lossCount = 0;
    let grossProfit = 0;
    let grossLoss = 0;
    let roundTrips = 0;

    for (const t of trades) {
      totalFees += t.transaction_cost;
      if (t.side === "SELL" && t.realized_pnl !== undefined && t.realized_pnl !== null) {
        roundTrips++;
        totalRealizedPnl += t.realized_pnl;
        if (t.realized_pnl > 0) {
          winCount++;
          grossProfit += t.realized_pnl;
        } else if (t.realized_pnl < 0) {
          lossCount++;
          grossLoss += Math.abs(t.realized_pnl);
        }
      }
    }

    const winRate = roundTrips > 0 ? (winCount / roundTrips) * 100 : 0;
    const profitFactor = grossLoss > 0 ? grossProfit / grossLoss : grossProfit > 0 ? 99.9 : 0;

    return {
      totalFills: trades.length,
      roundTrips,
      totalRealizedPnl,
      totalFees,
      winCount,
      lossCount,
      winRate,
      profitFactor,
      grossProfit,
      grossLoss,
    };
  }, [trades]);

  const filteredTrades = useMemo(() => {
    return trades.filter((t) => {
      if (filter === "BUY" && t.side !== "BUY") return false;
      if (filter === "SELL" && t.side !== "SELL") return false;
      if (filter === "WINNERS" && (t.side !== "SELL" || (t.realized_pnl ?? 0) <= 0)) return false;
      if (filter === "LOSERS" && (t.side !== "SELL" || (t.realized_pnl ?? 0) >= 0)) return false;

      if (searchQuery) {
        const q = searchQuery.toLowerCase();
        const matchId = String(t.id).includes(q);
        const matchDate = t.date.toLowerCase().includes(q);
        const matchPrice = String(t.price).includes(q);
        if (!matchId && !matchDate && !matchPrice) return false;
      }

      return true;
    });
  }, [trades, filter, searchQuery]);

  const exportCSV = () => {
    if (trades.length === 0) return;
    const headers = [
      "Trade ID",
      "Date",
      "Side",
      "Order Type",
      "Fill Price",
      "Quantity",
      "Notional Value",
      "Transaction Cost",
      "Realized PnL",
      "Return Pct",
      "Holding Period",
    ];

    const rows = trades.map((t) => {
      const notional = (t.price * t.quantity).toFixed(2);
      return [
        t.id,
        t.date,
        t.side,
        t.order_type || "MARKET",
        t.price.toFixed(2),
        t.quantity.toFixed(4),
        notional,
        t.transaction_cost.toFixed(2),
        t.realized_pnl !== undefined && t.realized_pnl !== null ? t.realized_pnl.toFixed(2) : "",
        t.return_pct !== undefined && t.return_pct !== null ? `${t.return_pct.toFixed(2)}%` : "",
        t.holding_period || "",
      ];
    });

    const csvContent =
      "data:text/csv;charset=utf-8," +
      [headers.join(","), ...rows.map((e) => e.join(","))].join("\n");

    const encodedUri = encodeURI(csvContent);
    const link = document.createElement("a");
    link.setAttribute("href", encodedUri);
    link.setAttribute("download", `execution_blotter_${new Date().toISOString().slice(0, 10)}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  return (
    <div className="rounded-xl border border-(--color-edge) bg-(--color-surface) p-5 shadow-sm flex flex-col space-y-4">
      {/* Title & Controls */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3 pb-3 border-b border-(--color-edge)">
        <div className="flex items-center space-x-3">
          <div className="p-2 rounded-lg bg-cyan-500/10 border border-cyan-500/20">
            <ListOrdered className="h-5 w-5 text-cyan-600 dark:text-cyan-400" />
          </div>
          <div>
            <div className="flex items-center space-x-2">
              <h3 className="text-sm font-bold tracking-wider text-(--color-ink) uppercase m-0">
                Institutional Execution Blotter
              </h3>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/15 border border-cyan-500/30 text-cyan-600 dark:text-cyan-400 font-semibold">
                {trades.length} FILLS
              </span>
              {stats.roundTrips > 0 && (
                <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-(--color-elev) text-(--color-muted) border border-(--color-edge)">
                  {stats.roundTrips} ROUND-TRIPS
                </span>
              )}
            </div>
            <p className="text-xs text-(--color-muted) mt-0.5">
              Deterministic T+1 execution log with slippage & transaction cost modeling
            </p>
          </div>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={exportCSV}
            disabled={trades.length === 0}
            className="flex items-center space-x-1.5 px-3 py-1.5 rounded-lg bg-(--color-elev) hover:bg-(--color-edge) disabled:opacity-40 disabled:cursor-not-allowed text-(--color-ink) text-xs font-mono font-medium transition cursor-pointer border border-(--color-edge)"
            title="Export full execution blotter as CSV"
          >
            <Download className="h-3.5 w-3.5 text-(--color-muted)" />
            <span>Export CSV</span>
          </button>
        </div>
      </div>

      {/* Summary KPI Strip */}
      <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-6 gap-2.5 p-3 rounded-lg bg-(--color-elev) border border-(--color-edge) font-mono text-xs">
        <div>
          <span className="text-[10px] text-(--color-muted) uppercase tracking-wider block">Realized P&L</span>
          <span
            className={`text-sm font-bold ${
              stats.totalRealizedPnl >= 0 ? "text-emerald-600 dark:text-emerald-400" : "text-rose-600 dark:text-rose-400"
            }`}
          >
            {stats.totalRealizedPnl >= 0 ? "+" : ""}
            {currencySymbol}
            {stats.totalRealizedPnl.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
          </span>
        </div>

        <div>
          <span className="text-[10px] text-(--color-muted) uppercase tracking-wider block">Win Rate</span>
          <span className="text-sm font-bold text-(--color-ink)">
            {stats.winRate.toFixed(1)}%
            <span className="text-[10px] text-(--color-muted) font-normal ml-1">
              ({stats.winCount}W / {stats.lossCount}L)
            </span>
          </span>
        </div>

        <div>
          <span className="text-[10px] text-(--color-muted) uppercase tracking-wider block">Profit Factor</span>
          <span className="text-sm font-bold text-cyan-600 dark:text-cyan-400">
            {stats.profitFactor.toFixed(2)}
          </span>
        </div>

        <div>
          <span className="text-[10px] text-(--color-muted) uppercase tracking-wider block">Gross Profit</span>
          <span className="text-sm font-bold text-emerald-600 dark:text-emerald-400">
            +{currencySymbol}
            {stats.grossProfit.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
          </span>
        </div>

        <div>
          <span className="text-[10px] text-(--color-muted) uppercase tracking-wider block">Gross Loss</span>
          <span className="text-sm font-bold text-rose-600 dark:text-rose-400">
            -{currencySymbol}
            {stats.grossLoss.toLocaleString(undefined, { minimumFractionDigits: 0, maximumFractionDigits: 0 })}
          </span>
        </div>

        <div>
          <span className="text-[10px] text-(--color-muted) uppercase tracking-wider block">Total Fees Paid</span>
          <span className="text-sm font-bold text-amber-600 dark:text-amber-400">
            {currencySymbol}{stats.totalFees.toFixed(2)}
          </span>
        </div>
      </div>

      {/* Filter Tabs & Search */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2.5 pt-1">
        <div className="flex items-center space-x-1.5 overflow-x-auto">
          <Filter className="h-3.5 w-3.5 text-(--color-muted) mr-1 shrink-0" />
          {(["ALL", "BUY", "SELL", "WINNERS", "LOSERS"] as FilterType[]).map((tab) => {
            const count =
              tab === "ALL"
                ? trades.length
                : tab === "BUY"
                ? trades.filter((t) => t.side === "BUY").length
                : tab === "SELL"
                ? trades.filter((t) => t.side === "SELL").length
                : tab === "WINNERS"
                ? trades.filter((t) => t.side === "SELL" && (t.realized_pnl ?? 0) > 0).length
                : trades.filter((t) => t.side === "SELL" && (t.realized_pnl ?? 0) < 0).length;

            return (
              <button
                key={tab}
                onClick={() => setFilter(tab)}
                className={`px-2.5 py-1 rounded text-xs font-mono transition-all cursor-pointer shrink-0 ${
                  filter === tab
                    ? "bg-cyan-500/15 text-cyan-600 dark:text-cyan-400 border border-cyan-500/30 font-semibold"
                    : "bg-(--color-elev) text-(--color-muted) hover:text-(--color-ink) border border-(--color-edge)"
                }`}
              >
                {tab} <span className="text-[10px] opacity-70">({count})</span>
              </button>
            );
          })}
        </div>

        <div className="relative max-w-xs w-full">
          <Search className="h-3.5 w-3.5 text-(--color-muted) absolute left-2.5 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            placeholder="Search by date, price, ID..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-8 pr-3 py-1 bg-(--color-surface) border border-(--color-edge) rounded text-xs font-mono text-(--color-ink) placeholder:text-(--color-muted) focus:outline-none focus:border-cyan-500"
          />
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto max-h-96 overflow-y-auto rounded-lg border border-(--color-edge) bg-(--color-surface)">
        <table className="w-full text-left text-xs font-mono border-collapse">
          <thead>
            <tr className="border-b border-(--color-edge) text-(--color-muted) sticky top-0 bg-(--color-elev) backdrop-blur-sm z-10">
              <th className="py-2.5 px-3 font-semibold">ID</th>
              <th className="py-2.5 px-3 font-semibold">EXEC DATE & TIME</th>
              <th className="py-2.5 px-3 font-semibold">SIDE</th>
              <th className="py-2.5 px-3 font-semibold">ORDER TYPE</th>
              <th className="py-2.5 px-3 font-semibold text-right">FILL PRICE</th>
              <th className="py-2.5 px-3 font-semibold text-right">QUANTITY</th>
              <th className="py-2.5 px-3 font-semibold text-right">NOTIONAL</th>
              <th className="py-2.5 px-3 font-semibold text-right">FEE / SLIP</th>
              <th className="py-2.5 px-3 font-semibold text-right">REALIZED P&L</th>
              <th className="py-2.5 px-3 font-semibold text-left">HOLDING PERIOD</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-(--color-edge)">
            {filteredTrades.length === 0 ? (
              <tr>
                <td colSpan={10} className="py-10 text-center text-(--color-muted) font-sans">
                  {trades.length === 0
                    ? "No trades executed yet. Run paper trading to generate institutional fills."
                    : "No trades match the current filter or search criteria."}
                </td>
              </tr>
            ) : (
              filteredTrades.map((t) => {
                const notional = t.price * t.quantity;
                const isBuy = t.side === "BUY";
                const hasPnl = t.realized_pnl !== undefined && t.realized_pnl !== null;
                const isWin = (t.realized_pnl ?? 0) > 0;

                return (
                  <tr key={t.id} className="hover:bg-(--color-elev)/50 transition">
                    <td className="py-2.5 px-3 text-(--color-muted) font-semibold">
                      #{String(t.id).padStart(3, "0")}
                    </td>
                    <td className="py-2.5 px-3 text-(--color-ink)">
                      <div className="flex items-center space-x-1.5">
                        <Clock className="h-3 w-3 text-(--color-muted) shrink-0" />
                        <span>{t.date}</span>
                      </div>
                    </td>
                    <td className="py-2.5 px-3">
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded text-[11px] font-bold ${
                          isBuy
                            ? "bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30"
                            : "bg-rose-500/15 text-rose-600 dark:text-rose-400 border border-rose-500/30"
                        }`}
                      >
                        {isBuy ? (
                          <ArrowUpRight className="h-3 w-3 mr-0.5" />
                        ) : (
                          <ArrowDownRight className="h-3 w-3 mr-0.5" />
                        )}
                        {t.side}
                      </span>
                    </td>
                    <td className="py-2.5 px-3 text-(--color-muted) text-[11px]">
                      {t.order_type || "MARKET (T+1)"}
                    </td>
                    <td className="py-2.5 px-3 text-right text-(--color-ink) font-medium">
                      {currencySymbol}
                      {t.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </td>
                    <td className="py-2.5 px-3 text-right text-(--color-ink)">
                      {t.quantity < 1
                        ? t.quantity.toFixed(4)
                        : t.quantity.toLocaleString(undefined, { maximumFractionDigits: 2 })}
                    </td>
                    <td className="py-2.5 px-3 text-right text-(--color-ink)">
                      {currencySymbol}
                      {notional.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
                    </td>
                    <td className="py-2.5 px-3 text-right text-amber-600 dark:text-amber-400">
                      {currencySymbol}{t.transaction_cost.toFixed(2)}
                    </td>
                    <td className="py-2.5 px-3 text-right font-semibold">
                      {hasPnl ? (
                        <div className="flex items-center justify-end space-x-1">
                          {isWin ? (
                            <CheckCircle className="h-3 w-3 text-emerald-500 dark:text-emerald-400 shrink-0" />
                          ) : (
                            <XCircle className="h-3 w-3 text-rose-500 dark:text-rose-400 shrink-0" />
                          )}
                          <span className={isWin ? "text-emerald-600 dark:text-emerald-400" : "text-rose-600 dark:text-rose-400"}>
                            {isWin ? "+" : ""}
                            {currencySymbol}
                            {t.realized_pnl?.toLocaleString(undefined, {
                              minimumFractionDigits: 2,
                              maximumFractionDigits: 2,
                            })}
                            <span className="text-[10px] ml-1 opacity-80">
                              ({isWin ? "+" : ""}
                              {t.return_pct?.toFixed(2)}%)
                            </span>
                          </span>
                        </div>
                      ) : (
                        <span className="text-(--color-muted) font-normal">--</span>
                      )}
                    </td>
                    <td className="py-2.5 px-3 text-(--color-muted) text-[11px]">
                      {t.holding_period || (isBuy ? "Position Opened" : "--")}
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};
