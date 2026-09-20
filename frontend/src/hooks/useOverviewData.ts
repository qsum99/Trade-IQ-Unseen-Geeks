"use client";

import { useQuery } from "@tanstack/react-query";
import { apiData } from "@/api/client";
import { endpoints } from "@/api/endpoints";
import { ASSETS, getHistory } from "@/lib/mock-data";
import type { Bar } from "@/lib/mock-data";

interface AssetHistoryData {
  symbol: string;
  interval: string;
  currency: string;
  data: Array<{
    timestamp?: string;
    date?: string;
    open: number;
    high: number;
    low: number;
    close: number;
    adjusted_close: number | null;
    volume: number | null;
    currency?: string;
    exchange?: string;
    provider?: string;
    interval?: string;
  }>;
}

export function useOverviewData() {
  const assetSymbols = ASSETS.map((a) => a.symbol);

  const { data: histories, isLoading, error } = useQuery({
    queryKey: ["overview-histories"],
    queryFn: async () => {
      const results = await Promise.all(
        assetSymbols.map(async (symbol) => {
          try {
            const res = await apiData<AssetHistoryData>(
              endpoints.assetHistory(symbol, {
                start_date: "2024-09-01",
                end_date: "2026-09-20",
                interval: "1d",
              })
            );

            const rawBars = res?.data;
            if (Array.isArray(rawBars) && rawBars.length > 0) {
              const bars: Bar[] = rawBars.map((d) => ({
                date: d.date ?? (d.timestamp ? d.timestamp.split("T")[0] : ""),
                open: Number(d.open),
                high: Number(d.high),
                low: Number(d.low),
                close: Number(d.close),
                volume: Number(d.volume ?? 0),
              }));
              return { symbol, bars };
            }
          } catch (err) {
            console.warn(`[useOverviewData] Could not fetch real data for ${symbol}, using fallback`, err);
          }
          return { symbol, bars: getHistory(symbol, 760) };
        })
      );

      const map: Record<string, Bar[]> = {};
      results.forEach(({ symbol, bars }) => {
        map[symbol] = bars && bars.length > 0 ? bars : getHistory(symbol, 760);
      });
      return map;
    },
    staleTime: 60 * 1000,
    refetchInterval: 60 * 1000,
  });

  return { histories, isLoading, error };
}