"use client";

import React from "react";
import { X, ShieldCheck, AlertTriangle, CheckCircle, AlertCircle } from "lucide-react";
import type { TrustReport } from "@/types/paper-trading";

interface TrustReportModalProps {
  isOpen: boolean;
  onClose: () => void;
  report: TrustReport | null;
}

export const TrustReportModal: React.FC<TrustReportModalProps> = ({
  isOpen,
  onClose,
  report,
}) => {
  if (!isOpen || !report) return null;

  const checks = [
    {
      title: "Lookahead Bias Check",
      data: report.lookahead_bias_check,
      desc: "Ensures signals at bar T only execute at T+1 (next open/close). No future pricing leakage.",
    },
    {
      title: "Data Leakage & Chronology Check",
      data: report.data_leakage_check,
      desc: "Validates strict monotonic date ordering across all rolling bar feed windows.",
    },
    {
      title: "Execution & Slippage Model",
      data: report.execution_model_check,
      desc: "Checks that fills apply realistic slippage penalties on both entry and exit.",
    },
    {
      title: "Transaction Cost & Tax Schedule",
      data: report.transaction_cost_check,
      desc: "Audits transaction costs, exchange turnover fees, and brokerage deductions.",
    },
    {
      title: "Out-of-Sample Window Check",
      data: report.out_of_sample_check,
      desc: "Detects overfitting by checking performance across unseen live feed periods.",
    },
  ];

  return (
    <div className="fixed inset-0 bg-black/75 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-(--color-surface) border border-(--color-edge) rounded-2xl max-w-xl w-full p-6 shadow-2xl relative flex flex-col gap-4">
        {/* Header */}
        <div className="flex items-center justify-between pb-3 border-b border-(--color-edge)">
          <div className="flex items-center space-x-2">
            <ShieldCheck className="h-5 w-5 text-indigo-500" />
            <h2 className="text-base font-bold text-(--color-ink) tracking-tight m-0">
              Institutional Trust & Audit Report
            </h2>
          </div>
          <button
            onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-(--color-elev) text-(--color-muted) hover:text-(--color-ink) transition cursor-pointer"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {/* Backtest ID & Overall status */}
        <div className="flex items-center justify-between p-3.5 bg-(--color-elev) rounded-xl border border-(--color-edge)">
          <div>
            <div className="text-[11px] font-mono text-(--color-muted) uppercase">
              Run Identifier
            </div>
            <div className="text-xs font-mono text-cyan-600 dark:text-cyan-400 truncate max-w-xs font-semibold">
              {report.backtest_id}
            </div>
          </div>
          <div className="text-right">
            <div className="text-[11px] font-mono text-(--color-muted) uppercase">
              Audit Verdict
            </div>
            <span
              className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold font-mono uppercase ${
                report.overall === "pass"
                  ? "bg-emerald-50 dark:bg-emerald-500/20 text-emerald-700 dark:text-emerald-400 border border-emerald-200 dark:border-emerald-500/40"
                  : "bg-amber-50 dark:bg-amber-500/20 text-amber-700 dark:text-amber-400 border border-amber-200 dark:border-amber-500/40"
              }`}
            >
              {report.overall === "pass" ? (
                <CheckCircle className="h-3 w-3 mr-1" />
              ) : (
                <AlertTriangle className="h-3 w-3 mr-1" />
              )}
              {report.overall}
            </span>
          </div>
        </div>

        {/* Checklist */}
        <div className="space-y-3 max-h-80 overflow-y-auto pr-1">
          {checks.map((item, idx) => {
            const status = item.data?.status || "passed";
            const isPassed = status === "passed" || status === "pass";
            const isWarning = status === "warning" || status === "review";

            return (
              <div
                key={idx}
                className="p-3 bg-(--color-elev)/70 rounded-lg border border-(--color-edge) flex items-start justify-between gap-3"
              >
                <div className="flex-1">
                  <div className="flex items-center space-x-2">
                    {isPassed ? (
                      <CheckCircle className="h-4 w-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
                    ) : isWarning ? (
                      <AlertTriangle className="h-4 w-4 text-amber-600 dark:text-amber-400 shrink-0" />
                    ) : (
                      <AlertCircle className="h-4 w-4 text-rose-600 dark:text-rose-400 shrink-0" />
                    )}
                    <span className="text-xs font-semibold text-(--color-ink)">
                      {item.title}
                    </span>
                  </div>
                  <p className="text-[11px] text-(--color-muted) mt-1 leading-relaxed">
                    {item.desc}
                  </p>
                  {item.data?.message && (
                    <div className="text-[10px] font-mono text-amber-700 dark:text-amber-400 mt-1 bg-amber-500/10 px-2 py-0.5 rounded border border-amber-500/30 inline-block">
                      Note: {item.data.message}
                    </div>
                  )}
                </div>

                <span
                  className={`px-2 py-0.5 rounded text-[10px] font-mono uppercase font-bold shrink-0 border ${
                    isPassed
                      ? "text-emerald-700 dark:text-emerald-400 bg-emerald-500/10 border-emerald-500/30"
                      : isWarning
                      ? "text-amber-700 dark:text-amber-400 bg-amber-500/10 border-amber-500/30"
                      : "text-rose-700 dark:text-rose-400 bg-rose-500/10 border-rose-500/30"
                  }`}
                >
                  {status}
                </span>
              </div>
            );
          })}
        </div>

        {/* Footer */}
        <div className="pt-2 flex justify-end">
          <button
            onClick={onClose}
            className="px-4 py-2 rounded-lg bg-(--color-elev) hover:bg-(--color-edge) text-(--color-ink) text-xs font-semibold transition cursor-pointer border border-(--color-edge) shadow-xs"
          >
            Close Audit
          </button>
        </div>
      </div>
    </div>
  );
};
