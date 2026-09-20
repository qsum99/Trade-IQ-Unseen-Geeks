"""
Unit & Integration Tests — CoinGecko Integration
================================================
Tests live cryptocurrency data fetching from CoinGecko API v3.
"""

import pytest
import pandas as pd

from app.integrations.coingecko import coingecko_client


@pytest.mark.asyncio
async def test_coingecko_simple_price():
    """Test fetching live crypto prices."""
    data = await coingecko_client.get_simple_price(["bitcoin", "ethereum"], vs_currencies=["usd"])
    assert "bitcoin" in data
    assert "usd" in data["bitcoin"]
    assert data["bitcoin"]["usd"] > 0
    assert "ethereum" in data
    assert data["ethereum"]["usd"] > 0


@pytest.mark.asyncio
async def test_coingecko_market_chart():
    """Test fetching historical market data and return series."""
    df = await coingecko_client.get_market_chart("bitcoin", vs_currency="usd", days=7)
    assert isinstance(df, pd.DataFrame)
    assert not df.empty
    assert "price" in df.columns
    assert "return" in df.columns
    assert len(df) >= 5


@pytest.mark.asyncio
async def test_coingecko_trending():
    """Test fetching trending cryptocurrencies."""
    trending = await coingecko_client.get_trending()
    assert isinstance(trending, list)
    assert len(trending) > 0
    assert "name" in trending[0]
    assert "symbol" in trending[0]


@pytest.mark.asyncio
async def test_coingecko_search():
    """Test searching for coins."""
    results = await coingecko_client.search("solana")
    assert isinstance(results, list)
    assert any(c.get("id") == "solana" for c in results)
