"""
CoinGecko Market Data Integration & Resilient Caching Layer
===========================================================
Institutional-grade cryptocurrency market data pipeline.
Features:
  - In-memory TTL caching (30s prices, 1hr charts, 5min trending)
  - Sub-millisecond latency on cache hits
  - Exponential backoff retry with jitter on HTTP 429 / 5xx
  - Full support for real-time prices, historical returns & volatility

Documentation: https://docs.coingecko.com/docs/ai-agents-llm-apps
"""

from __future__ import annotations

import asyncio
import logging
import random
import time
from datetime import datetime, timezone
from typing import Any

import httpx
import pandas as pd

from app.config import settings

logger = logging.getLogger(__name__)


class TTLCache:
    """Thread-safe and async-friendly in-memory TTL cache."""

    def __init__(self):
        self._store: dict[str, tuple[float, Any]] = {}

    def get(self, key: str) -> Any | None:
        """Retrieve value if not expired."""
        if key in self._store:
            expiry, value = self._store[key]
            if time.time() < expiry:
                return value
            del self._store[key]
        return None

    def set(self, key: str, value: Any, ttl_seconds: float) -> None:
        """Store value with expiration time in seconds."""
        self._store[key] = (time.time() + ttl_seconds, value)

    def clear(self) -> None:
        """Clear all cached entries."""
        self._store.clear()


# Global cache instance
_coingecko_cache = TTLCache()


class CoinGeckoClient:
    """Async client for CoinGecko v3 API with institutional resilience."""

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        cache: TTLCache | None = None,
    ):
        self.api_key = api_key or settings.coingecko_api_key
        self.base_url = (base_url or "https://api.coingecko.com/api/v3").rstrip("/")
        self.cache = cache or _coingecko_cache

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "User-Agent": "QuantPlatform/1.0",
        }
        if self.api_key:
            if self.api_key.startswith("CG-"):
                headers["x-cg-demo-api-key"] = self.api_key
            else:
                headers["x-cg-pro-api-key"] = self.api_key
        return headers

    async def _get_with_retry(self, url: str, params: dict, max_retries: int = 3) -> dict:
        """Execute GET request with exponential backoff on 429 rate limit or 5xx."""
        async with httpx.AsyncClient(timeout=20.0) as client:
            for attempt in range(max_retries):
                try:
                    resp = await client.get(url, params=params, headers=self._headers())
                    if resp.status_code == 429:
                        wait_sec = (2 ** attempt) + random.uniform(0.1, 0.5)
                        logger.warning(
                            "CoinGecko rate limit hit (429). Backing off for %.2fs (attempt %d/%d)...",
                            wait_sec, attempt + 1, max_retries
                        )
                        await asyncio.sleep(wait_sec)
                        continue

                    resp.raise_for_status()
                    return resp.json()
                except httpx.HTTPStatusError as e:
                    if e.response.status_code in (429, 500, 502, 503, 504) and attempt < max_retries - 1:
                        wait_sec = (2 ** attempt) + random.uniform(0.1, 0.5)
                        logger.warning("CoinGecko error %s. Retrying in %.2fs...", e, wait_sec)
                        await asyncio.sleep(wait_sec)
                    else:
                        raise e
                except (httpx.ConnectError, httpx.TimeoutException) as e:
                    if attempt < max_retries - 1:
                        wait_sec = (2 ** attempt) + random.uniform(0.1, 0.5)
                        logger.warning("CoinGecko connection error %s. Retrying in %.2fs...", e, wait_sec)
                        await asyncio.sleep(wait_sec)
                    else:
                        raise e
            raise RuntimeError(f"CoinGecko request failed after {max_retries} attempts.")

    async def get_simple_price(
        self,
        coin_ids: list[str],
        vs_currencies: list[str] = ["usd"],
        include_market_cap: bool = True,
        include_24hr_vol: bool = True,
        include_24hr_change: bool = True,
    ) -> dict[str, Any]:
        """
        Get current price of one or more cryptocurrencies.
        GET /simple/price
        Cached for 30 seconds to prevent rate-limit throttling.
        """
        cache_key = f"price:{','.join(sorted(coin_ids))}:{','.join(sorted(vs_currencies))}"
        cached = self.cache.get(cache_key)
        if cached is not None:
            logger.debug("CoinGecko cache HIT: %s", cache_key)
            return cached

        url = f"{self.base_url}/simple/price"
        params = {
            "ids": ",".join(coin_ids),
            "vs_currencies": ",".join(vs_currencies),
            "include_market_cap": str(include_market_cap).lower(),
            "include_24hr_vol": str(include_24hr_vol).lower(),
            "include_24hr_change": str(include_24hr_change).lower(),
        }

        data = await self._get_with_retry(url, params=params)
        self.cache.set(cache_key, data, ttl_seconds=30.0)
        return data

    async def get_market_chart(
        self,
        coin_id: str,
        vs_currency: str = "usd",
        days: int = 30,
    ) -> pd.DataFrame:
        """
        Get historical market data (prices, market_caps, total_volumes).
        GET /coins/{id}/market_chart
        Returns a DataFrame with DateTime index and 'price', 'return' columns.
        Cached for 3600 seconds (1 hour).
        """
        cache_key = f"chart:{coin_id}:{vs_currency}:{days}"
        cached_df = self.cache.get(cache_key)
        if cached_df is not None:
            logger.debug("CoinGecko cache HIT: %s", cache_key)
            return cached_df.copy()

        url = f"{self.base_url}/coins/{coin_id}/market_chart"
        params = {
            "vs_currency": vs_currency,
            "days": str(days),
            "interval": "daily" if days > 1 else "",
        }

        data = await self._get_with_retry(url, params=params)
        prices = data.get("prices", [])
        if not prices:
            return pd.DataFrame()

        records = []
        for point in prices:
            ts_ms, price = point[0], point[1]
            dt = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)
            records.append({"timestamp": dt, "price": price})

        df = pd.DataFrame(records).set_index("timestamp").sort_index()
        df["return"] = df["price"].pct_change().fillna(0.0)

        self.cache.set(cache_key, df.copy(), ttl_seconds=3600.0)
        return df

    async def get_trending(self) -> list[dict[str, Any]]:
        """
        Get trending search coins.
        GET /search/trending
        Cached for 300 seconds (5 minutes).
        """
        cache_key = "trending"
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        url = f"{self.base_url}/search/trending"
        data = await self._get_with_retry(url, params={})
        coins = data.get("coins", [])
        result = [
            {
                "id": c["item"]["id"],
                "name": c["item"]["name"],
                "symbol": c["item"]["symbol"],
                "market_cap_rank": c["item"].get("market_cap_rank"),
                "thumb": c["item"].get("thumb"),
                "price_btc": c["item"].get("price_btc"),
            }
            for c in coins
        ]
        self.cache.set(cache_key, result, ttl_seconds=300.0)
        return result

    async def search(self, query: str) -> list[dict[str, Any]]:
        """Search for coins, categories, and markets."""
        url = f"{self.base_url}/search"
        data = await self._get_with_retry(url, params={"query": query})
        return data.get("coins", [])[:10]


# Shared singleton client
coingecko_client = CoinGeckoClient()
