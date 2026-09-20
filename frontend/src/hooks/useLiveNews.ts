"use client";

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { apiData, apiClient } from "@/api/client";
import { endpoints } from "@/api/endpoints";
import type { FinancialNewsItem, NewsCategory } from "@/types/news";

export function useLiveNews(params?: {
  category?: NewsCategory;
  symbol?: string;
  limit?: number;
  refetchInterval?: number;
}) {
  const category = params?.category ?? "all";
  const symbol = params?.symbol;
  const limit = params?.limit ?? 25;
  const refetchInterval = params?.refetchInterval ?? 60000;

  return useQuery({
    queryKey: ["live-news", category, symbol ?? "all", limit],
    queryFn: async () => {
      return await apiData<FinancialNewsItem[]>(
        endpoints.news({ category, symbol, limit })
      );
    },
    refetchInterval,
    staleTime: 30000,
  });
}

export function useBreakingNews(limit = 6) {
  return useQuery({
    queryKey: ["breaking-news", limit],
    queryFn: async () => {
      return await apiData<FinancialNewsItem[]>(
        endpoints.newsBreaking({ limit })
      );
    },
    refetchInterval: 45000, // Poll breaking news every 45s
    staleTime: 20000,
  });
}

export function useForceRefreshNews() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async () => {
      return await apiClient(endpoints.newsRefresh(), { method: "POST" });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["live-news"] });
      queryClient.invalidateQueries({ queryKey: ["breaking-news"] });
    },
  });
}
