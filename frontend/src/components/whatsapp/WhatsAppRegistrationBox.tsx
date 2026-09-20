"use client";

import { useState, useEffect } from "react";
import { 
  MessageSquare, 
  Send, 
  CheckCircle, 
  Clock, 
  TrendingUp, 
  TrendingDown, 
  Minus, 
  ExternalLink, 
  ChevronDown, 
  ChevronUp, 
  Radio, 
  Smartphone,
  AlertCircle,
  Copy,
  Check
} from "lucide-react";
import { endpoints } from "@/api/endpoints";
import { apiClient } from "@/api/client";
import type { WhatsAppPreviewData, WhatsAppSubscribeResponse, WhatsAppAsset, WhatsAppNewsItem } from "@/types/whatsapp";

interface WhatsAppRegistrationBoxProps {
  className?: string;
  defaultExpanded?: boolean;
}

const COUNTRY_CODES = [
  { code: "+91", country: "India", flag: "🇮🇳" },
  { code: "+1", country: "USA / Canada", flag: "🇺🇸" },
  { code: "+44", country: "United Kingdom", flag: "🇬🇧" },
  { code: "+971", country: "UAE", flag: "🇦🇪" },
  { code: "+65", country: "Singapore", flag: "🇸🇬" },
  { code: "+61", country: "Australia", flag: "🇦🇺" },
  { code: "+49", country: "Germany", flag: "🇩🇪" },
  { code: "+81", country: "Japan", flag: "🇯🇵" },
];

export function WhatsAppRegistrationBox({ className = "", defaultExpanded = false }: WhatsAppRegistrationBoxProps) {
  const [countryCode, setCountryCode] = useState("+91");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [traderName, setTraderName] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [subscribeSuccess, setSubscribeSuccess] = useState<WhatsAppSubscribeResponse | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Preview & Live Data State
  const [previewData, setPreviewData] = useState<WhatsAppPreviewData | null>(null);
  const [isLoadingPreview, setIsLoadingPreview] = useState(false);
  const [showFullPreview, setShowFullPreview] = useState(defaultExpanded);
  const [copied, setCopied] = useState(false);
  const [subscriberCount, setSubscriberCount] = useState<number | null>(null);

  // Fetch initial preview and subscriber count on mount
  useEffect(() => {
    let isMounted = true;
    async function loadInitialData() {
      try {
        setIsLoadingPreview(true);
        const [prevRes, subRes] = await Promise.allSettled([
          apiClient<WhatsAppPreviewData>(endpoints.whatsapp.preview()),
          apiClient<{ total_subscribers: number }>(endpoints.whatsapp.subscribers()),
        ]);

        if (isMounted) {
          if (prevRes.status === "fulfilled" && prevRes.value.data) {
            setPreviewData(prevRes.value.data);
          }
          if (subRes.status === "fulfilled" && subRes.value.data) {
            setSubscriberCount(subRes.value.data.total_subscribers);
          }
        }
      } catch (err) {
        console.error("Failed to load WhatsApp preview:", err);
      } finally {
        if (isMounted) setIsLoadingPreview(false);
      }
    }
    loadInitialData();
    return () => {
      isMounted = false;
    };
  }, []);

  const handleSubscribe = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!phoneNumber.trim()) {
      setErrorMessage("Please enter your mobile phone number.");
      return;
    }

    setErrorMessage(null);
    setIsSubmitting(true);

    try {
      const resp = await apiClient<WhatsAppSubscribeResponse>(
        endpoints.whatsapp.subscribe(),
        {
          method: "POST",
          body: JSON.stringify({
            phone_number: phoneNumber.trim(),
            name: traderName.trim() || "Trader",
            country_code: countryCode,
            notify_time: "07:00",
          }),
        }
      );

      if (resp.data) {
        setSubscribeSuccess(resp.data);
        if (subscriberCount !== null) {
          setSubscriberCount(subscriberCount + 1);
        }
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to register phone number. Please verify format.";
      setErrorMessage(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleSendInstantTest = async () => {
    if (!phoneNumber.trim()) {
      setErrorMessage("Enter your phone number above first to trigger your test briefing.");
      return;
    }

    setErrorMessage(null);
    setIsSubmitting(true);

    try {
      const resp = await apiClient<{ 
        success: boolean; 
        dispatch_urls: { web_url: string; wa_me_url: string }; 
        message: string;
      }>(
        endpoints.whatsapp.sendTest(),
        {
          method: "POST",
          body: JSON.stringify({
            phone_number: phoneNumber.trim(),
            name: traderName.trim() || "Trader",
          }),
        }
      );

      if (resp.data && resp.data.dispatch_urls) {
        // Open WhatsApp Web/Mobile directly with compiled message!
        window.open(resp.data.dispatch_urls.web_url, "_blank", "noopener,noreferrer");
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to dispatch instant test.";
      setErrorMessage(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCopyMessage = () => {
    if (previewData?.message_text) {
      navigator.clipboard.writeText(previewData.message_text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  return (
    <div className={`relative overflow-hidden rounded-xl border border-emerald-500/30 bg-gradient-to-br from-emerald-50/70 via-white to-emerald-50/40 dark:from-emerald-950/20 dark:via-neutral-900/60 dark:to-black/80 backdrop-blur-md p-5 shadow-sm dark:shadow-2xl transition-all duration-300 ${className}`}>
      {/* Background ambient glow */}
      <div className="absolute -top-24 -right-24 w-60 h-60 bg-emerald-500/10 rounded-full blur-3xl pointer-events-none" />
      <div className="absolute -bottom-24 -left-24 w-60 h-60 bg-teal-500/10 rounded-full blur-3xl pointer-events-none" />

      {/* Header bar */}
      <div className="relative z-10 flex flex-col md:flex-row md:items-center md:justify-between gap-3 border-b border-emerald-500/20 pb-4">
        <div className="flex items-center gap-3">
          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-emerald-500/15 dark:bg-emerald-500/20 border border-emerald-500/30 dark:border-emerald-500/40 text-emerald-600 dark:text-emerald-400 shadow-inner shadow-emerald-500/10">
            <MessageSquare className="h-6 w-6" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h3 className="text-base font-bold text-neutral-900 dark:text-white tracking-tight">WhatsApp Morning Market Intelligence</h3>
              <span className="inline-flex items-center gap-1 rounded-full bg-emerald-500/10 dark:bg-emerald-500/15 border border-emerald-500/20 dark:border-emerald-500/30 px-2 py-0.5 text-[11px] font-semibold text-emerald-700 dark:text-emerald-400">
                <Clock className="h-3 w-3" /> 07:00 AM Daily
              </span>
            </div>
            <p className="text-xs text-neutral-600 dark:text-neutral-400 mt-0.5">
              Live prices of Gold, S&P 500, NIFTY 50, Bitcoin, trend signals (Bullish/Bearish/Neutral) & top 5 financial trading headlines.
            </p>
          </div>
        </div>

        {subscriberCount !== null && (
          <div className="flex items-center gap-2 self-start md:self-auto bg-white dark:bg-neutral-900/80 border border-neutral-200 dark:border-neutral-800 rounded-lg px-3 py-1 text-xs text-neutral-700 dark:text-neutral-300 shadow-xs">
            <Radio className="h-3 w-3 text-emerald-500 dark:text-emerald-400 animate-pulse" />
            <span><strong className="text-emerald-600 dark:text-emerald-400">{subscriberCount}</strong> Traders Subscribed</span>
          </div>
        )}
      </div>

      {/* Main Registration Form */}
      <div className="relative z-10 mt-4 grid grid-cols-1 lg:grid-cols-12 gap-5 items-start">
        {/* Left: Input Form */}
        <div className="lg:col-span-6 space-y-4">
          <form onSubmit={handleSubscribe} className="space-y-3">
            <div>
              <label className="block text-xs font-semibold text-neutral-800 dark:text-neutral-300 mb-1.5 flex items-center justify-between">
                <span>Your WhatsApp Phone Number</span>
                <span className="text-[11px] text-neutral-500 dark:text-neutral-400 font-normal">Direct encrypted briefing</span>
              </label>
              <div className="flex gap-2">
                {/* Country Code Select */}
                <select
                  value={countryCode}
                  onChange={(e) => setCountryCode(e.target.value)}
                  className="rounded-lg border border-neutral-300 dark:border-neutral-700/80 bg-white dark:bg-neutral-900/90 px-2.5 py-2 text-xs font-medium text-neutral-900 dark:text-white focus:border-emerald-500 focus:outline-none transition-colors shadow-xs"
                >
                  {COUNTRY_CODES.map((c) => (
                    <option key={c.code} value={c.code} className="bg-white dark:bg-neutral-900 text-neutral-900 dark:text-white">
                      {c.flag} {c.code}
                    </option>
                  ))}
                </select>

                {/* Phone Input */}
                <div className="relative flex-1">
                  <input
                    type="tel"
                    value={phoneNumber}
                    onChange={(e) => {
                      setPhoneNumber(e.target.value);
                      if (errorMessage) setErrorMessage(null);
                    }}
                    placeholder="Enter phone (e.g. 9876543210)"
                    className="w-full rounded-lg border border-neutral-300 dark:border-neutral-700/80 bg-white dark:bg-neutral-900/90 px-3.5 py-2 text-xs text-neutral-900 dark:text-white placeholder-neutral-400 dark:placeholder-neutral-500 focus:border-emerald-500 focus:outline-none transition-colors shadow-inner"
                  />
                  <Smartphone className="absolute right-3 top-2.5 h-4 w-4 text-neutral-400 dark:text-neutral-500" />
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <div>
                <label className="block text-[11px] font-medium text-neutral-600 dark:text-neutral-400 mb-1">
                  Name / Desk (Optional)
                </label>
                <input
                  type="text"
                  value={traderName}
                  onChange={(e) => setTraderName(e.target.value)}
                  placeholder="e.g. Quantitative Desk"
                  className="w-full rounded-lg border border-neutral-300 dark:border-neutral-700/80 bg-white dark:bg-neutral-900/90 px-3 py-1.5 text-xs text-neutral-900 dark:text-white placeholder-neutral-400 dark:placeholder-neutral-500 focus:border-emerald-500 focus:outline-none transition-colors shadow-xs"
                />
              </div>

              <div>
                <label className="block text-[11px] font-medium text-neutral-600 dark:text-neutral-400 mb-1">
                  Schedule Time
                </label>
                <div className="flex items-center gap-1.5 rounded-lg border border-emerald-200 dark:border-neutral-800 bg-emerald-50/80 dark:bg-neutral-950/60 px-3 py-1.5 text-xs text-emerald-700 dark:text-emerald-400 font-mono shadow-xs">
                  <Clock className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
                  <span>07:00 AM IST</span>
                </div>
              </div>
            </div>

            {/* Error banner */}
            {errorMessage && (
              <div className="flex items-center gap-2 rounded-lg bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-500/30 p-2.5 text-xs text-red-700 dark:text-red-300">
                <AlertCircle className="h-4 w-4 shrink-0 text-red-500 dark:text-red-400" />
                <span>{errorMessage}</span>
              </div>
            )}

            {/* Success banner */}
            {subscribeSuccess && (
              <div className="rounded-lg bg-emerald-50 dark:bg-emerald-950/40 border border-emerald-200 dark:border-emerald-500/40 p-3 space-y-2 text-xs text-emerald-900 dark:text-emerald-200 animate-fadeIn shadow-xs">
                <div className="flex items-center gap-2 font-semibold text-emerald-700 dark:text-emerald-300">
                  <CheckCircle className="h-4 w-4 text-emerald-600 dark:text-emerald-400" />
                  <span>{subscribeSuccess.message}</span>
                </div>
                <p className="text-[11px] text-neutral-600 dark:text-neutral-300">
                  You are scheduled for daily updates. You can also trigger an instant dispatch to WhatsApp right now:
                </p>
                <div className="flex items-center gap-2 pt-1">
                  <a
                    href={subscribeSuccess.dispatch_urls.web_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-flex items-center gap-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 px-3 py-1.5 text-xs font-semibold text-white transition-all shadow-md hover:shadow-emerald-600/30"
                  >
                    <Send className="h-3.5 w-3.5" />
                    Open in WhatsApp Now
                    <ExternalLink className="h-3 w-3" />
                  </a>
                </div>
              </div>
            )}

            {/* Action Buttons */}
            <div className="flex flex-wrap items-center gap-2.5 pt-1">
              <button
                type="submit"
                disabled={isSubmitting}
                className="flex-1 inline-flex items-center justify-center gap-2 rounded-lg bg-emerald-600 hover:bg-emerald-500 active:scale-[0.98] disabled:opacity-50 px-4 py-2 text-xs font-bold text-white transition-all shadow-md shadow-emerald-600/20 cursor-pointer"
              >
                {isSubmitting ? (
                  <div className="h-4 w-4 rounded-full border-2 border-white/30 border-t-white animate-spin" />
                ) : (
                  <CheckCircle className="h-4 w-4" />
                )}
                <span>Register for 7:00 AM Updates</span>
              </button>

              <button
                type="button"
                onClick={handleSendInstantTest}
                disabled={isSubmitting}
                className="inline-flex items-center justify-center gap-1.5 rounded-lg border border-emerald-600/30 dark:border-emerald-500/40 bg-emerald-50 hover:bg-emerald-100 dark:bg-emerald-950/30 dark:hover:bg-emerald-900/40 active:scale-[0.98] px-3.5 py-2 text-xs font-semibold text-emerald-800 dark:text-emerald-300 transition-colors shadow-xs cursor-pointer"
                title="Send the live briefing directly to WhatsApp now"
              >
                <Send className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400" />
                <span>Send Instant Test</span>
              </button>
            </div>
          </form>

          {/* Quick specs pill */}
          <div className="flex items-center justify-between text-[11px] text-neutral-500 dark:text-neutral-400 border-t border-neutral-200 dark:border-neutral-800/80 pt-2.5">
            <span>✓ Zero spam guarantee</span>
            <span>✓ Verified real-time prices</span>
            <span>✓ Reply STOP anytime</span>
          </div>
        </div>

        {/* Right: Live Benchmark Asset Cards & Briefing Preview */}
        <div className="lg:col-span-6 space-y-3">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold text-neutral-800 dark:text-neutral-300 flex items-center gap-1.5">
              <Radio className="h-3 w-3 text-emerald-600 dark:text-emerald-400" />
              Live 7:00 AM Assets Included
            </span>
            <button
              type="button"
              onClick={() => setShowFullPreview(!showFullPreview)}
              className="text-xs text-emerald-700 dark:text-emerald-400 hover:text-emerald-800 dark:hover:text-emerald-300 flex items-center gap-1 font-medium transition-colors cursor-pointer"
            >
              {showFullPreview ? "Hide WhatsApp Mockup" : "Preview WhatsApp Message"}
              {showFullPreview ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
            </button>
          </div>

          {/* 4 Benchmark Asset Cards Grid (Gold, S&P 500, NIFTY 50, Bitcoin) */}
          <div className="grid grid-cols-2 gap-2">
            {previewData?.briefing.assets.map((asset: WhatsAppAsset) => {
              const isBull = asset.trend.toLowerCase() === "bullish";
              const isBear = asset.trend.toLowerCase() === "bearish";

              return (
                <div 
                  key={asset.symbol}
                  className="rounded-lg border border-neutral-200 dark:border-neutral-800 bg-white/90 dark:bg-neutral-950/50 p-2.5 transition-colors hover:border-emerald-500/40 shadow-xs dark:shadow-none"
                >
                  <div className="flex items-center justify-between mb-1">
                    <span className="text-xs font-bold text-neutral-900 dark:text-white">{asset.name}</span>
                    <span 
                      className={`inline-flex items-center gap-0.5 rounded px-1.5 py-0.5 text-[10px] font-bold ${
                        isBull
                          ? "bg-emerald-50 text-emerald-700 border border-emerald-200 dark:bg-emerald-500/20 dark:text-emerald-400 dark:border-emerald-500/30"
                          : isBear
                          ? "bg-red-50 text-red-700 border border-red-200 dark:bg-red-500/20 dark:text-red-400 dark:border-red-500/30"
                          : "bg-neutral-100 text-neutral-700 border border-neutral-200 dark:bg-neutral-800 dark:text-neutral-300 dark:border-neutral-700"
                      }`}
                    >
                      {isBull && <TrendingUp className="h-2.5 w-2.5" />}
                      {isBear && <TrendingDown className="h-2.5 w-2.5" />}
                      {!isBull && !isBear && <Minus className="h-2.5 w-2.5" />}
                      {asset.trend}
                    </span>
                  </div>
                  <div className="flex items-baseline justify-between">
                    <span className="text-sm font-bold text-neutral-900 dark:text-white font-mono">{asset.formatted_price}</span>
                    <span className={`text-[11px] font-mono font-medium ${asset.change_pct >= 0 ? "text-emerald-600 dark:text-emerald-400" : "text-red-600 dark:text-red-400"}`}>
                      {asset.formatted_change}
                    </span>
                  </div>
                </div>
              );
            }) || (
              Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="h-16 rounded-lg bg-neutral-200 dark:bg-neutral-800/40 animate-pulse" />
              ))
            )}
          </div>

          {/* Collapsible WhatsApp Preview Mockup */}
          {showFullPreview && previewData && (
            <div className="relative rounded-lg border border-neutral-200 dark:border-neutral-800 bg-neutral-50/90 dark:bg-neutral-950 p-3 shadow-sm dark:shadow-inner">
              <div className="flex items-center justify-between border-b border-neutral-200 dark:border-neutral-800 pb-2 mb-2">
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-emerald-500 dark:bg-emerald-400 animate-ping" />
                  <span className="text-[11px] font-semibold text-neutral-800 dark:text-neutral-300">WhatsApp Message Layout</span>
                </div>
                <button
                  type="button"
                  onClick={handleCopyMessage}
                  className="inline-flex items-center gap-1 rounded bg-white hover:bg-neutral-50 dark:bg-neutral-800 dark:hover:bg-neutral-750 border border-neutral-200 dark:border-neutral-700 px-2 py-1 text-[10px] text-neutral-700 dark:text-neutral-300 shadow-xs transition-colors cursor-pointer"
                >
                  {copied ? <Check className="h-3 w-3 text-emerald-600 dark:text-emerald-400" /> : <Copy className="h-3 w-3" />}
                  {copied ? "Copied" : "Copy Text"}
                </button>
              </div>

              {/* Message bubble preview (Theme-Adaptive WhatsApp Window) */}
              <div className="max-h-48 overflow-y-auto rounded-lg bg-[#efeae2] dark:bg-[#0b141a] p-3 text-[11px] text-[#111b21] dark:text-[#e9edef] font-mono leading-relaxed border border-[#d1d7db] dark:border-[#202c33] select-text shadow-inner">
                <div className="rounded-md bg-white dark:bg-[#1f2c34] p-2.5 shadow-sm border border-neutral-200/60 dark:border-transparent">
                  <pre className="whitespace-pre-wrap font-sans text-neutral-900 dark:text-[#e9edef]">{previewData.message_text}</pre>
                </div>
              </div>

              {/* Live Top 5 Headlines preview */}
              <div className="mt-2.5 pt-2 border-t border-neutral-200 dark:border-neutral-800/80">
                <span className="text-[10px] font-semibold text-neutral-500 dark:text-neutral-400 uppercase tracking-wider block mb-1">
                  Breaking News Feed Included
                </span>
                <ul className="space-y-1 text-[11px] text-neutral-700 dark:text-neutral-300">
                  {previewData.briefing.news.slice(0, 3).map((item: WhatsAppNewsItem) => (
                    <li key={item.rank} className="truncate flex items-center gap-1.5">
                      <span className="text-emerald-600 dark:text-emerald-400 font-bold">{item.rank}.</span>
                      <span className="truncate">{item.title}</span>
                      <span className="text-[10px] text-neutral-400 dark:text-neutral-500 shrink-0">({item.source})</span>
                    </li>
                  ))}
                  {previewData.briefing.news.length > 3 && (
                    <li className="text-[10px] text-neutral-500 dark:text-neutral-400 pl-3">
                      + {previewData.briefing.news.length - 3} more financial wire stories
                    </li>
                  )}
                </ul>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
