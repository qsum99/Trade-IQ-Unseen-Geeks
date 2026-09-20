// Presentation formatting ONLY. Backend returns raw decimals
// (docs/api.md §51: { return: 0.1824 }) — formatting lives here, never in API types.

export function formatPercent(value: number | null | undefined, digits = 2): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  const sign = value > 0 ? "+" : "";
  return `${sign}${(value * 100).toFixed(digits)}%`;
}

export function formatSigned(value: number | null | undefined, digits = 2): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  const sign = value > 0 ? "+" : "";
  return `${sign}${value.toFixed(digits)}`;
}

export function formatPrice(
  value: number | null | undefined,
  currency: "USD" | "INR" = "USD",
  digits = 2,
): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  const symbol = currency === "INR" ? "₹" : "$";
  return `${symbol}${value.toLocaleString("en-US", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })}`;
}

/** ISO date (2026-09-19) → display (19 Sep 2026). */
export function formatDate(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleDateString("en-GB", { day: "2-digit", month: "short", year: "numeric" });
}

/** ISO datetime → display with time. */
export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = new Date(iso);
  if (Number.isNaN(d.getTime())) return iso;
  return d.toLocaleString("en-GB", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

export function toneFor(value: number | null | undefined): "positive" | "negative" | "neutral" {
  if (value === null || value === undefined) return "neutral";
  if (value > 0) return "positive";
  if (value < 0) return "negative";
  return "neutral";
}
