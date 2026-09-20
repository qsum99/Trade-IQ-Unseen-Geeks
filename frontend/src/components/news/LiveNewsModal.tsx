"use client";

import { useState, useMemo } from "react";
import Link from "next/link";
import { 
  X, 
  ExternalLink, 
  RefreshCw, 
  Search, 
  Radio, 
  TrendingUp, 
  TrendingDown, 
  Minus, 
  ShieldCheck,
  Globe,
  Filter,
  ArrowUpRight
} from "lucide-react";
import { useLiveNews, useForceRefreshNews } from "@/hooks/useLiveNews";
import type { FinancialNewsItem, NewsCategory } from "@/types/news";

interface LiveNewsModalProps {
  isOpen: boolean;
  onClose: () => void;
  initialCategory?: NewsCategory;
}

const CATEGORIES: { id: NewsCategory; label: string; icon: string }[] = [
  { id: "all", label: "All Markets", icon: "🌐" },
  { id: "macro", label: "Macro & Fed", icon: "🏛️" },
  { id: "crypto", label: "Crypto & Web3", icon: "⚡" },
  { id: "equities", label: "Equities & Wall St", icon: "📈" },
  { id: "india", label: "India & NSE", icon: "🇮🇳" },
];

export function LiveNewsModal({ isOpen, onClose, initialCategory = "all" }: LiveNewsModalProps) {
  const [category, setCategory] = useState<NewsCategory>(initialCategory);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedSentiment, setSelectedSentiment] = useState<string>("all");

  const { data: newsItems, isLoading, isFetching, refetch } = useLiveNews({
    category,
    limit: 50,
  });

  const refreshMutation = useForceRefreshNews();

  const handleRefresh = async () => {
    await refreshMutation.mutateAsync();
    refetch();
  };

  const filteredItems = useMemo(() => {
    if (!newsItems) return [];
    return newsItems.filter((item) => {
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
  }, [newsItems, searchTerm, selectedSentiment]);

  // Sentiment counts
  const sentimentStats = useMemo(() => {
    if (!newsItems || newsItems.length === 0) return { bullish: 0, bearish: 0, neutral: 0 };
    let b = 0, br = 0, n = 0;
    for (const item of newsItems) {
      if (item.sentiment === "bullish") b++;
      else if (item.sentiment === "bearish") br++;
      else n++;
    }
    return { bullish: b, bearish: br, neutral: n };
  }, [newsItems]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/75 p-4 backdrop-blur-sm anim-fadeIn">
      <div className="flex h-[88vh] w-full max-w-5xl flex-col rounded-2xl border border-(--color-edge) bg-(--color-surface) shadow-2xl overflow-hidden anim-scaleIn">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-(--color-edge) px-6 py-4 bg-(--color-elev)/40">
          <div className="flex items-center gap-3">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-blue-500/10 text-blue-400 border border-blue-500/20">
              <Globe size={20} />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <h2 className="text-lg font-bold tracking-tight text-(--color-ink)">
                  Live Financial News Wire
                </h2>
                <span className="flex items-center gap-1 rounded bg-red-500/15 px-2 py-0.5 text-[10px] font-bold text-red-400 border border-red-500/30">
                  <span className="h-1.5 w-1.5 rounded-full bg-red-500 animate-ping" />
                  REAL-TIME LIVE
                </span>
                <span className="hidden sm:flex items-center gap-1 text-[11px] text-emerald-400">
                  <ShieldCheck size={13} />
                  100% Authentic Wire (Zero Synthetic)
                </span>
              </div>
              <p className="text-xs text-(--color-muted) mt-0.5">
                Real-time institutional news scraped from Bloomberg, Reuters, CNBC, AP, CoinDesk, and MarketWatch.
              </p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <button
              onClick={handleRefresh}
              disabled={isFetching || refreshMutation.isPending}
              className="flex items-center gap-1.5 rounded-lg border border-(--color-edge) bg-(--color-elev) px-3 py-1.5 text-xs font-medium text-(--color-muted) hover:text-(--color-ink) hover:border-blue-500/30 transition-all disabled:opacity-50"
              title="Force refresh live feeds"
            >
              <RefreshCw
                size={13}
                className={isFetching || refreshMutation.isPending ? "animate-spin text-blue-400" : ""}
              />
              <span className="hidden sm:inline">Refresh Wire</span>
            </button>

            <Link
              href="/news"
              onClick={onClose}
              className="flex items-center gap-1 rounded-lg bg-blue-600/15 border border-blue-500/30 px-3 py-1.5 text-xs font-medium text-blue-400 hover:bg-blue-600/25 transition-colors"
            >
              Full Page <ArrowUpRight size={13} />
            </Link>

            <button
              onClick={onClose}
              className="rounded-lg p-1.5 text-(--color-muted) hover:text-(--color-ink) hover:bg-white/5 transition-colors"
            >
              <X size={18} />
            </button>
          </div>
        </div>

        {/* Toolbar: Category tabs, Search, Sentiment filters */}
        <div className="flex flex-wrap items-center justify-between gap-3 border-b border-(--color-edge) px-6 py-3 bg-(--color-elev)/20">
          {/* Category Tabs */}
          <div className="flex flex-wrap items-center gap-1.5">
            {CATEGORIES.map((cat) => (
              <button
                key={cat.id}
                onClick={() => setCategory(cat.id)}
                className={`flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-xs font-medium transition-all ${
                  category === cat.id
                    ? "bg-blue-600 text-white shadow-sm"
                    : "text-(--color-muted) hover:bg-(--color-elev) hover:text-(--color-ink)"
                }`}
              >
                <span>{cat.icon}</span>
                <span>{cat.label}</span>
              </button>
            ))}
          </div>

          {/* Search and Sentiment Pill filters */}
          <div className="flex items-center gap-2">
            <div className="flex items-center gap-1.5 rounded-lg bg-(--color-elev) px-2.5 py-1 text-xs text-(--color-muted) border border-(--color-edge) focus-within:border-blue-500/50 w-48 sm:w-60">
              <Search size={13} className="shrink-0" />
              <input
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                placeholder="Filter by keyword or $ticker…"
                className="w-full bg-transparent outline-none placeholder:text-(--color-muted) text-xs"
              />
              {searchTerm && (
                <button onClick={() => setSearchTerm("")} className="text-zinc-500 hover:text-white">
                  <X size={12} />
                </button>
              )}
            </div>

            <div className="hidden md:flex items-center gap-1 text-xs border border-(--color-edge) rounded-lg p-0.5 bg-(--color-elev)">
              <button
                onClick={() => setSelectedSentiment("all")}
                className={`px-2 py-0.5 rounded text-[11px] font-medium transition-colors ${
                  selectedSentiment === "all" ? "bg-(--color-surface) text-(--color-ink) shadow-sm" : "text-(--color-muted)"
                }`}
              >
                All
              </button>
              <button
                onClick={() => setSelectedSentiment("bullish")}
                className={`px-2 py-0.5 rounded text-[11px] font-medium transition-colors flex items-center gap-1 ${
                  selectedSentiment === "bullish" ? "bg-emerald-500/20 text-emerald-400 font-semibold shadow-sm" : "text-(--color-muted)"
                }`}
              >
                <TrendingUp size={11} /> {sentimentStats.bullish}
              </button>
              <button
                onClick={() => setSelectedSentiment("bearish")}
                className={`px-2 py-0.5 rounded text-[11px] font-medium transition-colors flex items-center gap-1 ${
                  selectedSentiment === "bearish" ? "bg-rose-500/20 text-rose-400 font-semibold shadow-sm" : "text-(--color-muted)"
                }`}
              >
                <TrendingDown size={11} /> {sentimentStats.bearish}
              </button>
            </div>
          </div>
        </div>

        {/* News Feed Stream */}
        <div className="flex-1 overflow-y-auto p-6 space-y-3">
          {isLoading && !newsItems && (
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <Radio size={32} className="text-blue-400 animate-spin mb-3" />
              <div className="text-sm font-semibold text-(--color-ink)">Connecting to live financial news feeds…</div>
              <p className="text-xs text-(--color-muted) mt-1">
                Scraping genuine global wire stories and computing algorithmic sentiment.
              </p>
            </div>
          )}

          {!isLoading && filteredItems.length === 0 && (
            <div className="flex flex-col items-center justify-center py-20 text-center">
              <Filter size={32} className="text-(--color-muted) mb-3" />
              <div className="text-sm font-semibold text-(--color-ink)">No matching headlines found</div>
              <p className="text-xs text-(--color-muted) mt-1">
                Try searching for a different keyword, ticker, or clearing filters.
              </p>
            </div>
          )}

          {filteredItems.map((item) => (
            <div
              key={item.id}
              className="group flex flex-col sm:flex-row sm:items-start justify-between gap-3 rounded-xl border border-(--color-edge) bg-(--color-elev)/40 p-4 transition-all duration-300 hover:border-blue-500/40 hover:bg-(--color-elev) hover:shadow-md"
            >
              <div className="space-y-1.5 flex-1 min-w-0">
                {/* Meta bar: Source, Time, Symbols, Sentiment */}
                <div className="flex flex-wrap items-center gap-2 text-xs">
                  <span className="rounded bg-blue-500/10 px-2 py-0.5 font-semibold text-blue-400 border border-blue-500/20 text-[11px]">
                    {item.source}
                  </span>

                  <span className="text-[11px] text-(--color-muted)">
                    {item.time_ago}
                  </span>

                  {/* Sentiment Pill */}
                  {item.sentiment === "bullish" && (
                    <span className="flex items-center gap-1 rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
                      <TrendingUp size={10} className="stroke-[2.5]" /> Bullish
                    </span>
                  )}
                  {item.sentiment === "bearish" && (
                    <span className="flex items-center gap-1 rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase bg-rose-500/15 text-rose-400 border border-rose-500/30">
                      <TrendingDown size={10} className="stroke-[2.5]" /> Bearish
                    </span>
                  )}
                  {item.sentiment === "neutral" && (
                    <span className="flex items-center gap-1 rounded px-1.5 py-0.5 text-[10px] font-medium uppercase bg-zinc-500/15 text-zinc-400 border border-zinc-500/30">
                      <Minus size={10} /> Neutral
                    </span>
                  )}

                  {/* Tickers */}
                  {item.symbols && item.symbols.map((sym) => (
                    <span
                      key={sym}
                      className="rounded bg-(--color-elev) px-1.5 py-0.5 text-[10px] font-mono font-medium text-blue-600 dark:text-blue-300 border border-(--color-edge)"
                    >
                      ${sym}
                    </span>
                  ))}
                </div>

                {/* Headline */}
                <h3 className="text-sm font-semibold tracking-tight text-(--color-ink) group-hover:text-blue-400 transition-colors leading-snug">
                  <a
                    href={item.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="hover:underline flex items-start gap-1"
                  >
                    <span>{item.title}</span>
                  </a>
                </h3>

                {/* Summary */}
                {item.summary && item.summary !== item.title && (
                  <p className="text-xs text-(--color-muted) line-clamp-2 leading-relaxed">
                    {item.summary}
                  </p>
                )}
              </div>

              {/* Action button */}
              <div className="flex sm:flex-col items-center justify-end sm:items-end shrink-0 gap-2 mt-2 sm:mt-0">
                <a
                  href={item.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1.5 rounded-lg bg-white/5 px-3 py-1.5 text-xs font-medium text-(--color-muted) hover:text-white hover:bg-blue-600 transition-all shadow-sm"
                >
                  <span>Read Wire</span>
                  <ExternalLink size={12} />
                </a>
              </div>
            </div>
          ))}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-between border-t border-(--color-edge) px-6 py-3 bg-(--color-elev)/30 text-xs text-(--color-muted)">
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-emerald-500 inline-block" />
            <span>Showing {filteredItems.length} live verified articles</span>
          </div>
          <div className="flex items-center gap-3">
            <span>Auto-refreshing every 60s</span>
            <button
              onClick={onClose}
              className="px-3 py-1 rounded bg-(--color-elev) text-(--color-ink) hover:bg-white/10 transition-colors"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
