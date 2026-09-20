"use client";

import { useMemo, useRef, useState } from "react";
import { searchAssets } from "@/lib/mock-data";
import { inputCls } from "@/components/ui";

/** Shared asset search with suggestion dropdown (symbol / name / aliases). */
export function AssetSearch({
  exclude = [],
  onAdd,
  placeholder = "Search assets… (e.g. nasdaq, snp)",
  width = "w-[240px]",
  label,
}: {
  exclude?: string[];
  onAdd: (symbol: string) => void;
  placeholder?: string;
  width?: string;
  label?: string;
}) {
  const [q, setQ] = useState("");
  const [open, setOpen] = useState(false);
  const closeTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  const results = useMemo(() => searchAssets(q, exclude), [q, exclude]);

  const cancelClose = () => {
    if (closeTimer.current) clearTimeout(closeTimer.current);
  };
  const scheduleClose = () => {
    cancelClose();
    closeTimer.current = setTimeout(() => setOpen(false), 120);
  };

  return (
    <div className="relative" onMouseLeave={scheduleClose}>
      {label && (
        <span className="mb-1 block text-xs font-medium tracking-wide text-(--color-muted) uppercase">
          {label}
        </span>
      )}
      <input
        value={q}
        onChange={(e) => {
          setQ(e.target.value);
          setOpen(true);
        }}
        onFocus={() => setOpen(true)}
        onMouseEnter={cancelClose}
        onKeyDown={(e) => {
          if (e.key === "Enter" && results.length > 0) {
            onAdd(results[0].symbol);
            setQ("");
            setOpen(false);
          }
          if (e.key === "Escape") setOpen(false);
        }}
        placeholder={placeholder}
        className={`${inputCls} ${width}`}
        aria-label={label ?? placeholder}
      />
      {open && q.trim() !== "" && (
        <div className="card absolute z-20 mt-1 w-full min-w-[240px] p-1 shadow-lg anim-slideUp" onMouseEnter={cancelClose}>
          {results.length === 0 && (
            <div className="px-3 py-2 text-sm text-(--color-muted)">No matches</div>
          )}
          {results.map((a) => (
            <button
              key={a.symbol}
              onClick={() => {
                onAdd(a.symbol);
                setQ("");
                setOpen(false);
              }}
              className="block w-full rounded-md px-3 py-2 text-left text-sm transition-colors duration-600 hover:bg-(--color-elev)"
            >
              <span className="font-medium">{a.symbol}</span>
              <span className="ml-2 text-xs text-(--color-muted)">{a.name}</span>
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
