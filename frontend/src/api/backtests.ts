import { apiData } from "./client";
import { endpoints } from "./endpoints";
import type { BacktestCreate } from "@/types/api";

export interface CreateBacktestResponse {
  backtest_id: string;
  status: string;
  job_id?: string;
}

/** POST /backtests — creates a backend backtest job (or returns 202 queued). */
export function createBacktest(payload: BacktestCreate): Promise<CreateBacktestResponse> {
  return apiData<CreateBacktestResponse>(endpoints.backtests(), {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

/** Sensible default 3-year window ending today (ISO dates). */
export function defaultPeriod(): { start_date: string; end_date: string } {
  const end = new Date();
  const start = new Date();
  start.setFullYear(end.getFullYear() - 3);
  return {
    start_date: start.toISOString().slice(0, 10),
    end_date: end.toISOString().slice(0, 10),
  };
}
