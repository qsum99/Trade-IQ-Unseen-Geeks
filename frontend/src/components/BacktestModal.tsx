"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { searchAssets } from "@/lib/mock-data";
import { createBacktest, defaultPeriod } from "@/api/backtests";
import type { StrategyType } from "@/types/api";
import { inputCls } from "@/components/ui";

/**
 * "Enter the index name" dialog. Resolves the user's text to a known
 * symbol, POSTs the backtest request to the backend, then deep-links into
 * /backtesting. If the backend is unreachable, falls back to the mock
 * workspace so the demo never dead-ends.
 */
export function BacktestModal({
  strategyId,
  strategyName,
  onClose,
}: {
  strategyId: string;
  strategyName: string;
  onClose: () => void;
}) {
  const router = useRouter();
  const [q, setQ] = useState("");
  const [resolved, setResolved] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [note, setNote] = useState<string | null>(null);
  const [sending, setSending] = useState(false);

  const results = useMemo(() => searchAssets(q, [], 6), [q]);

  const resolveSymbol = (text: string): string | null => {
    const t = text.trim().toLowerCase();
    if (!t) return null;
    const hit = searchAssets(text, [], 20).find(
      (a) =>
        a.symbol.toLowerCase() === t ||
        a.name.toLowerCase() === t ||
        (a.aliases ?? []).some((k) => k === t),
    );
    return hit ? hit.symbol : null;
  };

  const submit = async () => {
    const symbol = resolved ?? resolveSymbol(q);
    if (!symbol) {
      setError("Unknown index — pick one from the suggestions (e.g. NVDA, nasdaq, snp).");
      return;
    }
    setError(null);
    setSending(true);
    setNote("Sending to backend…");
    const period = defaultPeriod();
    try {
      const res = await createBacktest({
        name: `${symbol} ${strategyName}`,
        symbol,
        strategy: { type: strategyId as StrategyType, parameters: { fast_period: 20, slow_period: 50 } },
        period,
        capital: { initial: 100000, position_sizing: "full" },
        execution: { transaction_cost: 0.001, slippage: 0.0005, execution_price: "next_open" },
        benchmark: "buy_and_hold",
      });
      router.push(`/backtesting?symbol=${encodeURIComponent(symbol)}&strategy=${strategyId}&bt=${res.backtest_id}`);
    } catch {
      setNote("Backend unreachable — opening the workspace in mock mode.");
      setTimeout(() => {
        router.push(`/backtesting?symbol=${encodeURIComponent(symbol)}&strategy=${strategyId}`);
      }, 700);
    }
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4 anim-fadeIn"
      onClick={onClose}
      role="dialog"
      aria-modal="true"
      aria-label={`Run backtest for ${strategyName}`}
    >
      <div
        className="card w-full max-w-md p-6 anim-scaleIn"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="text-lg font-semibold">Run backtest — {strategyName}</div>
        <p className="mt-1 text-sm text-(--color-muted)">
          Enter the index name. It will be sent to the backend as the backtest request.
        </p>

        <label className="mt-4 block text-sm">
          <span className="mb-1 block text-xs font-medium tracking-wide text-(--color-muted) uppercase">
            Index name
          </span>
          <input
            autoFocus
            value={q}
            onChange={(e) => {
              setQ(e.target.value);
              setResolved(null);
              setError(null);
            }}
            onKeyDown={(e) => {
              if (e.key === "Enter") submit();
              if (e.key === "Escape") onClose();
            }}
            placeholder="e.g. NVDA, nasdaq, snp, reliance…"
            className={inputCls}
          />
        </label>

        {q.trim() !== "" && !resolved && (
          <div className="card mt-2 max-h-44 overflow-y-auto p-1">
            {results.length === 0 && (
              <div className="px-3 py-2 text-sm text-(--color-muted)">No matches</div>
            )}
            {results.map((a) => (
              <button
                key={a.symbol}
                onClick={() => {
                  setResolved(a.symbol);
                  setQ(a.symbol);
                  setError(null);
                }}
                className="block w-full rounded-md px-3 py-2 text-left text-sm transition-colors duration-300 hover:bg-(--color-elev)"
              >
                <span className="font-medium">{a.symbol}</span>
                <span className="ml-2 text-xs text-(--color-muted)">{a.name} · {a.exchange}</span>
              </button>
            ))}
          </div>
        )}
        {resolved && (
          <p className="mt-2 text-xs text-(--color-up)">✓ Resolved to {resolved}</p>
        )}
        {error && <p className="mt-2 text-xs text-(--color-down)">{error}</p>}
        {note && <p className="mt-2 text-xs text-(--color-muted)">{note}</p>}

        <div className="mt-5 flex justify-end gap-2">
          <button
            onClick={onClose}
            disabled={sending}
            className="rounded-lg border border-(--color-edge) px-4 py-2 text-sm font-medium transition-all duration-600 hover:border-(--color-muted) hover:scale-105"
          >
            Cancel
          </button>
          <button
            onClick={submit}
            disabled={sending}
            className="rounded-lg bg-(--color-ink) px-4 py-2 text-sm font-semibold text-(--color-elev) transition-all duration-600 hover:scale-105 disabled:opacity-60"
          >
            {sending ? "Working…" : "Proceed"}
          </button>
        </div>
      </div>
    </div>
  );
}
