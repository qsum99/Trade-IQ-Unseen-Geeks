"use client";

import Link from "next/link";
import { useQuery } from "@tanstack/react-query";
import { ASSETS } from "@/lib/mock-data";
import { formatPrice } from "@/lib/format";
import { Card, PageHeader } from "@/components/ui";

interface AssetInfo {
  symbol: string;
  name: string;
  asset_class: string;
  currency: string;
  exchange: string;
  provider: string;
  active: boolean;
}

export default function AssetsPage() {
  const { data: assetsData, isLoading, error } = useQuery({
    queryKey: ["assets-list"],
    queryFn: async () => {
      const response = await fetch("/api/v1/assets");
      const data = await response.json();
      return data.success ? data.data : [];
    },
  });

  if (isLoading) {
    return (
      <div className="p-8">
        <div className="flex items-center justify-center h-64">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-(--color-info)"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8">
        <div className="text-center text-(--color-down) py-8">
          Failed to load assets. Please try again later.
        </div>
      </div>
    );
  }

  return (
    <div className="p-8">
      <h1 className="text-2xl font-semibold tracking-tight mb-1">Assets</h1>
      <p className="text-sm text-(--color-muted) mb-8">Pick an asset to open the full analysis workspace</p>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-3">
        {ASSETS.map((a) => (
          <a key={a.symbol} href={`/assets/${encodeURIComponent(a.symbol)}`}>
            <div className="transition-shadow hover:shadow-md border border-(--color-edge) bg-(--color-surface) rounded-lg p-4">
              <div className="flex items-center justify-between">
                <span className="font-semibold">{a.symbol}</span>
                <span className="text-xs text-(--color-muted)">{a.assetClass} · {a.exchange}</span>
              </div>
              <div className="mt-2">
                <span className="inline-block text-(--color-info) text-sm font-medium">
                  View analysis →
                </span>
              </div>
              <div className="mt-1 text-xs text-(--color-muted)">{a.name} · Source: {a.provider}</div>
            </div>
          </a>
        ))}
      </div>
    </div>
  );
}