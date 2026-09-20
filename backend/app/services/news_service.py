"""Real-Time Live Financial News Scraper & Service.

Scrapes verified live financial news from institutional RSS feeds (Google News Business/Markets)
and Yahoo Finance ticker news. Zero synthetic data — 100% authentic, real-time reporting.
"""
from __future__ import annotations

import datetime
import email.utils
import hashlib
import re
import threading
import time
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional

import yfinance as yf

# In-memory cache (TTL: 60s)
_CACHE: Dict[str, Any] = {}
_CACHE_LOCK = threading.Lock()
CACHE_TTL = 60  # seconds

FEEDS = {
    "all": "https://news.google.com/rss/headlines/section/topic/BUSINESS?hl=en-US&gl=US&ceid=US:en",
    "macro": "https://news.google.com/rss/search?q=federal+reserve+inflation+interest+rates+economy&hl=en-US&gl=US&ceid=US:en",
    "crypto": "https://news.google.com/rss/search?q=bitcoin+crypto+ethereum+solana+cryptocurrency&hl=en-US&gl=US&ceid=US:en",
    "equities": "https://news.google.com/rss/search?q=stock+market+wall+street+earnings+nasdaq+sp500&hl=en-US&gl=US&ceid=US:en",
    "india": "https://news.google.com/rss/search?q=nifty+sensex+nse+india+stock+market&hl=en-IN&gl=IN&ceid=IN:en",
}

BULLISH_KEYWORDS = {
    "surge", "surges", "surging", "rally", "rallies", "gain", "gains", "gaining",
    "bull", "bullish", "high", "record", "profit", "profits", "beat", "beats",
    "soar", "soars", "jump", "jumps", "buy", "upgraded", "upgrade", "positive",
    "breakout", "rebound", "advances", "advance", "growth", "optimism"
}

BEARISH_KEYWORDS = {
    "drop", "drops", "falling", "fall", "falls", "loss", "losses", "plunge",
    "plunges", "slump", "slumps", "bear", "bearish", "crash", "crashes", "down",
    "miss", "misses", "cut", "cuts", "decline", "declines", "fear", "warning",
    "slide", "slides", "inflation", "selloff", "recession", "slashed", "downgrade"
}

SYMBOL_PATTERNS = [
    (r"\b(BTC|BITCOIN)\b", "BTC"),
    (r"\b(ETH|ETHEREUM)\b", "ETH"),
    (r"\b(SOL|SOLANA)\b", "SOL"),
    (r"\b(NVDA|NVIDIA)\b", "NVDA"),
    (r"\b(AAPL|APPLE)\b", "AAPL"),
    (r"\b(MSFT|MICROSOFT)\b", "MSFT"),
    (r"\b(TSLA|TESLA)\b", "TSLA"),
    (r"\b(RELIANCE|RIL)\b", "RELIANCE"),
    (r"\b(TCS|TATA CONSULTANCY)\b", "TCS"),
    (r"\b(HDFC)\b", "HDFC"),
    (r"\b(FED|POWELL|FOMC)\b", "FED"),
    (r"\b(S&P 500|SPX|SPY)\b", "SPX"),
    (r"\b(NASDAQ|QQQ)\b", "NDX"),
    (r"\b(NIFTY)\b", "NIFTY"),
    (r"\b(GOLD)\b", "GOLD"),
    (r"\b(CRUDE|OIL)\b", "OIL"),
]


import html


def _clean_html(raw_html: str) -> str:
    """Strip HTML tags, decode HTML entities (&nbsp;, &amp;), and clean whitespace."""
    if not raw_html:
        return ""
    clean = re.sub(r"<.*?>", " ", raw_html)
    clean = html.unescape(clean)
    clean = clean.replace("&nbsp;", " ").replace("\xa0", " ")
    clean = re.sub(r"\s+", " ", clean)
    return clean.strip()


def _format_time_ago(dt: datetime.datetime) -> str:
    """Format human-readable time ago."""
    now = datetime.datetime.now(datetime.timezone.utc)
    diff = now - dt
    secs = int(diff.total_seconds())
    if secs < 60:
        return f"{max(1, secs)}s ago"
    mins = secs // 60
    if mins < 60:
        return f"{mins}m ago"
    hours = mins // 60
    if hours < 24:
        return f"{hours}h ago"
    days = hours // 24
    return f"{days}d ago"


def _analyze_sentiment(text: str) -> str:
    words = re.findall(r"\w+", text.lower())
    bull_count = sum(1 for w in words if w in BULLISH_KEYWORDS)
    bear_count = sum(1 for w in words if w in BEARISH_KEYWORDS)
    if bull_count > bear_count:
        return "bullish"
    elif bear_count > bull_count:
        return "bearish"
    return "neutral"


def _extract_symbols(text: str) -> List[str]:
    found = set()
    for pattern, tag in SYMBOL_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            found.add(tag)
    return sorted(list(found))


def _fetch_rss_feed(url: str, category: str) -> List[Dict[str, Any]]:
    """Fetch and parse live RSS items."""
    items = []
    try:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 TradeIQ/1.0"
                )
            },
        )
        with urllib.request.urlopen(req, timeout=8) as response:
            content = response.read()

        root = ET.fromstring(content)
        for item in root.findall(".//item"):
            title_elem = item.find("title")
            link_elem = item.find("link")
            pub_date_elem = item.find("pubDate")
            source_elem = item.find("source")
            desc_elem = item.find("description")

            if title_elem is None or not title_elem.text:
                continue

            raw_title = title_elem.text.strip()
            link = link_elem.text.strip() if link_elem is not None and link_elem.text else ""
            source_name = source_elem.text.strip() if source_elem is not None and source_elem.text else "Financial Press"

            # Parse publisher name from title if " - Publisher" exists
            title = raw_title
            if " - " in raw_title:
                parts = raw_title.rsplit(" - ", 1)
                title = parts[0].strip()
                if source_name == "Financial Press" and len(parts) > 1:
                    source_name = parts[1].strip()

            pub_dt = None
            if pub_date_elem is not None and pub_date_elem.text:
                try:
                    pub_dt = email.utils.parsedate_to_datetime(pub_date_elem.text)
                except Exception:
                    pub_dt = datetime.datetime.now(datetime.timezone.utc)
            else:
                pub_dt = datetime.datetime.now(datetime.timezone.utc)

            summary = _clean_html(desc_elem.text) if desc_elem is not None and desc_elem.text else ""

            news_id = hashlib.md5((link or title).encode("utf-8")).hexdigest()[:12]
            combined_text = f"{title} {summary}"

            items.append({
                "id": f"news_{news_id}",
                "title": title,
                "summary": summary,
                "source": source_name,
                "url": link,
                "published_at": pub_dt.isoformat(),
                "time_ago": _format_time_ago(pub_dt),
                "category": category,
                "symbols": _extract_symbols(combined_text),
                "sentiment": _analyze_sentiment(combined_text),
            })
    except Exception as exc:
        print(f"[NewsService] Error fetching RSS ({url}): {exc}")

    return items


def _fetch_ticker_news(symbol: str) -> List[Dict[str, Any]]:
    """Fetch live ticker news from Yahoo Finance."""
    items = []
    try:
        ticker = yf.Ticker(symbol)
        raw_news = getattr(ticker, "news", []) or []
        for item in raw_news[:10]:
            content = item.get("content") or item
            title = content.get("title")
            if not title:
                continue

            summary = content.get("summary") or content.get("description") or ""
            provider = content.get("provider") or {}
            source_name = provider.get("displayName") if isinstance(provider, dict) else "Yahoo Finance"

            urls = content.get("clickThroughUrl") or content.get("canonicalUrl") or {}
            url = urls.get("url") if isinstance(urls, dict) else (content.get("link") or "")

            pub_str = content.get("pubDate") or content.get("displayTime")
            if pub_str:
                try:
                    pub_dt = datetime.datetime.fromisoformat(pub_str.replace("Z", "+00:00"))
                except Exception:
                    pub_dt = datetime.datetime.now(datetime.timezone.utc)
            else:
                pub_dt = datetime.datetime.now(datetime.timezone.utc)

            clean_sym = symbol.split(".")[0].split("-")[0].upper()
            combined_text = f"{title} {summary}"

            news_id = content.get("id") or hashlib.md5(title.encode("utf-8")).hexdigest()[:12]

            items.append({
                "id": f"news_{news_id}",
                "title": title,
                "summary": summary,
                "source": source_name or "Yahoo Finance",
                "url": url,
                "published_at": pub_dt.isoformat(),
                "time_ago": _format_time_ago(pub_dt),
                "category": "equities" if "USD" not in symbol else "crypto",
                "symbols": list(set([clean_sym] + _extract_symbols(combined_text))),
                "sentiment": _analyze_sentiment(combined_text),
            })
    except Exception as exc:
        print(f"[NewsService] Error fetching yfinance news for {symbol}: {exc}")

    return items


def get_live_news(category: str = "all", symbol: Optional[str] = None, limit: int = 30) -> List[Dict[str, Any]]:
    """Fetch aggregated, deduped live financial news with 60s cache."""
    cache_key = f"{category}:{symbol or 'none'}"

    with _CACHE_LOCK:
        cached = _CACHE.get(cache_key)
        if cached and (time.time() - cached["ts"]) < CACHE_TTL:
            return cached["data"][:limit]

    articles: List[Dict[str, Any]] = []

    # 1. If symbol specified, fetch ticker news first
    if symbol:
        ticker_items = _fetch_ticker_news(symbol)
        articles.extend(ticker_items)

    # 2. Fetch category RSS feeds
    feed_url = FEEDS.get(category) or FEEDS["all"]
    rss_items = _fetch_rss_feed(feed_url, category)
    articles.extend(rss_items)

    # 3. If 'all', also mix in top crypto and equities
    if category == "all" and not symbol:
        crypto_items = _fetch_rss_feed(FEEDS["crypto"], "crypto")
        india_items = _fetch_rss_feed(FEEDS["india"], "india")
        articles.extend(crypto_items[:10])
        articles.extend(india_items[:8])

    # 4. Deduplicate by title similarity
    seen_titles = set()
    deduped = []
    for a in articles:
        normalized_t = re.sub(r"[^a-zA-Z0-9]", "", a["title"].lower())[:60]
        if normalized_t and normalized_t not in seen_titles:
            seen_titles.add(normalized_t)
            deduped.append(a)

    # Sort descending by published_at
    deduped.sort(key=lambda x: x["published_at"], reverse=True)

    with _CACHE_LOCK:
        _CACHE[cache_key] = {"ts": time.time(), "data": deduped}

    return deduped[:limit]


def get_breaking_news(limit: int = 5) -> List[Dict[str, Any]]:
    """Fetch top breaking news headlines for the top navigation ticker."""
    items = get_live_news(category="all", limit=max(limit, 10))
    return items[:limit]


def clear_cache() -> None:
    """Clear in-memory cache to force live refresh."""
    with _CACHE_LOCK:
        _CACHE.clear()

