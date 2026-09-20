"use client";

import Link from "next/link";
import { useMemo, useRef, useState } from "react";
import { ASSETS, getHistory, type AssetMeta } from "@/lib/mock-data";
import { useOverviewData } from "@/hooks/useOverviewData";
import { formatPercent, formatPrice } from "@/lib/format";
import { Card, PageHeader, inputCls } from "@/components/ui";

type Filter = "All" | "Equity" | "Indian Equity" | "US Equity" | "Crypto" | "Commodity" | "Index";

const EQUITY_CHILDREN: { label: string; value: Filter }[] = [
  { label: "All Equities", value: "Equity" },
  { label: "Indian Equity", value: "Indian Equity" },
  { label: "US Equity", value: "US Equity" },
];

const TOP_LEVEL: { label: string; value: Filter; hasSub?: boolean }[] = [
  { label: "All", value: "All" },
  { label: "Equity", value: "Equity", hasSub: true },
  { label: "Crypto", value: "Crypto" },
  { label: "Commodity", value: "Commodity" },
  { label: "Index", value: "Index" },
];

function matches(a: AssetMeta, f: Filter): boolean {
  switch (f) {
    case "All":
      return true;
    case "Equity":
      return a.assetClass === "Equity";
    case "Indian Equity":
      return a.assetClass === "Equity" && a.region === "IN";
    case "US Equity":
      return a.assetClass === "Equity" && a.region === "US";
    default:
      return a.assetClass === f;
  }
}

function classLabel(a: AssetMeta): string {
  if (a.assetClass === "Equity") return a.region === "IN" ? "Indian Equity" : "US Equity";
  return a.assetClass;
}

function ClassFilter({
  value,
  onChange,
}: {
  value: Filter;
  onChange: (f: Filter) => void;
}) {
  const [open, setOpen] = useState(false);
  const [subOpen, setSubOpen] = useState(false);
  const closeTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  const pick = (f: Filter) => {
    onChange(f);
    setOpen(false);
    setSubOpen(false);
  };

  const scheduleClose = () => {
    if (closeTimer.current) clearTimeout(closeTimer.current);
    closeTimer.current = setTimeout(() => {
      setOpen(false);
      setSubOpen(false);
    }, 120);
  };
  const cancelClose = () => {
    if (closeTimer.current) clearTimeout(closeTimer.current);
  };

  return (
    <div className="relative" onMouseLeave={scheduleClose}>
      <button
        onClick={() => setOpen((o) => !o)}
        onMouseEnter={() => {
          cancelClose();
          setOpen(true);
        }}
        className={`${inputCls} flex w-[190px] cursor-pointer items-center justify-between text-left`}
        aria-haspopup="menu"
        aria-expanded={open}
      >
        <span>{value}</span>
        <span className="text-(--color-muted)">▾</span>
      </button>

      {open && (
        <div
          className="card absolute z-20 mt-1 w-[190px] overflow-visible p-1 shadow-lg"
          role="menu"
          onMouseEnter={cancelClose}
        >
          {TOP_LEVEL.map((item) => (
            <div key={item.value} className="relative">
              <button
                role="menuitem"
                onClick={() => pick(item.value)}
                onMouseEnter={() => {
                  cancelClose();
                  setSubOpen(!!item.hasSub);
                }}
                className={`flex w-full items-center justify-between rounded-md px-3 py-2 text-left text-sm hover:bg-(--color-elev) ${
                  value === item.value ||
                  (item.hasSub && (value === "Indian Equity" || value === "US Equity"))
                    ? "font-semibold"
                    : ""
                }`}
              >
                <span>{item.label}</span>
                {item.hasSub && <span className="text-(--color-muted)">›</span>}
              </button>

              {item.hasSub && subOpen && (
                <div
                  className="card absolute top-0 left-full z-30 ml-1 w-[170px] p-1 shadow-lg"
                  role="menu"
                  onMouseEnter={cancelClose}
                  onMouseLeave={scheduleClose}
                >
                  {EQUITY_CHILDREN.map((child) => (
                    <button
                      key={child.value}
                      role="menuitem"
                      onClick={(e) => {
                        e.stopPropagation();
                        pick(child.value);
                      }}
                      className={`block w-full rounded-md px-3 py-2 text-left text-sm hover:bg-(--color-elev) ${
                        value === child.value ? "font-semibold" : ""
                      }`}
                    >
                      {child.label}
                    </button>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

export default function MarketsPage() {
  const [q, setQ] = useState("");
  const [cls, setCls] = useState<Filter>("All");
  const { histories } = useOverviewData();

  const rows = useMemo(
    () =>
      ASSETS.filter(
        (a) =>
          matches(a, cls) &&
          (a.symbol.toLowerCase().includes(q.toLowerCase()) || a.name.toLowerCase().includes(q.toLowerCase())),
      ).map((a) => {
        const bars = histories?.[a.symbol] ?? getHistory(a.symbol);
        const c = bars.map((b) => b.close);
        const last = c[c.length - 1] ?? 0;
        const d1 = c.length >= 2 ? last / c[c.length - 2] - 1 : 0;
        const m1 = c.length >= 22 ? last / c[c.length - 22] - 1 : d1;
        const rets = c.slice(1).map((v, i) => v / c[i] - 1);
        const mean = rets.length > 0 ? rets.reduce((x, y) => x + y, 0) / rets.length : 0;
        const vol =
          rets.length > 1
            ? Math.sqrt(rets.reduce((x, y) => x + (y - mean) * (y - mean), 0) / (rets.length - 1)) * Math.sqrt(252)
            : 0;
        return { meta: a, last, d1, m1, vol };
      }),
    [q, cls, histories],
  );

  return (
    <div>
      <PageHeader title="Markets" sub="Asset discovery across equities, crypto, commodities and indices" />
      <div className="mb-4 flex gap-3">
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search asset…" className={`${inputCls} max-w-xs`} />
        <ClassFilter value={cls} onChange={setCls} />
      </div>
      <Card>
        <table className="w-full text-sm">
          <thead>
            <tr className="text-left text-xs text-(--color-muted)">
              <th className="py-2">Asset</th>
              <th>Class</th>
              <th className="text-right">Price</th>
              <th className="text-right">1D</th>
              <th className="text-right">1M</th>
              <th className="text-right">Vol</th>
              <th className="text-right">Source</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((r) => (
              <tr key={r.meta.symbol} className="border-t border-(--color-edge)">
                <td className="py-2.5">
                  <Link href={`/assets/${encodeURIComponent(r.meta.symbol)}`} className="font-medium hover:underline">
                    {r.meta.symbol}
                  </Link>
                  <span className="ml-2 text-xs text-(--color-muted)">{r.meta.name}</span>
                </td>
                <td className="text-(--color-muted)">{classLabel(r.meta)}</td>
                <td className="tnum text-right">{formatPrice(r.last, r.meta.currency, r.meta.currency === "INR" ? 0 : 2)}</td>
                <td className={`tnum text-right ${r.d1 >= 0 ? "text-(--color-up)" : "text-(--color-down)"}`}>{formatPercent(r.d1)}</td>
                <td className={`tnum text-right ${r.m1 >= 0 ? "text-(--color-up)" : "text-(--color-down)"}`}>{formatPercent(r.m1)}</td>
                <td className="tnum text-right">{formatPercent(r.vol)}</td>
                <td className="text-right text-(--color-muted)">{r.meta.provider}</td>
              </tr>
            ))}
          </tbody>
        </table>
        {rows.length === 0 && (
          <p className="py-8 text-center text-sm text-(--color-muted)">No assets match this filter.</p>
        )}
      </Card>
    </div>
  );
}
