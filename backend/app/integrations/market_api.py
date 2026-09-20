"""Single gateway for all external market data. Owned by Satish.

No other domain may import yfinance/requests directly for market data.
"""
from __future__ import annotations

import random
from datetime import UTC, datetime, timedelta

import pandas as pd

from app.core.exceptions import AssetNotFound
from app.core.schemas.market import SUPPORTED_ASSETS, Asset, MarketData


def _synthetic_history(symbol: str, start: str, end: str, provider: str = "mock") -> pd.DataFrame:
    """Deterministic synthetic OHLCV so Samarth/Somesh can develop without live providers."""
    seed = abs(hash(symbol)) % (2**32)
    rng = random.Random(seed)
    start_dt = datetime.fromisoformat(start).replace(tzinfo=UTC)
    end_dt = datetime.fromisoformat(end).replace(tzinfo=UTC)
    days = max((end_dt - start_dt).days, 30)
    price = 100.0 + (seed % 50)
    rows = []
    for i in range(min(days, 756)):
        dt = start_dt + timedelta(days=i)
        drift = rng.uniform(-0.015, 0.017)
        open_p = price
        close_p = max(open_p * (1 + drift), 1.0)
        high_p = max(open_p, close_p) * (1 + rng.uniform(0, 0.008))
        low_p = min(open_p, close_p) * (1 - rng.uniform(0, 0.008))
        rows.append({
            "timestamp": dt, "symbol": symbol, "open": round(open_p, 2),
            "high": round(high_p, 2), "low": round(low_p, 2),
            "close": round(close_p, 2), "adjusted_close": round(close_p, 2),
            "volume": float(1_000_000 + rng.randint(0, 2_000_000)),
            "currency": "INR" if symbol.endswith(".NS") or symbol == "^NSEI" else "USD",
            "exchange": "NSE" if symbol.endswith(".NS") or symbol == "^NSEI" else "MOCK",
            "provider": provider, "interval": "1d",
        })
        price = close_p
    return pd.DataFrame(rows)


def _try_yahoo(symbol: str, start: str, end: str) -> pd.DataFrame | None:
    try:
        import yfinance as yf
    except ImportError:
        return None
    try:
        df = yf.download(symbol, start=start, end=end, progress=False, auto_adjust=False)
        if df is None or df.empty:
            return None
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = [c[0] if isinstance(c, tuple) else c for c in df.columns]
        df = df.reset_index()
        col = {c.lower().replace(" ", "_"): c for c in df.columns}
        out = pd.DataFrame({
            "timestamp": pd.to_datetime(df[col.get("date", "Date")], utc=True),
            "symbol": symbol,
            "open": df[col.get("open", "Open")].astype(float),
            "high": df[col.get("high", "High")].astype(float),
            "low": df[col.get("low", "Low")].astype(float),
            "close": df[col.get("close", "Close")].astype(float),
            "adjusted_close": df[col.get("adj_close", col.get("close", "Close"))].astype(float),
            "volume": df[col.get("volume", "Volume")].astype(float) if "volume" in col else 0.0,
            "currency": "INR" if (symbol.endswith(".NS") or symbol.endswith(".BO") or symbol in ("^NSEI", "^BSESN", "NIFTY", "SENSEX")) else "USD",
            "exchange": "NSE" if (symbol.endswith(".NS") or symbol in ("^NSEI", "NIFTY")) else ("BSE" if (symbol.endswith(".BO") or symbol in ("^BSESN", "SENSEX")) else "YAHOO"),
            "provider": "yahoo",
            "interval": "1d",
        })
        return out.dropna(subset=["close"])
    except (ValueError, KeyError, IndexError, AttributeError):
        return None


class MarketDataClient:
    """Provider abstraction: Yahoo -> synthetic fallback. Binance/NSE/Zerodha/FRED pluggable."""

    def get_supported_assets(self, asset_class: str | None = None, search: str | None = None) -> list[Asset]:
        assets = list(SUPPORTED_ASSETS)
        if asset_class:
            assets = [a for a in assets if a.asset_class == asset_class]
        if search:
            s = search.lower()
            assets = [a for a in assets if s in a.symbol.lower() or s in a.name.lower()]
        return assets

    def validate_symbol(self, symbol: str) -> Asset:
        for a in SUPPORTED_ASSETS:
            if a.symbol == symbol:
                return a
        # Allow ad-hoc symbols via Yahoo convention rather than hard-failing
        return Asset(symbol=symbol, name=symbol, provider="yahoo")

    def get_history(self, symbol: str, start_date: str, end_date: str, interval: str = "1d", provider: str = "auto") -> pd.DataFrame:
        df = None
        if provider in ("auto", "yahoo"):
            df = _try_yahoo(symbol, start_date, end_date)
        if df is None or df.empty:
            df = _synthetic_history(symbol, start_date, end_date, provider="mock" if provider == "auto" else provider)
        if df.empty:
            raise AssetNotFound(symbol)
        return df

    def get_latest_price(self, symbol: str) -> MarketData:
        from datetime import date, timedelta
        today = date.today()
        # Use last 60 days of data to ensure we get the most recent trading day
        end_date = today.isoformat()
        start_date = (today - timedelta(days=60)).isoformat()
        df = self.get_history(symbol, start_date, end_date)
        row = df.iloc[-1]
        return MarketData(**{k: row[k] for k in MarketData.model_fields if k in row})

    def get_quote(self, symbol: str) -> dict:
        md = self.get_latest_price(symbol)
        return {"symbol": symbol, "price": md.close, "currency": md.currency, "timestamp": md.timestamp.isoformat()}

    def get_benchmark_history(self, start_date: str, end_date: str) -> pd.DataFrame:
        return self.get_history("^NSEI", start_date, end_date)


client = MarketDataClient()


# Convenience functions (stable interface for Samarth/Somesh)
def get_history(symbol: str, start_date: str, end_date: str, interval: str = "1d") -> pd.DataFrame:
    return client.get_history(symbol, start_date, end_date, interval)


def get_latest_price(symbol: str) -> MarketData:
    return client.get_latest_price(symbol)


def get_quote(symbol: str) -> dict:
    return client.get_quote(symbol)


def get_supported_assets(asset_class: str | None = None, search: str | None = None) -> list[Asset]:
    return client.get_supported_assets(asset_class, search)


def validate_symbol(symbol: str) -> Asset:
    return client.validate_symbol(symbol)


def get_benchmark_history(start_date: str, end_date: str) -> pd.DataFrame:
    return client.get_benchmark_history(start_date, end_date)
