"use client";

import type { ReactNode } from "react";
import { formatPercent, toneFor } from "@/lib/format";

export function Card({ children, className = "", animate = true }: { children: ReactNode; className?: string; animate?: boolean }) {
  return <div className={`card p-5 ${animate ? "anim-scaleIn" : ""} ${className}`}>{children}</div>;
}

export function PageHeader({
  title,
  sub,
  right,
}: {
  title: string;
  sub?: string;
  right?: ReactNode;
}) {
  return (
    <div className="mb-6 flex flex-wrap items-end justify-between gap-3 anim-slideUp">
      <div>
        <h1 className="text-2xl font-semibold tracking-tight">{title}</h1>
        {sub && <p className="mt-1 text-sm text-(--color-muted)">{sub}</p>}
      </div>
      {right}
    </div>
  );
}

export function MetricCard({
  label,
  value,
  delta,
  hint,
}: {
  label: string;
  value: string;
  delta?: number;
  hint?: string;
}) {
  const tone = delta === undefined ? "neutral" : toneFor(delta);
  const color =
    tone === "positive" ? "text-(--color-up)" : tone === "negative" ? "text-(--color-down)" : "text-(--color-muted)";
  return (
    <div className="card p-4 anim-slideUp">
      <div className="text-xs font-medium tracking-wide text-(--color-muted) uppercase">{label}</div>
      <div className="tnum mt-1 text-2xl font-semibold">{value}</div>
      <div className="mt-1 flex items-center gap-2 text-xs">
        {delta !== undefined && <span className={`tnum font-medium ${color}`}>{formatPercent(delta)}</span>}
        {hint && <span className="text-(--color-muted)">{hint}</span>}
      </div>
    </div>
  );
}

export function Badge({
  children,
  tone = "neutral",
}: {
  children: ReactNode;
  tone?: "positive" | "negative" | "neutral" | "warn" | "info" | "quant";
}) {
  const map: Record<string, string> = {
    positive: "bg-green-500/10 text-(--color-up)",
    negative: "bg-red-500/10 text-(--color-down)",
    neutral: "bg-(--color-elev) text-(--color-muted)",
    warn: "bg-amber-500/10 text-(--color-warn)",
    info: "bg-blue-500/10 text-(--color-info)",
    quant: "bg-violet-500/10 text-(--color-quant)",
  };
  return (
    <span className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium transition-transform duration-300 hover:scale-105 ${map[tone]}`}>
      {children}
    </span>
  );
}

export function Skeleton({ className = "h-32" }: { className?: string }) {
  return <div className={`animate-pulse rounded-lg bg-(--color-elev) ${className}`} />;
}

export function Tabs({
  tabs,
  active,
  onChange,
}: {
  tabs: string[];
  active: string;
  onChange: (t: string) => void;
}) {
  return (
    <div className="mb-4 flex gap-1 rounded-lg bg-(--color-elev) p-1 text-sm anim-slideUp">
      {tabs.map((t) => (
        <button
          key={t}
          onClick={() => onChange(t)}
          className={`rounded-md px-3 py-1.5 font-medium transition-all duration-600 ${
            active === t ? "bg-(--color-surface) shadow-sm" : "text-(--color-muted) hover:text-(--color-ink)"
          }`}
        >
          {t}
        </button>
      ))}
    </div>
  );
}

export function Field({
  label,
  children,
}: {
  label: string;
  children: ReactNode;
}) {
  return (
    <label className="block text-sm">
      <span className="mb-1 block text-xs font-medium tracking-wide text-(--color-muted) uppercase">{label}</span>
      {children}
    </label>
  );
}

export const inputCls =
  "w-full rounded-lg border border-(--color-edge) bg-(--color-surface) px-3 py-2 text-sm outline-none transition-all duration-600 focus:border-(--color-info) focus:ring-1 focus:ring-(--color-info)/30";

export function EmptyState({ title, body, action }: { title: string; body: string; action?: ReactNode }) {
  return (
    <div className="card flex flex-col items-center px-6 py-14 text-center anim-scaleIn">
      <div className="text-base font-semibold">{title}</div>
      <p className="mt-1 max-w-sm text-sm text-(--color-muted)">{body}</p>
      {action && <div className="mt-4">{action}</div>}
    </div>
  );
}
