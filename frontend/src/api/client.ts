// Central API client — the ONLY place that talks to the FastAPI backend.
// Per docs/api.md: base URL comes from env, never hardcoded in components.
// Backend envelope: { success, data, meta, error }.

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ??
  (typeof window !== "undefined" ? "/api/v1" : "http://localhost:8000/api/v1");

export interface ApiErrorBody {
  code: string;
  message: string;
  details?: Record<string, unknown>;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T | null;
  meta?: {
    request_id?: string;
    page?: number;
    page_size?: number;
    total?: number;
    total_pages?: number;
    [key: string]: unknown;
  };
  error?: ApiErrorBody | null;
}

export class ApiError extends Error {
  code: string;
  status: number;
  details?: Record<string, unknown>;
  requestId?: string;

  constructor(
    message: string,
    opts: {
      code?: string;
      status?: number;
      details?: Record<string, unknown>;
      requestId?: string;
    } = {},
  ) {
    super(message);
    this.name = "ApiError";
    this.code = opts.code ?? "INTERNAL_ERROR";
    this.status = opts.status ?? 500;
    this.details = opts.details;
    this.requestId = opts.requestId;
  }
}

function getAuthHeader(): Record<string, string> {
  // JWT stored by the auth flow (Settings/profile). Absent during early dev.
  if (typeof window === "undefined") return {};
  const token = window.localStorage.getItem("access_token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function apiClient<T>(
  endpoint: string,
  options?: RequestInit,
): Promise<ApiResponse<T>> {
  const res = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...getAuthHeader(),
      ...options?.headers,
    },
  });

  // 204 — no body
  if (res.status === 204) {
    return { success: true, data: null };
  }

  const requestId = res.headers.get("X-Request-ID") ?? undefined;
  let body: ApiResponse<T>;
  try {
    body = (await res.json()) as ApiResponse<T>;
  } catch {
    throw new ApiError(`Request failed with status ${res.status}`, {
      code: "INTERNAL_ERROR",
      status: res.status,
      requestId,
    });
  }

  if (!res.ok || body.success === false) {
    throw new ApiError(body.error?.message ?? `Request failed (${res.status})`, {
      code: body.error?.code ?? "INTERNAL_ERROR",
      status: res.status,
      details: body.error?.details,
      requestId: body.meta?.request_id ?? requestId,
    });
  }

  return body;
}

/** Unwrap helper for components/hooks that only need `data`. */
export async function apiData<T>(
  endpoint: string,
  options?: RequestInit,
): Promise<T> {
  const res = await apiClient<T>(endpoint, options);
  return res.data as T;
}
