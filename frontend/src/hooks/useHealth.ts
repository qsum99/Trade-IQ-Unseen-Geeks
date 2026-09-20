"use client";

import { useQuery } from "@tanstack/react-query";
import { apiData } from "@/api/client";
import { endpoints } from "@/api/endpoints";
import type { HealthStatus } from "@/types/api";

/** Backend liveness — powers the top-bar `● API Connected` badge. */
export function useHealth() {
  return useQuery({
    queryKey: ["health"],
    queryFn: () => apiData<HealthStatus>(endpoints.health()),
    refetchInterval: 60_000,
  });
}
