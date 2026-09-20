"""
Zerodha / Kite Connect Integration
==================================
Handles Indian equity and index data for NSE / BSE.
Attempts Zerodha Kite Connect API first, with seamless fallback
to Yahoo Finance NSE (.NS) and live exchange data.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Any

import httpx

from app.config import settings

logger = logging.getLogger("quant.integrations.zerodha")

# India Standard Time offset: UTC + 5:30
IST = timezone(timedelta(hours=5, minutes=30))


class ZerodhaClient:
    """Zerodha Kite Connect client with graceful NSE fallback."""

    def __init__(self) -> None:
        self.api_key = settings.zerodha_api_key or os.getenv("ZERODHA_API_KEY")
        self.api_secret = settings.zerodha_api_secret or os.getenv("ZERODHA_API_SECRET")
        self.access_token = os.getenv("ZERODHA_ACCESS_TOKEN")
        self.base_url = "https://api.kite.trade"

    def _get_ist_now(self) -> datetime:
        return datetime.now(IST)

    async def get_nse_quote(self, symbol: str) -> dict[str, Any]:
        """
        Get live NSE/BSE quote.
        1. Attempts Zerodha Kite Connect quote endpoint if access token is available.
        2. Seamlessly falls back to Yahoo Finance (.NS) for live NSE pricing.
        """
        clean_sym = symbol.strip().upper()

        # Handle index aliases
        if clean_sym in ("NIFTY", "NIFTY50", "NIFTY 50", "^NSEI"):
            kite_tradingsymbol = "NIFTY 50"
            kite_exchange = "NSE"
            yf_symbol = "^NSEI"
            display_name = "Nifty 50 Index"
        elif clean_sym in ("SENSEX", "BSE SENSEX", "^BSESN"):
            kite_tradingsymbol = "SENSEX"
            kite_exchange = "BSE"
            yf_symbol = "^BSESN"
            display_name = "BSE Sensex"
        else:
            # Strip exchange suffixes for Kite
            base_sym = clean_sym.replace(".NS", "").replace(".BO", "")
            kite_tradingsymbol = base_sym
            kite_exchange = "BSE" if clean_sym.endswith(".BO") else "NSE"
            yf_symbol = f"{base_sym}.NS" if not clean_sym.endswith((".NS", ".BO")) else clean_sym
            display_name = base_sym

        # Attempt 1: Zerodha Kite Connect API if credentials configured
        if self.api_key and self.access_token:
            try:
                instrument = f"{kite_exchange}:{kite_tradingsymbol}"
                headers = {
                    "X-Kite-Version": "3",
                    "Authorization": f"token {self.api_key}:{self.access_token}",
                }
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.get(
                        f"{self.base_url}/quote",
                        params={"i": instrument},
                        headers=headers,
                    )
                    if resp.status_code == 200:
                        data = resp.json().get("data", {}).get(instrument, {})
                        if data:
                            ohlc = data.get("ohlc", {})
                            last_price = float(data.get("last_price", 0))
                            close_p = float(ohlc.get("close", last_price))
                            open_p = float(ohlc.get("open", last_price))
                            change = round(last_price - close_p, 2)
                            change_pct = round((change / close_p) * 100, 2) if close_p > 0 else 0.0
                            trend = "Bullish" if change_pct > 0.05 else ("Bearish" if change_pct < -0.05 else "Neutral")
                            now_ist = self._get_ist_now()

                            return {
                                "symbol": clean_sym,
                                "name": display_name,
                                "price": last_price,
                                "price_inr": last_price,
                                "open": open_p,
                                "high": float(ohlc.get("high", last_price)),
                                "low": float(ohlc.get("low", last_price)),
                                "volume": float(data.get("volume", 0)),
                                "currency": "INR",
                                "change_24h": change,
                                "change_percent_24h": change_pct,
                                "trend_24h": f"{trend} ({'+' if change_pct >= 0 else ''}{change_pct}%)",
                                "exchange": kite_exchange,
                                "provider": "Zerodha Kite Connect",
                                "timestamp": now_ist.isoformat(),
                                "timestamp_ist": now_ist.strftime("%Y-%m-%d %H:%M:%S IST"),
                            }
            except Exception as e:
                logger.info("Zerodha Kite API call failed (%s), falling back to NSE live gateway", e)

        # Attempt 2: Live Market Gateway (Yahoo Finance NSE / BSE)
        try:
            from app.integrations.market_api import client as market_client
            md = market_client.get_latest_price(yf_symbol)
            open_p = float(md.open) if md.open and md.open > 0 else float(md.close)
            close_p = float(md.close)
            change = round(close_p - open_p, 2)
            change_pct = round((change / open_p) * 100, 2) if open_p > 0 else 0.0
            trend = "Bullish" if change_pct > 0.05 else ("Bearish" if change_pct < -0.05 else "Neutral/Consolidating")
            now_ist = self._get_ist_now()

            return {
                "symbol": clean_sym,
                "name": display_name,
                "price": close_p,
                "price_inr": close_p,
                "open": open_p,
                "high": float(md.high) if md.high else close_p,
                "low": float(md.low) if md.low else open_p,
                "volume": float(md.volume) if md.volume else 0.0,
                "currency": "INR",
                "change_24h": change,
                "change_percent_24h": change_pct,
                "trend_24h": f"{trend} ({'+' if change_pct >= 0 else ''}{change_pct}%)",
                "exchange": "NSE" if (clean_sym.endswith(".NS") or clean_sym.startswith("^NSE") or "NIFTY" in clean_sym) else "BSE",
                "provider": "Zerodha Gateway (NSE Live)",
                "timestamp": now_ist.isoformat(),
                "timestamp_ist": now_ist.strftime("%Y-%m-%d %H:%M:%S IST"),
            }
        except Exception as e:
            logger.error("NSE price lookup failed for %s: %s", clean_sym, e)
            return {"symbol": clean_sym, "error": str(e), "provider": "Zerodha Gateway"}


zerodha_client = ZerodhaClient()
