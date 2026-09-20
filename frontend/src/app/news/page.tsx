"use client";

import { useState, useMemo } from "react";
import { 
  Globe, 
  RefreshCw, 
  Search, 
  TrendingUp, 
  TrendingDown, 
  Minus, 
  ExternalLink, 
  ShieldCheck, 
  Radio, 
  Newspaper,
  Filter,
  Flame,
  Clock
} from "lucide-react";
import { PageHeader, Card, MetricCard, Skeleton } from "@/components/ui";
import { useLiveNews, useForceRefreshNews } from "@/hooks/useLiveNews";
import { WhatsAppRegistrationBox } from "@/components/whatsapp/WhatsAppRegistrationBox";
import type { FinancialNewsItem, NewsCategory } from "@/types/news";

const CATEGORIES: { id: NewsCategory; label: string; icon: string }[] = [
  { id: "all", label: "All Markets", icon: "🌐" },
  { id: "macro", label: "Macro & Fed", icon: "🏛️" },
  { id: "crypto", label: "Crypto & Web3", icon: "⚡" },
  { id: "equities", label: "Equities & Wall St", icon: "📈" },
  { id: "india", label: "India & NSE", icon: "🇮🇳" },
];

export default function NewsPage() {
  const [category, setCategory] = useState<NewsCategory>("all");
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedSentiment, setSelectedSentiment] = useState<string>("all");
  const [selectedSymbol, setSelectedSymbol] = useState<string | null>(null);

  const { data: newsItems, isLoading, isFetching, refetch } = useLiveNews({
    category,
    limit: 60,
  });

  const refreshMutation = useForceRefreshNews();

  const handleRefresh = async () => {
    await refreshMutation.mutateAsync();
    refetch();
  };

  // Filter items
  const filteredItems = useMemo(() => {
    if (!newsItems) return [];
    return newsItems.filter((item) => {
      // Symbol filter
      if (selectedSymbol && !item.symbols.includes(selectedSymbol)) {
        return false;
      }

      // Search term filter
      if (searchTerm.trim()) {
        const query = searchTerm.toLowerCase();
        const matchTitle = item.title.toLowerCase().includes(query);
        const matchSummary = item.summary.toLowerCase().includes(query);
        const matchSource = item.source.toLowerCase().includes(query);
        const matchSymbols = item.symbols.some((s) => s.toLowerCase().includes(query));
        if (!matchTitle && !matchSummary && !matchSource && !matchSymbols) {
          return false;
        }
      }

      // Sentiment filter
      if (selectedSentiment !== "all" && item.sentiment !== selectedSentiment) {
        return false;
      }

      return true;
    });
  }, [newsItems, selectedSymbol, searchTerm, selectedSentiment]);

  // Aggregate stats
  const stats = useMemo(() => {
    if (!newsItems || newsItems.length === 0) {
      return { total: 0, bullish: 0, bearish: 0, neutral: 0, bullishRatio: 0, topSymbols: [] };
    }
    let b = 0, br = 0, n = 0;
    const symbolMap: Record<string, number> = {};

    for (const item of newsItems) {
      if (item.sentiment === "bullish") b++;
      else if (item.sentiment === "bearish") br++;
      else n++;

      for (const s of item.symbols) {
        symbolMap[s] = (symbolMap[s] || 0) + 1;
      }
    }

    const sortedSymbols = Object.entries(symbolMap)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 8)
      .map(([sym]) => sym);

    const bullishRatio = Math.round((b / newsItems.length) * 100);

    return {
      total: newsItems.length,
      bullish: b,
      bearish: br,
      neutral: n,
      bullishRatio,
      topSymbols: sortedSymbols,
    };
  }, [newsItems]);

  return (
    <div className="space-y-6">
      {/* Header */}
      <PageHeader
        title="Live Financial News Wire"
        sub="Scraped institutional news from Bloomberg, Reuters, CNBC, AP, and MarketWatch — 100% authentic, zero synthetic."
        right={
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 rounded-full bg-red-500/10 border border-red-500/30 px-3 py-1 text-xs font-semibold text-red-400">
              <span className="relative flex h-2 w-2">
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
              </span>
              REAL-TIME WIRE
            </div>

            <button
              onClick={handleRefresh}
              disabled={isFetching || refreshMutation.isPending}
              className="flex items-center gap-1.5 rounded-lg border border-(--color-edge) bg-(--color-elev) px-3 py-1.5 text-xs font-medium text-(--color-muted) hover:text-(--color-ink) hover:border-blue-500/30 transition-all disabled:opacity-50"
            >
              <RefreshCw
                size={13}
                className={isFetching || refreshMutation.isPending ? "animate-spin text-blue-400" : ""}
              />
              <span>Refresh Wire</span>
            </button>
          </div>
        }
      />

      {/* KPI Overview */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          label="Total Live Wire Reports"
          value={String(stats.total)}
          hint="Aggregated across 5 feeds"
        />
        <MetricCard
          label="Market Sentiment Index"
          value={`${stats.bullishRatio}% Bullish`}
          delta={stats.bullish - stats.bearish}
          hint={`${stats.bullish} Bull vs ${stats.bearish} Bear`}
        />
        <MetricCard
          label="Scraped Sources"
          value="12+ Publishers"
          hint="Reuters, CNBC, Bloomberg, AP"
        />
        <MetricCard
          label="Wire Latency"
          value="< 60s"
          hint="Sub-minute freshness"
        />
      </div>

      {/* WhatsApp Daily Morning Briefing Registration */}
      <WhatsAppRegistrationBox className="mt-4" />

      {/* Top Mentioned Symbols Bar */}
      {stats.topSymbols.length > 0 && (
        <Card className="flex flex-wrap items-center gap-2 p-3 bg-(--color-elev)/30">
          <span className="flex items-center gap-1 text-xs font-semibold text-(--color-muted) uppercase tracking-wider mr-2">
            <Flame size={14} className="text-amber-400" /> Hot Tickers:
          </span>
          {stats.topSymbols.map((sym) => (
            <button
              key={sym}
              onClick={() => setSelectedSymbol(selectedSymbol === sym ? null : sym)}
              className={`flex items-center gap-1 rounded-lg px-2.5 py-1 text-xs font-mono transition-all ${
                selectedSymbol === sym
                  ? "bg-blue-600 text-white shadow-sm"
                  : "bg-(--color-elev) text-blue-400 hover:bg-blue-500/20 border border-blue-500/20"
              }`}
            >
              <span>${sym}</span>
            </button>
          ))}
          {selectedSymbol && (
            <button
              onClick={() => setSelectedSymbol(null)}
              className="text-xs text-(--color-muted) hover:text-(--color-ink) underline ml-2 cursor-pointer"
            >
              Clear ticker filter
            </button>
          )}
        </Card>
      )}

      {/* Controls: Categories, Search, Sentiment tabs */}
      <div className="flex flex-wrap items-center justify-between gap-4 border-b border-(--color-edge) pb-4">
        {/* Categories */}
        <div className="flex flex-wrap items-center gap-1.5">
          {CATEGORIES.map((cat) => (
            <button
              key={cat.id}
              onClick={() => setCategory(cat.id)}
              className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-all ${
                category === cat.id
                  ? "bg-blue-600 text-white shadow-sm"
                  : "bg-(--color-elev) text-(--color-muted) hover:text-(--color-ink)"
              }`}
            >
              <span>{cat.icon}</span>
              <span>{cat.label}</span>
            </button>
          ))}
        </div>

        {/* Search & Sentiment filter */}
        <div className="flex flex-wrap items-center gap-3">
          <div className="flex items-center gap-2 rounded-lg bg-(--color-elev) px-3 py-1.5 text-xs text-(--color-muted) border border-(--color-edge) focus-within:border-blue-500/50 w-64">
            <Search size={14} className="shrink-0" />
            <input
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              placeholder="Search news or ticker…"
              className="w-full bg-transparent outline-none placeholder:text-(--color-muted) text-xs"
            />
          </div>

          <div className="flex items-center gap-1 text-xs border border-(--color-edge) rounded-lg p-1 bg-(--color-elev)">
            <button
              onClick={() => setSelectedSentiment("all")}
              className={`px-2.5 py-1 rounded text-xs font-medium transition-colors ${
                selectedSentiment === "all" ? "bg-(--color-surface) text-(--color-ink) shadow-sm" : "text-(--color-muted)"
              }`}
            >
              All ({newsItems?.length || 0})
            </button>
            <button
              onClick={() => setSelectedSentiment("bullish")}
              className={`px-2.5 py-1 rounded text-xs font-medium transition-colors flex items-center gap-1 ${
                selectedSentiment === "bullish" ? "bg-emerald-500/20 text-emerald-400 font-semibold shadow-sm" : "text-(--color-muted)"
              }`}
            >
              <TrendingUp size={12} /> Bullish ({stats.bullish})
            </button>
            <button
              onClick={() => setSelectedSentiment("bearish")}
              className={`px-2.5 py-1 rounded text-xs font-medium transition-colors flex items-center gap-1 ${
                selectedSentiment === "bearish" ? "bg-rose-500/20 text-rose-400 font-semibold shadow-sm" : "text-(--color-muted)"
              }`}
            >
              <TrendingDown size={12} /> Bearish ({stats.bearish})
            </button>
          </div>
        </div>
      </div>

      {/* News Stream Cards */}
      <div className="space-y-3">
        {isLoading && !newsItems && (
          <div className="space-y-3">
            <Skeleton className="h-28" />
            <Skeleton className="h-28" />
            <Skeleton className="h-28" />
            <Skeleton className="h-28" />
          </div>
        )}

        {!isLoading && filteredItems.length === 0 && (
          <Card className="flex flex-col items-center justify-center py-20 text-center">
            <Filter size={36} className="text-(--color-muted) mb-3" />
            <div className="text-base font-semibold text-(--color-ink)">No matching articles found</div>
            <p className="text-xs text-(--color-muted) mt-1">
              Try adjusting your search query, selecting another category, or clearing active filters.
            </p>
          </Card>
        )}

        {filteredItems.map((item) => (
          <Card
            key={item.id}
            className="group flex flex-col md:flex-row md:items-start justify-between gap-4 p-5 transition-all duration-300 hover:border-blue-500/40 hover:shadow-lg"
          >
            <div className="space-y-2 flex-1 min-w-0">
              {/* Metadata row */}
              <div className="flex flex-wrap items-center gap-2 text-xs">
                <span className="rounded bg-blue-500/10 px-2.5 py-0.5 font-semibold text-blue-600 dark:text-blue-400 border border-blue-500/20 text-xs">
                  {item.source}
                </span>

                <span className="flex items-center gap-1 text-xs text-(--color-muted)">
                  <Clock size={12} />
                  {item.time_ago}
                </span>

                {item.sentiment === "bullish" && (
                  <span className="flex items-center gap-1 rounded px-2 py-0.5 text-[11px] font-semibold uppercase bg-emerald-500/15 text-emerald-700 dark:text-emerald-400 border border-emerald-500/30">
                    <TrendingUp size={11} className="stroke-[2.5]" /> Bullish
                  </span>
                )}
                {item.sentiment === "bearish" && (
                  <span className="flex items-center gap-1 rounded px-2 py-0.5 text-[11px] font-semibold uppercase bg-rose-500/15 text-rose-700 dark:text-rose-400 border border-rose-500/30">
                    <TrendingDown size={11} className="stroke-[2.5]" /> Bearish
                  </span>
                )}
                {item.sentiment === "neutral" && (
                  <span className="flex items-center gap-1 rounded px-2 py-0.5 text-[11px] font-medium uppercase bg-zinc-500/15 text-zinc-700 dark:text-zinc-400 border border-zinc-500/30">
                    <Minus size={11} /> Neutral
                  </span>
                )}

                {item.symbols && item.symbols.map((sym) => (
                  <button
                    key={sym}
                    onClick={() => setSelectedSymbol(selectedSymbol === sym ? null : sym)}
                    className="rounded bg-(--color-elev) px-2 py-0.5 text-[11px] font-mono font-medium text-blue-600 dark:text-blue-300 hover:bg-blue-600 hover:text-white transition-colors border border-(--color-edge) cursor-pointer"
                  >
                    ${sym}
                  </button>
                ))}
              </div>

              {/* Title */}
              <h2 className="text-base font-semibold tracking-tight text-(--color-ink) group-hover:text-blue-500 transition-colors leading-snug">
                <a
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="hover:underline flex items-start gap-1.5"
                >
                  <span>{item.title}</span>
                </a>
              </h2>

              {/* Description */}
              {item.summary && (
                <p className="text-sm text-(--color-muted) leading-relaxed">
                  {item.summary}
                </p>
              )}
            </div>

            {/* Read Article Action */}
            <div className="flex md:flex-col items-center justify-end md:items-end shrink-0 gap-2">
              <a
                href={item.url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-1.5 rounded-lg bg-blue-600/10 border border-blue-500/20 px-4 py-2 text-xs font-semibold text-blue-600 dark:text-blue-400 hover:bg-blue-600 hover:text-white transition-all shadow-sm"
              >
                <span>Read Original Wire</span>
                <ExternalLink size={13} />
              </a>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
