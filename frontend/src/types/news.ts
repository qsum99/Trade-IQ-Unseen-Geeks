export type NewsCategory = "all" | "macro" | "crypto" | "equities" | "india";

export type NewsSentiment = "bullish" | "bearish" | "neutral";

export interface FinancialNewsItem {
  id: string;
  title: string;
  summary: string;
  source: string;
  url: string;
  published_at: string;
  time_ago: string;
  category: string;
  symbols: string[];
  sentiment: NewsSentiment;
}

export interface NewsFilters {
  category: NewsCategory;
  symbol?: string;
  search?: string;
}
