"""
AI Tool Definitions
====================
Tools exposed to the LLM for function/tool calling.
The LLM calls these tools → backend computes → LLM explains results.
"""

from __future__ import annotations

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_assets",
            "description": "List all supported assets, optionally filtered by asset class.",
            "parameters": {
                "type": "object",
                "properties": {
                    "asset_class": {
                        "type": "string",
                        "enum": ["equity", "crypto", "commodity", "macro"],
                        "description": "Filter by asset class.",
                    }
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_latest_price",
            "description": "Get real-time / latest price quote and exchange details for an equity, index, or asset symbol (e.g. AAPL, NVDA, RELIANCE.NS, ^NSEI, GC=F).",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Ticker symbol, e.g. NVDA, AAPL, MSFT, RELIANCE.NS, ^NSEI",
                    }
                },
                "required": ["symbol"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_price_history",
            "description": "Get historical OHLCV price data for a symbol.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string", "description": "Asset symbol e.g. NVDA, BTC-USD"},
                    "start_date": {"type": "string", "description": "Start date YYYY-MM-DD"},
                    "end_date": {"type": "string", "description": "End date YYYY-MM-DD"},
                    "interval": {"type": "string", "default": "1d"},
                },
                "required": ["symbol", "start_date", "end_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_indicators",
            "description": "Calculate technical indicators (SMA, EMA, returns, volatility, Sharpe, drawdown) for a symbol.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                    "indicators": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of indicators: sma, ema, returns, volatility, sharpe, drawdown",
                    },
                },
                "required": ["symbol", "start_date", "end_date", "indicators"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_correlation",
            "description": "Calculate correlation matrix between multiple assets.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbols": {"type": "array", "items": {"type": "string"}},
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                },
                "required": ["symbols", "start_date", "end_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_backtest",
            "description": "Run a backtest for a strategy on an asset.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "strategy": {
                        "type": "string",
                        "enum": ["sma_crossover", "ema_trend", "momentum", "mean_reversion", "buy_hold"],
                    },
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                    "initial_capital": {"type": "number", "default": 100000},
                    "transaction_cost": {"type": "number", "default": 0.001},
                    "parameters": {"type": "object", "description": "Strategy-specific parameters"},
                },
                "required": ["symbol", "strategy", "start_date", "end_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_risk",
            "description": "Calculate risk metrics (VaR, CVaR, Sharpe, Sortino, max drawdown, beta) for a symbol.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                    "benchmark": {"type": "string", "default": "^GSPC"},
                },
                "required": ["symbol", "start_date", "end_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_monte_carlo",
            "description": "Run Monte Carlo simulation to estimate risk distribution.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                    "num_simulations": {"type": "integer", "default": 10000},
                    "num_days": {"type": "integer", "default": 252},
                    "initial_value": {"type": "number", "default": 100000},
                },
                "required": ["symbol", "start_date", "end_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "optimize_portfolio",
            "description": "Optimize portfolio weights for given assets.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbols": {"type": "array", "items": {"type": "string"}},
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                    "method": {
                        "type": "string",
                        "enum": ["equal_weight", "inverse_vol", "min_variance", "max_sharpe", "risk_parity"],
                        "default": "max_sharpe",
                    },
                },
                "required": ["symbols", "start_date", "end_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "compare_strategies",
            "description": "Compare multiple strategies on the same asset and date range.",
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {"type": "string"},
                    "strategies": {"type": "array", "items": {"type": "string"}},
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                },
                "required": ["symbol", "strategies", "start_date", "end_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_quantum_experiment",
            "description": "Run a quantum computing experiment (regime detection or portfolio optimization).",
            "parameters": {
                "type": "object",
                "properties": {
                    "experiment_type": {
                        "type": "string",
                        "enum": ["regime_detection", "portfolio_optimization"],
                    },
                    "symbols": {"type": "array", "items": {"type": "string"}},
                    "start_date": {"type": "string"},
                    "end_date": {"type": "string"},
                },
                "required": ["experiment_type", "symbols", "start_date", "end_date"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_crypto_price",
            "description": "Get real-time cryptocurrency price, 24h change, volume, and market cap from CoinGecko.",
            "parameters": {
                "type": "object",
                "properties": {
                    "coin_ids": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "CoinGecko coin IDs e.g. ['bitcoin', 'ethereum', 'solana']",
                    },
                    "vs_currencies": {
                        "type": "array",
                        "items": {"type": "string"},
                        "default": ["usd"],
                        "description": "Target fiat or crypto currencies e.g. ['usd', 'inr']",
                    },
                },
                "required": ["coin_ids"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_crypto_market_chart",
            "description": "Get historical crypto prices and daily returns from CoinGecko for backtesting and risk.",
            "parameters": {
                "type": "object",
                "properties": {
                    "coin_id": {"type": "string", "description": "CoinGecko coin ID e.g. 'bitcoin'"},
                    "days": {"type": "integer", "default": 30, "description": "Number of days of historical data"},
                    "vs_currency": {"type": "string", "default": "usd"},
                },
                "required": ["coin_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_trending_crypto",
            "description": "Get top-7 trending search cryptocurrencies on CoinGecko in the last 24 hours.",
            "parameters": {
                "type": "object",
                "properties": {},
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_commodity_price",
            "description": (
                "Get live commodity or macro indicator data via FRED API. "
                "Use this for: crude oil (WTI/Brent), natural gas, gasoline, gold, silver, "
                "10-year treasury yield, federal funds rate, or any macro indicator. "
                "Examples: crude_oil, brent, treasury_10y, fed_funds, gold, silver."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "commodity": {
                        "type": "string",
                        "description": "Commodity or macro series name e.g. crude_oil, brent, gold, treasury_10y, fed_funds, gasoline",
                    }
                },
                "required": ["commodity"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_nse_price",
            "description": (
                "Get real-time NSE/BSE Indian equity or index price via Zerodha / NSE live market gateway. "
                "Use this for Indian stocks like Reliance, TCS, Infosys, HDFC Bank, or indices "
                "like Nifty 50, Sensex. Symbol examples: RELIANCE.NS, TCS.NS, INFY.NS, ^NSEI, ^BSESN."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "NSE/BSE ticker with .NS or .BO suffix, or index like ^NSEI, ^BSESN",
                    }
                },
                "required": ["symbol"],
            },
        },
    },
]

