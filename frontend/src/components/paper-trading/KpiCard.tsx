"use client";

import React from "react";
import type { LucideIcon } from "lucide-react";
import { TrendingUp, TrendingDown } from "lucide-react";

interface KpiCardProps {
  title: string;
  value: string | number;
  subtitle?: string;
  icon: LucideIcon;
  trend?: "up" | "down" | "neutral";
  trendValue?: string;
  tone?: "emerald" | "rose" | "cyan" | "amber" | "blue" | "slate";
}

export const KpiCard: React.FC<KpiCardProps> = ({
  title,
  value,
  subtitle,
  icon: Icon,
  trend,
  trendValue,
  tone = "slate",
}) => {
  const toneClasses = {
    emerald: "border-emerald-200 dark:border-emerald-500/20 bg-gradient-to-b from-emerald-50/70 to-white dark:from-emerald-950/20 dark:to-slate-900/60 text-emerald-700 dark:text-emerald-400",
    rose: "border-rose-200 dark:border-rose-500/20 bg-gradient-to-b from-rose-50/70 to-white dark:from-rose-950/20 dark:to-slate-900/60 text-rose-700 dark:text-rose-400",
    cyan: "border-cyan-200 dark:border-cyan-500/20 bg-gradient-to-b from-cyan-50/70 to-white dark:from-cyan-950/20 dark:to-slate-900/60 text-cyan-700 dark:text-cyan-400",
    amber: "border-amber-200 dark:border-amber-500/20 bg-gradient-to-b from-amber-50/70 to-white dark:from-amber-950/20 dark:to-slate-900/60 text-amber-700 dark:text-amber-400",
    blue: "border-blue-200 dark:border-blue-500/20 bg-gradient-to-b from-blue-50/70 to-white dark:from-blue-950/20 dark:to-slate-900/60 text-blue-700 dark:text-blue-400",
    slate: "border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900/60 text-slate-700 dark:text-slate-300",
  };

  const iconBgClasses = {
    emerald: "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400",
    rose: "bg-rose-500/10 text-rose-600 dark:text-rose-400",
    cyan: "bg-cyan-500/10 text-cyan-600 dark:text-cyan-400",
    amber: "bg-amber-500/10 text-amber-600 dark:text-amber-400",
    blue: "bg-blue-500/10 text-blue-600 dark:text-blue-400",
    slate: "bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400",
  };

  return (
    <div className={`p-4 rounded-xl border backdrop-blur-sm transition-all hover:border-slate-400 dark:hover:border-slate-700 shadow-xs dark:shadow-none ${toneClasses[tone]}`}>
      <div className="flex items-center justify-between">
        <span className="text-xs font-medium text-slate-600 dark:text-slate-400 uppercase tracking-wider">
          {title}
        </span>
        <div className={`p-2 rounded-lg ${iconBgClasses[tone]}`}>
          <Icon className="h-4 w-4" />
        </div>
      </div>

      <div className="mt-3 flex items-baseline justify-between">
        <div className="text-2xl font-bold font-mono tracking-tight text-slate-900 dark:text-white">
          {value}
        </div>
        {trend && trendValue && (
          <div
            className={`flex items-center text-xs font-semibold font-mono ${
              trend === "up" ? "text-emerald-600 dark:text-emerald-400" : trend === "down" ? "text-rose-600 dark:text-rose-400" : "text-slate-600 dark:text-slate-400"
            }`}
          >
            {trend === "up" && <TrendingUp className="h-3.5 w-3.5 mr-0.5" />}
            {trend === "down" && <TrendingDown className="h-3.5 w-3.5 mr-0.5" />}
            {trendValue}
          </div>
        )}
      </div>

      {subtitle && (
        <div className="mt-1 text-xs text-slate-500 dark:text-slate-400 font-mono">
          {subtitle}
        </div>
      )}
    </div>
  );
};
