"use client";

import { useState, useEffect } from "react";
import { 
  Radio, 
  ExternalLink, 
  ChevronLeft, 
  ChevronRight, 
  TrendingUp, 
  TrendingDown, 
  Minus,
  Maximize2,
  Newspaper
} from "lucide-react";
import { useBreakingNews } from "@/hooks/useLiveNews";
import type { FinancialNewsItem } from "@/types/news";

interface LiveNewsTickerProps {
  onOpenTerminal?: () => void;
  className?: string;
}

export function LiveNewsTicker({ onOpenTerminal, className = "" }: LiveNewsTickerProps) {
  const { data: newsItems, isLoading, isError } = useBreakingNews(8);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isPaused, setIsPaused] = useState(false);

  const items: FinancialNewsItem[] = newsItems && newsItems.length > 0 ? newsItems : [];

  // Auto-cycle headlines every 6 seconds if not hovered
  useEffect(() => {
    if (items.length <= 1 || isPaused) return;

    const timer = setInterval(() => {
      setCurrentIndex((prev) => (prev + 1) % items.length);
    }, 6000);

    return () => clearInterval(timer);
  }, [items.length, isPaused]);

  const current = items[currentIndex];

  const handlePrev = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (items.length > 0) {
      setCurrentIndex((prev) => (prev - 1 + items.length) % items.length);
    }
  };

  const handleNext = (e: React.MouseEvent) => {
    e.stopPropagation();
    if (items.length > 0) {
      setCurrentIndex((prev) => (prev + 1) % items.length);
    }
  };

  const getSentimentBadge = (sentiment: string) => {
    if (sentiment === "bullish") {
      return (
        <span className="flex items-center gap-0.5 rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase bg-emerald-500/15 text-emerald-400 border border-emerald-500/30">
          <TrendingUp size={10} className="stroke-[2.5]" /> Bullish
        </span>
      );
    }
    if (sentiment === "bearish") {
      return (
        <span className="flex items-center gap-0.5 rounded px-1.5 py-0.5 text-[10px] font-semibold uppercase bg-rose-500/15 text-rose-400 border border-rose-500/30">
          <TrendingDown size={10} className="stroke-[2.5]" /> Bearish
        </span>
      );
    }
    return (
      <span className="flex items-center gap-0.5 rounded px-1.5 py-0.5 text-[10px] font-medium uppercase bg-zinc-500/15 text-zinc-400 border border-zinc-500/30">
        <Minus size={10} /> Neutral
      </span>
    );
  };

  return (
    <div
      className={`flex items-center gap-2 rounded-lg border border-(--color-edge) bg-(--color-elev) px-2.5 py-1.5 text-xs transition-all duration-300 hover:border-blue-500/40 max-w-xl flex-1 ${className}`}
      onMouseEnter={() => setIsPaused(true)}
      onMouseLeave={() => setIsPaused(false)}
    >
      {/* Live Badge */}
      <div 
        onClick={onOpenTerminal}
        className="flex items-center gap-1.5 rounded bg-red-500/15 px-2 py-0.5 font-bold text-red-400 border border-red-500/30 shrink-0 cursor-pointer select-none hover:bg-red-500/25 transition-colors"
        title="Click to open Live Financial Terminal"
      >
        <span className="relative flex h-2 w-2">
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75"></span>
          <span className="relative inline-flex rounded-full h-2 w-2 bg-red-500"></span>
        </span>
        <span className="tracking-wider uppercase text-[10px]">LIVE WIRE</span>
      </div>

      {/* Content Area */}
      <div className="flex items-center gap-2 min-w-0 flex-1">
        {isLoading && !current && (
          <div className="flex items-center gap-2 text-(--color-muted) animate-pulse truncate text-xs">
            <Radio size={12} className="shrink-0 animate-spin text-blue-400" />
            <span>Connecting to real-time financial wire…</span>
          </div>
        )}

        {isError && (
          <span className="text-amber-400/90 text-xs truncate">
            Wire standby — retrying connection…
          </span>
        )}

        {current && (
          <div 
            onClick={onOpenTerminal}
            className="flex items-center gap-2 min-w-0 flex-1 cursor-pointer group"
          >
            {/* Publisher Source Pill */}
            <span className="shrink-0 rounded bg-blue-500/10 px-1.5 py-0.5 text-[10px] font-semibold text-blue-400 border border-blue-500/20 max-w-[100px] truncate">
              {current.source}
            </span>

            {/* Headline */}
            <span 
              className="truncate text-(--color-ink) group-hover:text-blue-400 transition-colors font-medium text-xs select-none"
              title={current.title}
            >
              {current.title}
            </span>

            {/* Sentiment Pill */}
            <div className="hidden sm:flex shrink-0">
              {getSentimentBadge(current.sentiment)}
            </div>

            {/* Symbols tag if present */}
            {current.symbols && current.symbols.length > 0 && (
              <span className="hidden md:inline-flex shrink-0 rounded bg-(--color-elev) px-1.5 py-0.5 text-[10px] font-mono text-blue-600 dark:text-blue-300 border border-(--color-edge)">
                ${current.symbols[0]}
              </span>
            )}

            {/* Time ago */}
            <span className="hidden lg:inline-block shrink-0 text-[11px] text-(--color-muted) whitespace-nowrap">
              {current.time_ago}
            </span>
          </div>
        )}
      </div>

      {/* Controls & Terminal Action */}
      <div className="flex items-center gap-1 shrink-0 border-l border-(--color-edge) pl-2">
        {items.length > 1 && (
          <>
            <button
              onClick={handlePrev}
              title="Previous headline"
              className="rounded p-0.5 text-(--color-muted) hover:text-(--color-ink) hover:bg-white/5 transition-colors"
            >
              <ChevronLeft size={13} />
            </button>
            <span className="text-[10px] text-(--color-muted) font-mono px-0.5">
              {currentIndex + 1}/{items.length}
            </span>
            <button
              onClick={handleNext}
              title="Next headline"
              className="rounded p-0.5 text-(--color-muted) hover:text-(--color-ink) hover:bg-white/5 transition-colors"
            >
              <ChevronRight size={13} />
            </button>
          </>
        )}

        {/* Read Original Article directly */}
        {current?.url && (
          <a
            href={current.url}
            target="_blank"
            rel="noopener noreferrer"
            title={`Open original wire report on ${current.source}`}
            className="rounded p-1 text-(--color-muted) hover:text-blue-400 hover:bg-blue-500/10 transition-colors ml-0.5"
            onClick={(e) => e.stopPropagation()}
          >
            <ExternalLink size={12} />
          </a>
        )}

        {/* Open Terminal Modal */}
        {onOpenTerminal && (
          <button
            onClick={onOpenTerminal}
            title="Open Live News Terminal & Filters"
            className="rounded p-1 text-(--color-muted) hover:text-emerald-400 hover:bg-emerald-500/10 transition-colors"
          >
            <Maximize2 size={12} />
          </button>
        )}
      </div>
    </div>
  );
}
