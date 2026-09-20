"""
FRED (Federal Reserve Economic Data) API Integration
===================================================
Fetches live macro & commodity indicators: Crude Oil, Brent, 10-Yr Treasury, Fed Funds, CPI.
Documentation: https://fred.stlouisfed.org/docs/api/fred/
"""

from __future__ import annotations

import json
import logging
import os
import urllib.request
from datetime import datetime, timezone
from typing import Any

from app.config import settings

logger = logging.getLogger(__name__)

FRED_SERIES_MAP = {
    "crude": "DCOILWTICO",
    "oil": "DCOILWTICO",
    "wti": "DCOILWTICO",
    "crude_oil": "DCOILWTICO",
    "brent": "DCOILBRENTEU",
    "treasury": "DGS10",
    "treasury_10y": "DGS10",
    "10y": "DGS10",
    "fed_funds": "DFF",
    "interest_rate": "DFF",
    "gas": "GASREGCOVW",
    "gasoline": "GASREGCOVW",
}


class FREDClient:
    """Client for Federal Reserve Economic Data API."""

    def __init__(self, api_key: str | None = None):
        self.api_key = api_key or settings.FRED_API_KEY or os.getenv("FRED_API_KEY")

    def get_commodity_observation(self, name_or_series: str) -> dict[str, Any] | None:
        """Fetch latest observation and 24h/daily change for an economic or commodity series."""
        clean_name = name_or_series.lower().strip().replace(" ", "_")
        series_id = FRED_SERIES_MAP.get(clean_name, name_or_series.upper().strip())

        if not self.api_key:
            logger.warning("FRED_API_KEY not configured.")
            return None

        url = (
            f"https://api.stlouisfed.org/fred/series/observations?"
            f"series_id={series_id}&api_key={self.api_key}&file_type=json&sort_order=desc&limit=5"
        )
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "QuantPlatform/1.0"})
            with urllib.request.urlopen(req, timeout=8) as resp:
                data = json.loads(resp.read().decode())
                raw_obs = data.get("observations", [])
                valid_obs = [o for o in raw_obs if o.get("value") not in (".", None, "")]

                if not valid_obs:
                    return None

                latest_val = float(valid_obs[0]["value"])
                prev_val = float(valid_obs[1]["value"]) if len(valid_obs) > 1 else latest_val
                chg = round(latest_val - prev_val, 2)
                pct = round((chg / prev_val) * 100, 2) if prev_val > 0 else 0.0

                display_title = {
                    "DCOILWTICO": "WTI Crude Oil",
                    "DCOILBRENTEU": "Brent Crude Oil",
                    "DGS10": "10-Year Treasury Yield",
                    "DFF": "Federal Funds Rate",
                    "GASREGCOVW": "US Regular Gasoline",
                }.get(series_id, series_id)

                unit = "%" if series_id in ("DGS10", "DFF") else ("$/bbl" if "COIL" in series_id else "$")

                return {
                    "name": display_title,
                    "series_id": series_id,
                    "price": latest_val,
                    "unit": unit,
                    "currency": "USD",
                    "observation_date": valid_obs[0]["date"],
                    "change_24h": chg,
                    "change_percent_24h": pct,
                    "trend_24h": f"{'Bullish' if pct > 0 else 'Bearish'} ({'+' if pct >= 0 else ''}{pct}%)",
                    "provider": "FRED (Federal Reserve)",
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
        except Exception as e:
            logger.error("FRED API query failed for series %s: %s", series_id, e)
            return None


fred_client = FREDClient()
