export interface WhatsAppAsset {
  name: string;
  symbol: string;
  display_symbol: string;
  currency: string;
  price: number;
  formatted_price: string;
  change_pct: number;
  formatted_change: string;
  trend: "Bullish" | "Bearish" | "Neutral" | string;
  trend_emoji: string;
}

export interface WhatsAppNewsItem {
  rank: number;
  title: string;
  source: string;
  url: string;
  time_ago: string;
  sentiment: "bullish" | "bearish" | "neutral" | string;
}

export interface WhatsAppBriefing {
  title: string;
  date_str: string;
  time_str: string;
  assets: WhatsAppAsset[];
  news: WhatsAppNewsItem[];
  generated_at: string;
}

export interface WhatsAppPreviewData {
  briefing: WhatsAppBriefing;
  message_text: string;
  sample_dispatch_urls: {
    clean_phone: string;
    web_url: string;
    wa_me_url: string;
  };
  schedule_time: string;
  asset_count: number;
  news_count: number;
}

export interface WhatsAppSubscribeRequest {
  phone_number: string;
  name?: string;
  country_code?: string;
  notify_time?: string;
}

export interface WhatsAppSubscribeResponse {
  message: string;
  subscriber: {
    id: string;
    phone: string;
    clean_phone: string;
    name: string;
    notify_time: string;
    is_active: boolean;
    subscribed_at: string;
    last_sent_at?: string | null;
  };
  dispatch_urls: {
    clean_phone: string;
    web_url: string;
    wa_me_url: string;
  };
  preview_message: string;
}

export interface WhatsAppSubscriberSummary {
  id: string;
  name: string;
  masked_phone: string;
  notify_time: string;
  is_active: boolean;
  subscribed_at: string;
  last_sent_at?: string | null;
}
