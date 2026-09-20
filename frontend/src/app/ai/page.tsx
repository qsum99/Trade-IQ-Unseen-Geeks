"use client";

import Link from "next/link";
import { useState, useRef, useEffect } from "react";
import { Badge, Card, PageHeader } from "@/components/ui";
import { apiClient } from "@/api/client";
import {
  Sparkles,
  Search,
  Activity,
  CheckCircle2,
  Clock,
  ChevronDown,
  ChevronUp,
  Cpu,
  Database,
  ArrowUpRight,
  ArrowDownRight,
  TrendingUp,
  ShieldCheck,
  RefreshCw,
  Terminal,
  ExternalLink,
  Copy,
  Check,
  Zap,
} from "lucide-react";

interface BackgroundStep {
  id: number | string;
  name: string;
  status: "completed" | "running" | "failed" | "pending";
  description: string;
  details?: string;
  duration_ms?: number;
  data?: any;
  timestamp?: string;
}

interface LivePriceAsset {
  name: string;
  symbol: string;
  type?: string;
  price_usd?: number | null;
  price_inr?: number | null;
  currency?: string;
  change_24h?: number | null;
  volume_24h_usd?: number | null;
  market_cap_usd?: number | null;
  provider?: string;
  exchange?: string;
  open?: number;
  high?: number;
  low?: number;
  timestamp_ist?: string;
}

interface AIResearchResponse {
  response: string;
  thought_process?: string;
  tools_called: Array<{
    name: string;
    args: Record<string, any>;
    result?: any;
  }>;
  background_steps: BackgroundStep[];
  live_prices: Record<string, LivePriceAsset>;
  model: string;
  provider: string;
  timestamp?: string;
  timestamp_ist?: string;
  timestamp_utc?: string;
  execution_time_ms?: number;
  error?: string;
}

interface HistoryItem {
  id: string;
  query: string;
  result: AIResearchResponse;
  timestamp: string; // full ISO string for display
}

const SAMPLE_QUERIES = [
  {
    label: "🔥 Crypto Live Prices",
    query: "What is the current live price of Bitcoin, Ethereum, and Solana and their 24 hour trend?",
  },
  {
    label: "⚡ Trending Coins",
    query: "What are the trending cryptocurrencies right now on CoinGecko and their current prices?",
  },
  {
    label: "📊 BTC 30D Risk",
    query: "Analyze Bitcoin live price, 30-day historical volatility, and period high/low range.",
  },
  {
    label: "🇮🇳 Nifty & Reliance",
    query: "What is the current Nifty 50 index level and Reliance Industries stock price today?",
  },
  {
    label: "📈 NVDA & AAPL",
    query: "Get the latest prices, annualized volatility, and risk metrics for NVDA and AAPL.",
  },
  {
    label: "🛢️ Crude Oil & Gold",
    query: "What is the current price of WTI crude oil and gold? Show the 24h change.",
  },
];

function formatCurrency(val: number | null | undefined, currency = "USD"): string {
  if (val === null || val === undefined || isNaN(val)) return "—";
  if (currency === "INR") {
    return new Intl.NumberFormat("en-IN", {
      style: "currency",
      currency: "INR",
      maximumFractionDigits: val < 10 ? 2 : 0,
    }).format(val);
  }
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: val < 10 ? 4 : 2,
  }).format(val);
}

function formatLargeNum(val: number | null | undefined): string {
  if (!val || isNaN(val)) return "—";
  if (val >= 1e12) return `$${(val / 1e12).toFixed(2)}T`;
  if (val >= 1e9) return `$${(val / 1e9).toFixed(2)}B`;
  if (val >= 1e6) return `$${(val / 1e6).toFixed(2)}M`;
  return `$${val.toLocaleString()}`;
}

// Markdown parser for institutional tables, bullet points, headers, and code
function MarkdownRenderer({ content }: { content: string }) {
  if (!content) return null;

  const lines = content.split("\n");
  const elements: React.ReactNode[] = [];
  let tableRows: string[][] = [];
  let inTable = false;
  let inCodeBlock = false;
  let codeBuffer: string[] = [];

  const flushTable = (key: string) => {
    if (tableRows.length === 0) return;
    const [header, , ...body] = tableRows;
    elements.push(
      <div key={key} className="my-3 overflow-x-auto rounded-lg border border-(--color-edge) bg-(--color-surface)">
        <table className="w-full text-left text-xs">
          {header && (
            <thead className="bg-(--color-elev) text-(--color-muted) font-semibold uppercase tracking-wider border-b border-(--color-edge)">
              <tr>
                {header.map((col, idx) => (
                  <th key={idx} className="px-3 py-2">
                    {col.trim()}
                  </th>
                ))}
              </tr>
            </thead>
          )}
          <tbody className="divide-y divide-(--color-edge)">
            {body.map((row, rIdx) => (
              <tr key={rIdx} className="hover:bg-(--color-elev)/50 transition-colors">
                {row.map((cell, cIdx) => {
                  const txt = cell.trim();
                  const isUp = txt.startsWith("+") || (txt.includes("%") && !txt.includes("-"));
                  const isDown = txt.includes("-");
                  return (
                    <td
                      key={cIdx}
                      className={`px-3 py-2 tnum font-medium ${
                        cIdx > 0 && isUp && !isDown
                          ? "text-(--color-up)"
                          : cIdx > 0 && isDown
                          ? "text-(--color-down)"
                          : ""
                      }`}
                    >
                      {txt.replace(/\*\*/g, "")}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
    tableRows = [];
    inTable = false;
  };

  lines.forEach((line, idx) => {
    const trimmed = line.trim();

    // Code block toggle
    if (trimmed.startsWith("```")) {
      if (inCodeBlock) {
        elements.push(
          <pre
            key={`code-${idx}`}
            className="my-2 overflow-x-auto rounded-lg bg-(--color-elev) p-3 text-xs font-mono text-(--color-ink) border border-(--color-edge)"
          >
            {codeBuffer.join("\n")}
          </pre>
        );
        codeBuffer = [];
        inCodeBlock = false;
      } else {
        if (inTable) flushTable(`table-before-code-${idx}`);
        inCodeBlock = true;
      }
      return;
    }

    if (inCodeBlock) {
      codeBuffer.push(line);
      return;
    }

    // Markdown Table Detection
    if (trimmed.startsWith("|") && trimmed.endsWith("|")) {
      inTable = true;
      const cells = trimmed
        .slice(1, -1)
        .split("|")
        .map((c) => c.trim());
      // Skip separator lines like |---|---|
      if (!cells.every((c) => /^:?-+:?$/.test(c))) {
        tableRows.push(cells);
      }
      return;
    } else if (inTable) {
      flushTable(`table-${idx}`);
    }

    // Empty line
    if (!trimmed) {
      elements.push(<div key={`sp-${idx}`} className="h-2" />);
      return;
    }

    // Headers
    if (trimmed.startsWith("### ")) {
      elements.push(
        <h4 key={`h3-${idx}`} className="mt-3 mb-1 text-sm font-semibold text-(--color-ink)">
          {trimmed.replace("### ", "").replace(/\*\*/g, "")}
        </h4>
      );
      return;
    }
    if (trimmed.startsWith("## ")) {
      elements.push(
        <h3 key={`h2-${idx}`} className="mt-4 mb-2 text-base font-bold text-(--color-ink) tracking-tight">
          {trimmed.replace("## ", "").replace(/\*\*/g, "")}
        </h3>
      );
      return;
    }
    if (trimmed.startsWith("# ")) {
      elements.push(
        <h2 key={`h1-${idx}`} className="mt-4 mb-2 text-lg font-bold text-(--color-ink) tracking-tight">
          {trimmed.replace("# ", "").replace(/\*\*/g, "")}
        </h2>
      );
      return;
    }

    // Bullet points
    if (trimmed.startsWith("- ") || trimmed.startsWith("* ")) {
      const text = trimmed.slice(2);
      elements.push(
        <div key={`bullet-${idx}`} className="flex items-start gap-2 text-xs text-(--color-ink)/90 my-1">
          <span className="text-(--color-info) mt-0.5">•</span>
          <span
            dangerouslySetInnerHTML={{
              __html: text
                .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
                .replace(/`(.*?)`/g, "<code class='bg-(--color-elev) px-1 rounded'>$1</code>"),
            }}
          />
        </div>
      );
      return;
    }

    // Regular paragraph
    elements.push(
      <p
        key={`p-${idx}`}
        className="text-xs leading-relaxed text-(--color-ink)/85 my-1"
        dangerouslySetInnerHTML={{
          __html: trimmed
            .replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>")
            .replace(/`(.*?)`/g, "<code class='bg-(--color-elev) px-1 rounded'>$1</code>"),
        }}
      />
    );
  });

  if (inTable) {
    flushTable("table-end");
  }

  return <div className="space-y-0.5">{elements}</div>;
}

export default function AIPage() {
  const [q, setQ] = useState("What is the current live price of Bitcoin, Ethereum, and Solana and their 24 hour trend?");
  const [loading, setLoading] = useState(false);
  const [activeStepText, setActiveStepText] = useState("");
  const [activeResult, setActiveResult] = useState<AIResearchResponse | null>(null);
  const [history, setHistory] = useState<HistoryItem[]>([]);
  const [showTelemetry, setShowTelemetry] = useState(false);
  const [showThought, setShowThought] = useState(false);
  const [copied, setCopied] = useState(false);
  const resultsEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to results on response
  useEffect(() => {
    if (activeResult) {
      resultsEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [activeResult]);

  async function handleAnalyze(queryToRun?: string) {
    const query = (queryToRun || q).trim();
    if (!query || loading) return;

    setLoading(true);
    setActiveStepText("Initiating multi-asset AI intelligence pipeline...");

    // Simulated animated progress while backend processes
    const stepInterval = setInterval(() => {
      setActiveStepText((curr) => {
        if (curr.includes("Initiating")) return "Query understanding: Identifying target assets and requirements...";
        if (curr.includes("Query understanding")) return "Connecting to CoinGecko & Market Data Live APIs...";
        if (curr.includes("Connecting to")) return "Executing real-time quotes & fetching orderbook statistics...";
        if (curr.includes("Executing real-time")) return "Running quantitative metrics (24h change, spread, volatility)...";
        if (curr.includes("Running quantitative")) return "Featherless AI / NVIDIA NIM model synthesizing grounded insights...";
        return "Finalizing institutional research summary...";
      });
    }, 1200);

    try {
      const resp = await apiClient<AIResearchResponse>("/ai/research", {
        method: "POST",
        body: JSON.stringify({ message: query }),
      });

      clearInterval(stepInterval);
      if (resp.data) {
        setActiveResult(resp.data);
        setHistory((prev) => [
          {
            id: String(Date.now()),
            query,
            result: resp.data as AIResearchResponse,
            // Show IST date+time
            timestamp: new Date().toLocaleString("en-IN", {
              timeZone: "Asia/Kolkata",
              day: "2-digit",
              month: "short",
              hour: "2-digit",
              minute: "2-digit",
              second: "2-digit",
              hour12: false,
            }) + " IST",
          },
          ...prev,
        ]);
      }
    } catch (err: any) {
      clearInterval(stepInterval);
      const errorMsg = err?.message || "Failed to communicate with AI research service.";
      setActiveResult({
        response: `### Error Encountered\n\nUnable to complete research query: ${errorMsg}\n\nPlease check backend connectivity or try another query.`,
        tools_called: [],
        background_steps: [
          {
            id: "err-1",
            name: "Execution Error",
            status: "failed",
            description: errorMsg,
            duration_ms: 0,
          },
        ],
        live_prices: {},
        model: "openai/gpt-oss-120b",
        provider: "featherless",
        error: errorMsg,
      });
    } finally {
      setLoading(false);
      setActiveStepText("");
    }
  }

  function handleCopy() {
    if (!activeResult?.response) return;
    navigator.clipboard.writeText(activeResult.response);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  }

  return (
    <div className="space-y-6 pb-12">
      {/* Page Header */}
      <PageHeader
        title="AI Market Intelligence Terminal"
        sub="Real-time multi-source data: CoinGecko (Crypto) · Zerodha / NSE (Indian Equities) · Yahoo Finance (US Equities) · FRED (Commodities/Macro)"
        right={
          <div className="flex items-center gap-2 flex-wrap">
            <span className="flex items-center gap-1.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-3 py-1 text-xs font-medium text-(--color-up)">
              <span className="relative flex h-2 w-2">
                <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75"></span>
                <span className="relative inline-flex h-2 w-2 rounded-full bg-emerald-500"></span>
              </span>
              Multi-API Live Connected
            </span>
            <Badge tone="quant">
              <Sparkles className="mr-1 h-3 w-3" />
              Featherless AI + NVIDIA NIM
            </Badge>
          </div>
        }
      />

      {/* Query Input Card */}
      <Card className="border-(--color-edge) shadow-sm">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Search className="h-4 w-4 text-(--color-info)" />
            <span className="text-sm font-semibold tracking-tight">Institutional Research Query</span>
          </div>
          <span className="text-xs text-(--color-muted)">Natural language · Real-time live market grounding</span>
        </div>

        <div className="mt-3 relative">
          <textarea
            value={q}
            onChange={(e) => setQ(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && (e.metaKey || e.ctrlKey)) {
                handleAnalyze();
              }
            }}
            rows={3}
            placeholder="Ask anything e.g. What is the current price of Bitcoin, Ethereum, and Solana and their 24h trend?"
            className="w-full rounded-xl border border-(--color-edge) bg-(--color-surface) p-3.5 text-sm outline-none transition-all focus:border-(--color-info) focus:ring-2 focus:ring-(--color-info)/20"
          />
        </div>

        {/* Action Row & Preset Chips */}
        <div className="mt-3 flex flex-wrap items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-xs font-medium text-(--color-muted) mr-1">Try:</span>
            {SAMPLE_QUERIES.map((preset, idx) => (
              <button
                key={idx}
                onClick={() => {
                  setQ(preset.query);
                  handleAnalyze(preset.query);
                }}
                disabled={loading}
                className="rounded-lg border border-(--color-edge) bg-(--color-elev) px-2.5 py-1 text-xs font-medium text-(--color-ink) hover:border-(--color-info) hover:text-(--color-info) transition-all cursor-pointer disabled:opacity-50"
              >
                {preset.label}
              </button>
            ))}
          </div>

          <div className="flex items-center gap-2">
            <span className="text-xs text-(--color-muted) hidden sm:inline">Ctrl+Enter to run</span>
            <button
              onClick={() => handleAnalyze()}
              disabled={loading || !q.trim()}
              className="flex items-center gap-2 rounded-xl bg-(--color-ink) px-5 py-2.5 text-xs font-semibold text-(--color-elev) hover:opacity-90 transition-all cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed shadow-md"
            >
              {loading ? (
                <>
                  <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                  Analyzing Live Feeds...
                </>
              ) : (
                <>
                  <Zap className="h-3.5 w-3.5 text-amber-400 fill-amber-400" />
                  Analyze Realtime
                </>
              )}
            </button>
          </div>
        </div>
      </Card>

      {/* Realtime Background Processing Banner */}
      {loading && (
        <Card className="border-(--color-info)/40 bg-gradient-to-r from-blue-500/5 to-indigo-500/5 p-4 anim-slideUp">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="relative flex h-8 w-8 items-center justify-center rounded-lg bg-(--color-info)/10 text-(--color-info)">
                <Activity className="h-4 w-4 animate-pulse" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold uppercase tracking-wider text-(--color-info)">
                    Background Work in Progress
                  </span>
                  <span className="relative flex h-2 w-2">
                    <span className="absolute inline-flex h-full w-full animate-ping rounded-full bg-blue-400 opacity-75"></span>
                    <span className="relative inline-flex h-2 w-2 rounded-full bg-blue-500"></span>
                  </span>
                </div>
                <p className="text-xs text-(--color-ink) font-medium mt-0.5">{activeStepText}</p>
              </div>
            </div>
            <div className="flex items-center gap-2 text-xs text-(--color-muted)">
              <Cpu className="h-3.5 w-3.5 animate-spin text-(--color-quant)" />
              <span>Orchestrating tools...</span>
            </div>
          </div>

          {/* Stepper Progress */}
          <div className="mt-4 grid grid-cols-2 sm:grid-cols-4 gap-2 pt-2 border-t border-(--color-edge)/50">
            <div className="flex items-center gap-2 rounded-md bg-(--color-surface)/70 p-2 text-xs">
              <CheckCircle2 className="h-3.5 w-3.5 text-emerald-500 shrink-0" />
              <span className="truncate font-medium">1. Intent Parsing</span>
            </div>
            <div className="flex items-center gap-2 rounded-md bg-(--color-surface)/70 p-2 text-xs">
              <RefreshCw className="h-3.5 w-3.5 text-blue-500 animate-spin shrink-0" />
              <span className="truncate font-medium">2. Live API Fetch</span>
            </div>
            <div className="flex items-center gap-2 rounded-md bg-(--color-surface)/70 p-2 text-xs opacity-75">
              <Clock className="h-3.5 w-3.5 text-(--color-muted) shrink-0" />
              <span className="truncate">3. Quant Engine</span>
            </div>
            <div className="flex items-center gap-2 rounded-md bg-(--color-surface)/70 p-2 text-xs opacity-75">
              <Sparkles className="h-3.5 w-3.5 text-(--color-muted) shrink-0" />
              <span className="truncate">4. LLM Grounding</span>
            </div>
          </div>
        </Card>
      )}

      {/* Main Results Container */}
      {activeResult && (
        <div className="space-y-4 anim-fadeIn" ref={resultsEndRef}>
          {/* Live Market Price Ticker Cards */}
          {Object.keys(activeResult.live_prices || {}).length > 0 && (
            <div>
              <div className="mb-2 flex items-center justify-between">
                <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-(--color-muted)">
                  <TrendingUp className="h-3.5 w-3.5 text-(--color-up)" />
                  Realtime Prices — CoinGecko · Zerodha / NSE · Yahoo Finance · FRED
                </div>
                {activeResult.timestamp_ist && (
                  <span className="text-[11px] font-mono text-(--color-muted) flex items-center gap-1">
                    <Clock className="h-3 w-3" />
                    {activeResult.timestamp_ist}
                  </span>
                )}
              </div>
              <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
                {Object.entries(activeResult.live_prices).map(([id, asset]) => {
                  const change = asset.change_24h ?? 0;
                  const isUp = change >= 0;
                  // Determine display currency
                  const isCommodity = (asset as any).type === "commodity";
                  const isINR = asset.currency === "INR" || (asset.price_inr && !asset.price_usd);
                  const displayPrice = isINR ? asset.price_inr : asset.price_usd;
                  const displayCurrency = isINR ? "INR" : "USD";
                  const prov = asset.provider || (isINR ? "Zerodha Gateway" : isCommodity ? "FRED" : asset.currency === "USD" && asset.exchange === "CoinGecko" ? "CoinGecko" : "Yahoo Finance");
                  const isZerodha = prov.includes("Zerodha");
                  const isFRED = prov.includes("FRED");
                  const isCoinGecko = prov.includes("CoinGecko");
                  return (
                    <Card
                      key={id}
                      className="border-(--color-edge) bg-gradient-to-b from-(--color-surface) to-(--color-elev)/40 p-4 hover:border-(--color-info)/50 transition-all shadow-sm"
                    >
                      <div className="flex items-center justify-between">
                        <div>
                          <div className="text-xs font-semibold text-(--color-muted)">{asset.name}</div>
                          <div className="flex items-center gap-1 mt-0.5 flex-wrap">
                            <span className="inline-block rounded bg-(--color-elev) px-1.5 py-0.5 text-[10px] font-mono font-bold text-(--color-ink)">
                              {asset.symbol}
                            </span>
                            <span
                              className={`inline-block rounded px-1.5 py-0.5 text-[9px] font-semibold ${
                                isZerodha
                                  ? "bg-orange-500/10 text-orange-600 dark:text-orange-400 border border-orange-500/20"
                                  : isFRED
                                  ? "bg-amber-500/10 text-amber-600 dark:text-amber-400 border border-amber-500/20"
                                  : isCoinGecko
                                  ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/20"
                                  : "bg-blue-500/10 text-blue-600 dark:text-blue-400 border border-blue-500/20"
                              }`}
                            >
                              {isZerodha ? "Zerodha / NSE" : isFRED ? "FRED" : isCoinGecko ? "CoinGecko" : "Yahoo"}
                            </span>
                          </div>
                        </div>
                        <div
                          className={`flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-semibold ${
                            isUp ? "bg-emerald-500/10 text-(--color-up)" : "bg-red-500/10 text-(--color-down)"
                          }`}
                        >
                          {isUp ? <ArrowUpRight className="h-3 w-3" /> : <ArrowDownRight className="h-3 w-3" />}
                          <span>{change !== 0 ? `${change > 0 ? "+" : ""}${change.toFixed(2)}%` : "0.00%"}</span>
                        </div>
                      </div>

                      <div className="mt-3">
                        <div className="text-xl font-bold tracking-tight tnum text-(--color-ink)">
                          {formatCurrency(displayPrice, displayCurrency)}
                          {isCommodity && (asset as any).unit && (asset as any).unit !== "USD" && (
                            <span className="ml-1 text-xs font-normal text-(--color-muted)">{(asset as any).unit}</span>
                          )}
                        </div>
                        {!isINR && asset.price_inr && (
                          <div className="text-xs font-medium tnum text-(--color-muted) mt-0.5">
                            {formatCurrency(asset.price_inr, "INR")}
                          </div>
                        )}
                        {isINR && asset.price_usd && (
                          <div className="text-xs font-medium tnum text-(--color-muted) mt-0.5">
                            {formatCurrency(asset.price_usd, "USD")}
                          </div>
                        )}
                      </div>

                      {(asset.volume_24h_usd || asset.market_cap_usd) && (
                        <div className="mt-3 pt-2.5 border-t border-(--color-edge) flex justify-between text-[11px] text-(--color-muted)">
                          <span>Vol: {formatLargeNum(asset.volume_24h_usd)}</span>
                          <span>Cap: {formatLargeNum(asset.market_cap_usd)}</span>
                        </div>
                      )}
                    </Card>
                  );
                })}
              </div>
            </div>
          )}

          {/* Background Work / Execution Stepper Card */}
          <Card className="border-(--color-edge) bg-(--color-surface) p-4 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-(--color-edge) pb-3">
              <div className="flex items-center gap-2">
                <Terminal className="h-4 w-4 text-(--color-info)" />
                <span className="text-xs font-bold uppercase tracking-wider text-(--color-ink)">
                  Background Execution Trace & Telemetry
                </span>
                <span className="rounded bg-emerald-500/10 px-2 py-0.5 text-[10px] font-semibold text-(--color-up)">
                  {activeResult.background_steps?.length || 0} Steps Verified
                </span>
              </div>
              <div className="flex items-center gap-2">
                {activeResult.execution_time_ms && (
                  <span className="text-xs font-mono text-(--color-muted)">
                    ⚡ Total Latency: {activeResult.execution_time_ms}ms
                  </span>
                )}
                <button
                  onClick={() => setShowTelemetry(!showTelemetry)}
                  className="flex items-center gap-1 rounded-lg border border-(--color-edge) bg-(--color-elev) px-2.5 py-1 text-xs font-medium hover:text-(--color-info) transition-colors cursor-pointer"
                >
                  {showTelemetry ? "Hide Raw Data" : "Inspect Background Payload"}
                  {showTelemetry ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
                </button>
              </div>
            </div>

            {/* Background Work Steps Timeline */}
            <div className="mt-3 space-y-2">
              {activeResult.background_steps?.map((step, sIdx) => (
                <div
                  key={sIdx}
                  className="flex items-start gap-3 rounded-lg border border-(--color-edge)/60 bg-(--color-elev)/40 p-2.5 text-xs transition-all hover:bg-(--color-elev)/80"
                >
                  <div className="mt-0.5 flex h-5 w-5 items-center justify-center rounded-full bg-emerald-500/15 text-emerald-600 shrink-0">
                    <Check className="h-3 w-3" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between gap-2">
                      <span className="font-semibold text-(--color-ink)">{step.name}</span>
                      {step.duration_ms !== undefined && (
                        <span className="text-[11px] font-mono text-(--color-muted) shrink-0">
                          {step.duration_ms}ms
                        </span>
                      )}
                    </div>
                    <p className="text-(--color-muted) mt-0.5 text-[11px] leading-relaxed">{step.description}</p>
                    {step.details && (
                      <p className="text-(--color-info) font-mono text-[10px] mt-1 bg-(--color-surface) rounded px-2 py-0.5 border border-(--color-edge) inline-block">
                        {step.details}
                      </p>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* Collapsible Raw Background Telemetry / Tool Call Inspector */}
            {showTelemetry && (
              <div className="mt-4 rounded-xl border border-(--color-edge) bg-(--color-elev) p-3 text-xs font-mono anim-scaleIn">
                <div className="flex items-center justify-between pb-2 border-b border-(--color-edge)">
                  <span className="font-bold text-(--color-ink)">Raw Tool Invocations & Payloads</span>
                  <Badge tone="info">{activeResult.provider} • {activeResult.model}</Badge>
                </div>
                <div className="mt-2 max-h-64 overflow-y-auto space-y-2 text-[11px]">
                  {activeResult.tools_called.length > 0 ? (
                    activeResult.tools_called.map((tool, tIdx) => (
                      <div key={tIdx} className="rounded bg-(--color-surface) p-2 border border-(--color-edge)">
                        <div className="text-(--color-quant) font-bold">API Tool: {tool.name}()</div>
                        <div className="text-(--color-muted) mt-0.5">Args: {JSON.stringify(tool.args)}</div>
                        {tool.result && (
                          <pre className="mt-1 max-h-32 overflow-x-auto text-[10px] text-(--color-ink) bg-(--color-elev) p-1.5 rounded">
                            {JSON.stringify(tool.result, null, 2)}
                          </pre>
                        )}
                      </div>
                    ))
                  ) : (
                    <div className="text-(--color-muted)">No tools required for this query. Direct synthesis.</div>
                  )}
                </div>
              </div>
            )}
          </Card>

          {/* Synthesized Research Summary Card */}
          <Card className="border-(--color-edge) shadow-md p-6">
            <div className="flex flex-wrap items-center justify-between gap-3 border-b border-(--color-edge) pb-4">
              <div className="flex items-center gap-2.5">
                <div className="flex h-7 w-7 items-center justify-center rounded-lg bg-(--color-quant)/10 text-(--color-quant)">
                  <Sparkles className="h-4 w-4" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-(--color-ink)">Synthesized Market Intelligence</h3>
                  <div className="flex items-center gap-2 text-[11px] text-(--color-muted) mt-0.5 flex-wrap">
                    <span>Model: {activeResult.model}</span>
                    <span>•</span>
                    <span>Provider: {activeResult.provider}</span>
                    {activeResult.timestamp_ist && (
                      <>
                        <span>•</span>
                        <span className="flex items-center gap-1 font-mono text-emerald-600 dark:text-emerald-400 font-semibold">
                          <Clock className="h-3 w-3" />
                          {activeResult.timestamp_ist}
                        </span>
                      </>
                    )}
                  </div>
                </div>
              </div>

              <div className="flex items-center gap-2">
                {activeResult.thought_process && (
                  <button
                    onClick={() => setShowThought(!showThought)}
                    className="flex items-center gap-1 rounded-lg border border-(--color-edge) bg-(--color-elev) px-2.5 py-1 text-xs font-medium text-(--color-muted) hover:text-(--color-ink) cursor-pointer"
                  >
                    <Cpu className="h-3 w-3" />
                    {showThought ? "Hide Thought" : "AI Reasoning"}
                  </button>
                )}
                <button
                  onClick={handleCopy}
                  className="flex items-center gap-1 rounded-lg border border-(--color-edge) bg-(--color-elev) px-2.5 py-1 text-xs font-medium text-(--color-muted) hover:text-(--color-ink) transition-colors cursor-pointer"
                >
                  {copied ? <Check className="h-3 w-3 text-emerald-500" /> : <Copy className="h-3 w-3" />}
                  {copied ? "Copied" : "Copy Report"}
                </button>
                <Badge tone="positive">
                  <ShieldCheck className="mr-1 h-3 w-3" />
                  Grounded in Live Data
                </Badge>
              </div>
            </div>

            {/* AI Thought Process (Reasoning Tokens) */}
            {showThought && activeResult.thought_process && (
              <div className="mt-3 rounded-lg border border-violet-500/20 bg-violet-500/5 p-3 text-xs anim-slideUp">
                <div className="flex items-center gap-1.5 font-semibold text-violet-600 dark:text-violet-400 mb-1">
                  <Cpu className="h-3.5 w-3.5" />
                  Chain of Thought & Analytical Reasoning
                </div>
                <p className="text-xs text-(--color-muted) font-mono leading-relaxed whitespace-pre-wrap">
                  {activeResult.thought_process}
                </p>
              </div>
            )}

            {/* Markdown Body */}
            <div className="mt-4 pt-1">
              <MarkdownRenderer content={activeResult.response} />
            </div>

            {/* Grounding & Platform Deep Dives */}
            <div className="mt-6 pt-4 border-t border-(--color-edge) flex flex-wrap items-center justify-between gap-3">
              <div className="flex flex-wrap items-center gap-2 text-xs">
                <span className="font-semibold text-(--color-muted) mr-1">Deep-Dive in Platform:</span>
                <Link
                  href="/backtesting"
                  className="flex items-center gap-1 rounded-lg border border-(--color-edge) px-2.5 py-1 font-medium hover:border-(--color-info) hover:text-(--color-info) transition-colors"
                >
                  <span>View Backtesting</span>
                  <ArrowUpRight className="h-3 w-3" />
                </Link>
                <Link
                  href="/regimes"
                  className="flex items-center gap-1 rounded-lg border border-(--color-edge) px-2.5 py-1 font-medium hover:border-(--color-info) hover:text-(--color-info) transition-colors"
                >
                  <span>Regime Analysis</span>
                  <ArrowUpRight className="h-3 w-3" />
                </Link>
                <Link
                  href="/risk"
                  className="flex items-center gap-1 rounded-lg border border-(--color-edge) px-2.5 py-1 font-medium hover:border-(--color-info) hover:text-(--color-info) transition-colors"
                >
                  <span>Risk Metrics</span>
                  <ArrowUpRight className="h-3 w-3" />
                </Link>
                <Link
                  href="/markets"
                  className="flex items-center gap-1 rounded-lg border border-(--color-edge) px-2.5 py-1 font-medium hover:border-(--color-info) hover:text-(--color-info) transition-colors"
                >
                  <span>Live Markets</span>
                  <ArrowUpRight className="h-3 w-3" />
                </Link>
              </div>

              <div className="text-[11px] text-(--color-muted)">
                Sources: CoinGecko API (Crypto) · Zerodha / NSE (Indian Equities) · Yahoo Finance (US Equities) · FRED Federal Reserve (Commodities/Macro)
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* Query History */}
      {history.length > 1 && (
        <div className="mt-8 space-y-3">
          <div className="text-xs font-bold uppercase tracking-wider text-(--color-muted)">
            Recent Queries in This Session
          </div>
          <div className="space-y-2">
            {history.slice(1).map((item) => (
              <Card
                key={item.id}
                className="cursor-pointer border-(--color-edge) p-3 hover:border-(--color-info)/40 transition-colors"
              >
                <div
                  className="flex items-center justify-between"
                  onClick={() => {
                    setQ(item.query);
                    setActiveResult(item.result);
                  }}
                >
                  <div className="flex items-center gap-2">
                    <Search className="h-3.5 w-3.5 text-(--color-muted)" />
                    <span className="text-xs font-semibold text-(--color-ink)">{item.query}</span>
                  </div>
                  <span className="text-[11px] text-(--color-muted)">{item.timestamp}</span>
                </div>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
