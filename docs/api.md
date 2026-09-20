Yes. For this application, I would define the frontend/backend contract as a **versioned REST API**, with FastAPI generating the OpenAPI specification automatically.

The frontend should never talk directly to PostgreSQL, market-data providers, ML models, Qiskit/PennyLane, or the LLM provider. Everything goes through `/api/v1/...`.

Below is the complete API contract I recommend for the hackathon implementation, including request/response structures, parameters, errors, async jobs, authentication, pagination, and frontend integration.

## 1. API architecture

```text
Next.js Frontend
       │
       │ HTTPS / JSON
       ▼
┌──────────────────────────────┐
│ FastAPI REST API             │
│ /api/v1                      │
├──────────────────────────────┤
│ Auth                         │
│ Assets / Market Data         │
│ Quant Analytics              │
│ Correlation                  │
│ Strategies                   │
│ Backtesting                  │
│ Robustness                   │
│ Regimes                      │
│ Risk                         │
│ Portfolio                    │
│ Quantum                      │
│ AI Research                  │
│ Research Experiments         │
│ Jobs                         │
└──────────────┬───────────────┘
               │
               ▼
        Application Services
               │
       ┌───────┼────────┐
       ▼       ▼        ▼
    Quant     ML      Quantum
    Engine   Engine    Engine
       │       │        │
       └───────┼────────┘
               ▼
       PostgreSQL / Parquet
```

### Base URL

Development:

```text
http://localhost:8000/api/v1
```

Production:

```text
https://api.yourdomain.com/api/v1
```

Frontend should receive this through:

```env
NEXT_PUBLIC_API_BASE_URL=https://api.yourdomain.com
```

Do **not** hardcode the API URL inside individual components.

---

# 2. API conventions

## HTTP methods

| Method | Purpose                                    |
| ------ | ------------------------------------------ |
| GET    | Retrieve data                              |
| POST   | Execute calculation/action/create resource |
| PUT    | Replace/update resource                    |
| PATCH  | Partial update                             |
| DELETE | Delete resource                            |

For this application, most quantitative operations should use `POST`, because the frontend will send a calculation configuration.

Example:

```http
POST /api/v1/indicators/sma
```

rather than putting a large configuration into a URL.

---

# 3. Standard response structure

For successful resource/action responses, use:

```json
{
  "success": true,
  "data": {},
  "meta": {},
  "error": null
}
```

Example:

```json
{
  "success": true,
  "data": {
    "symbol": "NVDA",
    "period": 20,
    "values": [
      {
        "date": "2025-01-02",
        "value": 138.42
      }
    ]
  },
  "meta": {
    "request_id": "req_123456"
  },
  "error": null
}
```

For errors:

```json
{
  "success": false,
  "data": null,
  "meta": {
    "request_id": "req_123456"
  },
  "error": {
    "code": "INVALID_PARAMETER",
    "message": "SMA period must be greater than 1",
    "details": {
      "field": "period"
    }
  }
}
```

---

# 4. HTTP status codes

Use standard codes.

| Status | Meaning                         |
| ------ | ------------------------------- |
| 200    | Successful request              |
| 201    | Resource created                |
| 202    | Async job accepted              |
| 204    | Successful request with no body |
| 400    | Invalid request                 |
| 401    | Authentication required         |
| 403    | Permission denied               |
| 404    | Resource not found              |
| 409    | Conflict                        |
| 422    | Validation error                |
| 429    | Rate limit                      |
| 500    | Internal server error           |
| 503    | Service unavailable             |

---

# 5. Authentication APIs

If authentication is included in the hackathon version:

## POST `/auth/register`

### Request

```json
{
  "email": "user@example.com",
  "password": "StrongPassword123",
  "name": "Satish"
}
```

### Response

```json
{
  "success": true,
  "data": {
    "user": {
      "id": "usr_123",
      "email": "user@example.com",
      "name": "Satish"
    },
    "access_token": "jwt-token",
    "token_type": "bearer",
    "expires_in": 3600
  }
}
```

---

## POST `/auth/login`

```json
{
  "email": "user@example.com",
  "password": "StrongPassword123"
}
```

Response:

```json
{
  "success": true,
  "data": {
    "access_token": "jwt-token",
    "token_type": "bearer",
    "expires_in": 3600
  }
}
```

Frontend sends:

```http
Authorization: Bearer <token>
```

---

## GET `/auth/me`

Response:

```json
{
  "success": true,
  "data": {
    "id": "usr_123",
    "email": "user@example.com",
    "name": "Satish",
    "created_at": "2026-09-19T10:00:00Z"
  }
}
```

---

# 6. Health API

## GET `/health`

Used by frontend to determine whether the backend is online.

Response:

```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "version": "1.0.0",
    "environment": "production",
    "services": {
      "database": "healthy",
      "market_data": "healthy",
      "quant_engine": "healthy",
      "ml_engine": "healthy",
      "quantum_engine": "available"
    }
  }
}
```

This can power the top-right:

```text
● API Connected
```

---

# 7. Asset APIs

## GET `/assets`

Returns all supported assets.

### Query parameters

```text
asset_class
provider
search
page
page_size
```

Example:

```http
GET /api/v1/assets?asset_class=crypto
```

Response:

```json
{
  "success": true,
  "data": [
    {
      "symbol": "BTC-USD",
      "name": "Bitcoin",
      "asset_class": "crypto",
      "currency": "USD",
      "exchange": "CRYPTO",
      "provider": "binance",
      "active": true
    },
    {
      "symbol": "NVDA",
      "name": "NVIDIA Corporation",
      "asset_class": "equity",
      "currency": "USD",
      "exchange": "NASDAQ",
      "provider": "yahoo",
      "active": true
    }
  ]
}
```

---

# 8. Historical market data APIs

## GET `/assets/{symbol}/history`

Example:

```http
GET /api/v1/assets/NVDA/history
```

### Query parameters

```text
start_date
end_date
interval
adjusted
provider
```

Example:

```http
GET /api/v1/assets/NVDA/history?start_date=2024-01-01&end_date=2025-01-01&interval=1d
```

### Response

```json
{
  "success": true,
  "data": {
    "symbol": "NVDA",
    "interval": "1d",
    "currency": "USD",
    "data": [
      {
        "timestamp": "2024-01-02T00:00:00Z",
        "open": 48.17,
        "high": 49.29,
        "low": 47.60,
        "close": 48.16,
        "adjusted_close": 48.16,
        "volume": 411254000
      }
    ]
  }
}
```

This endpoint feeds:

* Markets page
* Asset Analysis
* Strategy pages
* Backtesting
* Correlation
* Risk
* Portfolio

---

# 9. Data quality API

## POST `/data/validate`

Request:

```json
{
  "symbol": "NVDA",
  "start_date": "2024-01-01",
  "end_date": "2025-01-01",
  "provider": "yahoo"
}
```

Response:

```json
{
  "success": true,
  "data": {
    "symbol": "NVDA",
    "records": 251,
    "missing_values": 0,
    "duplicate_records": 0,
    "invalid_prices": 0,
    "date_gaps": 0,
    "quality_score": 100
  }
}
```

This is useful for the **data trust** section of the UI.

---

# 10. Quantitative indicator APIs

## SMA

### POST `/indicators/sma`

Request:

```json
{
  "symbol": "NVDA",
  "start_date": "2024-01-01",
  "end_date": "2025-01-01",
  "period": 20
}
```

Response:

```json
{
  "success": true,
  "data": {
    "symbol": "NVDA",
    "indicator": "SMA",
    "period": 20,
    "values": [
      {
        "date": "2024-02-01",
        "value": 55.42
      }
    ]
  }
}
```

---

## EMA

### POST `/indicators/ema`

Request:

```json
{
  "symbol": "NVDA",
  "period": 20,
  "start_date": "2024-01-01",
  "end_date": "2025-01-01"
}
```

Response structure same as SMA.

---

## Returns

### POST `/indicators/returns`

Request:

```json
{
  "symbol": "NVDA",
  "start_date": "2024-01-01",
  "end_date": "2025-01-01",
  "method": "simple"
}
```

Response:

```json
{
  "success": true,
  "data": {
    "symbol": "NVDA",
    "daily_returns": [],
    "cumulative_return": 0.284,
    "annualized_return": 0.291
  }
}
```

---

# 11. Volatility API

## POST `/indicators/volatility`

Request:

```json
{
  "symbol": "NVDA",
  "start_date": "2024-01-01",
  "end_date": "2025-01-01",
  "window": 20,
  "annualization_factor": 252
}
```

Response:

```json
{
  "success": true,
  "data": {
    "symbol": "NVDA",
    "window": 20,
    "annualized_volatility": 0.382,
    "rolling": [
      {
        "date": "2024-02-01",
        "value": 0.341
      }
    ]
  }
}
```

---

# 12. Sharpe API

## POST `/indicators/sharpe`

Request:

```json
{
  "symbol": "NVDA",
  "start_date": "2024-01-01",
  "end_date": "2025-01-01",
  "risk_free_rate": 0.05,
  "annualization_factor": 252
}
```

Response:

```json
{
  "success": true,
  "data": {
    "symbol": "NVDA",
    "sharpe_ratio": 1.42,
    "risk_free_rate": 0.05
  }
}
```

---

# 13. Drawdown API

## POST `/indicators/drawdown`

Request:

```json
{
  "symbol": "NVDA",
  "start_date": "2024-01-01",
  "end_date": "2025-01-01"
}
```

Response:

```json
{
  "success": true,
  "data": {
    "max_drawdown": -0.184,
    "peak_date": "2024-06-20",
    "trough_date": "2024-08-05",
    "recovery_date": "2024-10-15",
    "series": []
  }
}
```

---

# 14. Combined analytics endpoint

Instead of forcing the frontend to make six requests every time an asset page opens, provide:

## POST `/analytics/summary`

Request:

```json
{
  "symbol": "NVDA",
  "start_date": "2024-01-01",
  "end_date": "2025-01-01",
  "indicators": {
    "sma": [20, 50],
    "ema": [20, 50],
    "returns": true,
    "volatility": true,
    "sharpe": true,
    "drawdown": true
  }
}
```

Response:

```json
{
  "success": true,
  "data": {
    "symbol": "NVDA",
    "price": {},
    "sma": {},
    "ema": {},
    "returns": {},
    "volatility": {},
    "sharpe": {},
    "drawdown": {}
  }
}
```

This will significantly simplify the Asset Analysis frontend.

---

# 15. Correlation APIs

## POST `/correlation/matrix`

Request:

```json
{
  "symbols": [
    "BTC-USD",
    "NVDA",
    "GC=F"
  ],
  "start_date": "2024-01-01",
  "end_date": "2025-01-01",
  "method": "pearson"
}
```

Response:

```json
{
  "success": true,
  "data": {
    "method": "pearson",
    "symbols": [
      "BTC-USD",
      "NVDA",
      "GC=F"
    ],
    "matrix": [
      [1.0, 0.62, 0.18],
      [0.62, 1.0, 0.21],
      [0.18, 0.21, 1.0]
    ]
  }
}
```

This directly feeds the correlation heatmap.

---

## POST `/correlation/rolling`

Request:

```json
{
  "symbols": [
    "BTC-USD",
    "NVDA"
  ],
  "window": 30,
  "start_date": "2024-01-01",
  "end_date": "2025-01-01"
}
```

Response:

```json
{
  "success": true,
  "data": {
    "window": 30,
    "series": [
      {
        "date": "2024-03-01",
        "BTC-USD__NVDA": 0.54
      }
    ]
  }
}
```

---

# 16. Strategy APIs

## GET `/strategies`

Response:

```json
{
  "success": true,
  "data": [
    {
      "id": "sma_crossover",
      "name": "SMA Crossover",
      "description": "Generates signals using fast and slow SMA",
      "parameters": [
        {
          "name": "fast_period",
          "type": "integer",
          "default": 20
        },
        {
          "name": "slow_period",
          "type": "integer",
          "default": 50
        }
      ]
    },
    {
      "id": "ema_trend",
      "name": "EMA Trend",
      "parameters": []
    },
    {
      "id": "momentum",
      "name": "Momentum",
      "parameters": []
    },
    {
      "id": "mean_reversion",
      "name": "Mean Reversion",
      "parameters": []
    }
  ]
}
```

This lets the frontend dynamically generate strategy forms.

---

# 17. Strategy signal API

## POST `/strategies/signals`

Request:

```json
{
  "symbol": "NVDA",
  "strategy": "sma_crossover",
  "parameters": {
    "fast_period": 20,
    "slow_period": 50
  },
  "start_date": "2024-01-01",
  "end_date": "2025-01-01"
}
```

Response:

```json
{
  "success": true,
  "data": {
    "strategy": "sma_crossover",
    "signals": [
      {
        "date": "2024-04-12",
        "signal": "BUY",
        "price": 87.32
      },
      {
        "date": "2024-07-19",
        "signal": "SELL",
        "price": 118.45
      }
    ]
  }
}
```

---

# 18. Backtesting APIs

This is the **core API domain** of the application.

## POST `/backtests`

Request:

```json
{
  "name": "NVDA SMA 20/50",
  "symbol": "NVDA",
  "strategy": {
    "type": "sma_crossover",
    "parameters": {
      "fast_period": 20,
      "slow_period": 50
    }
  },
  "period": {
    "start_date": "2023-01-01",
    "end_date": "2025-01-01"
  },
  "capital": {
    "initial": 100000,
    "position_sizing": "full"
  },
  "execution": {
    "transaction_cost": 0.001,
    "slippage": 0.0005,
    "execution_price": "next_open"
  },
  "benchmark": "buy_and_hold"
}
```

### Response

For a short backtest:

```json
{
  "success": true,
  "data": {
    "backtest_id": "bt_123456",
    "status": "completed"
  }
}
```

For a large backtest:

```http
202 Accepted
```

```json
{
  "success": true,
  "data": {
    "backtest_id": "bt_123456",
    "status": "queued",
    "job_id": "job_789"
  }
}
```

---

# 19. Backtest result API

## GET `/backtests/{id}`

Response:

```json
{
  "success": true,
  "data": {
    "id": "bt_123456",
    "status": "completed",
    "strategy": "sma_crossover",
    "symbol": "NVDA",
    "initial_capital": 100000,
    "final_value": 137500,
    "total_return": 0.375,
    "annualized_return": 0.173,
    "sharpe": 1.31,
    "volatility": 0.28,
    "max_drawdown": -0.16,
    "total_trades": 18
  }
}
```

---

# 20. Backtest equity curve

## GET `/backtests/{id}/equity`

Response:

```json
{
  "success": true,
  "data": {
    "series": [
      {
        "date": "2023-01-03",
        "portfolio_value": 100000,
        "benchmark_value": 100000
      },
      {
        "date": "2023-01-04",
        "portfolio_value": 100850,
        "benchmark_value": 100420
      }
    ]
  }
}
```

Frontend uses this for:

**Strategy vs Buy-and-Hold chart.**

---

# 21. Backtest trades

## GET `/backtests/{id}/trades`

Response:

```json
{
  "success": true,
  "data": {
    "trades": [
      {
        "id": 1,
        "date": "2023-02-15",
        "side": "BUY",
        "price": 210.32,
        "quantity": 100,
        "transaction_cost": 21.03
      },
      {
        "id": 2,
        "date": "2023-05-20",
        "side": "SELL",
        "price": 242.10,
        "quantity": 100,
        "transaction_cost": 24.21
      }
    ]
  }
}
```

---

# 22. Backtest metrics

## GET `/backtests/{id}/metrics`

Response:

```json
{
  "success": true,
  "data": {
    "total_return": 0.375,
    "annualized_return": 0.173,
    "volatility": 0.28,
    "sharpe_ratio": 1.31,
    "max_drawdown": -0.16,
    "win_rate": 0.61,
    "profit_factor": 1.74,
    "total_trades": 18,
    "average_trade_return": 0.021
  }
}
```

---

# 23. Benchmark API

## GET `/backtests/{id}/benchmark`

Response:

```json
{
  "success": true,
  "data": {
    "strategy": {
      "return": 0.375,
      "sharpe": 1.31,
      "volatility": 0.28,
      "max_drawdown": -0.16
    },
    "buy_and_hold": {
      "return": 0.31,
      "sharpe": 1.08,
      "volatility": 0.31,
      "max_drawdown": -0.22
    }
  }
}
```

The frontend can present this as a comparison table.

---

# 24. Robustness APIs

## POST `/robustness/parameter-stress`

Request:

```json
{
  "symbol": "NVDA",
  "strategy": "sma_crossover",
  "parameters": {
    "fast_period": [10, 20, 30],
    "slow_period": [40, 50, 60]
  },
  "period": {
    "start_date": "2023-01-01",
    "end_date": "2025-01-01"
  }
}
```

Response:

```json
{
  "success": true,
  "data": {
    "experiment_id": "exp_123",
    "results": [
      {
        "fast_period": 10,
        "slow_period": 40,
        "return": 0.21,
        "sharpe": 1.02,
        "max_drawdown": -0.19
      }
    ]
  }
}
```

This feeds the parameter heatmap.

---

# 25. Transaction cost stress

## POST `/robustness/cost-stress`

Request:

```json
{
  "backtest_id": "bt_123456",
  "transaction_costs": [
    0,
    0.0005,
    0.001,
    0.002,
    0.005
  ]
}
```

Response:

```json
{
  "success": true,
  "data": {
    "results": [
      {
        "transaction_cost": 0.001,
        "return": 0.34,
        "sharpe": 1.21
      }
    ]
  }
}
```

---

# 26. Walk-forward API

## POST `/robustness/walk-forward`

Request:

```json
{
  "symbol": "NVDA",
  "strategy": "sma_crossover",
  "parameters": {
    "fast_period": 20,
    "slow_period": 50
  },
  "training_window": 252,
  "testing_window": 63,
  "step": 63,
  "start_date": "2021-01-01",
  "end_date": "2025-01-01"
}
```

Response:

```json
{
  "success": true,
  "data": {
    "experiment_id": "wf_123",
    "windows": [
      {
        "train_start": "2021-01-01",
        "train_end": "2021-12-31",
        "test_start": "2022-01-01",
        "test_end": "2022-03-31",
        "return": 0.083
      }
    ],
    "aggregate": {
      "return": 0.27,
      "sharpe": 1.12,
      "max_drawdown": -0.18
    }
  }
}
```

---

# 27. Market regime APIs

## POST `/regimes/detect`

Request:

```json
{
  "symbol": "NVDA",
  "start_date": "2020-01-01",
  "end_date": "2025-01-01",
  "model": "kmeans",
  "features": [
    "return",
    "volatility",
    "momentum"
  ],
  "n_regimes": 4
}
```

Response:

```json
{
  "success": true,
  "data": {
    "model": "kmeans",
    "regimes": [
      {
        "id": 0,
        "label": "Bull",
        "description": "Positive return / moderate volatility"
      },
      {
        "id": 1,
        "label": "Bear",
        "description": "Negative return / elevated volatility"
      }
    ],
    "timeline": [
      {
        "date": "2024-01-02",
        "regime_id": 0,
        "regime_label": "Bull"
      }
    ]
  }
}
```

---

# 28. Regime comparison

## POST `/regimes/compare`

Request:

```json
{
  "symbol": "NVDA",
  "models": [
    "kmeans",
    "hmm"
  ],
  "start_date": "2020-01-01",
  "end_date": "2025-01-01"
}
```

Response:

```json
{
  "success": true,
  "data": {
    "models": {
      "kmeans": {},
      "hmm": {}
    },
    "agreement": 0.74
  }
}
```

---

# 29. Regime-adaptive strategy

## POST `/strategies/regime-adaptive`

Request:

```json
{
  "symbol": "NVDA",
  "regime_model": "kmeans",
  "strategies": {
    "bull": "momentum",
    "bear": "mean_reversion",
    "high_volatility": "mean_reversion",
    "low_volatility": "trend"
  },
  "period": {
    "start_date": "2023-01-01",
    "end_date": "2025-01-01"
  }
}
```

Response:

```json
{
  "success": true,
  "data": {
    "strategy_id": "regime_adaptive_123",
    "signals": [],
    "performance": {}
  }
}
```

---

# 30. Risk APIs

## POST `/risk/metrics`

Request:

```json
{
  "portfolio": [
    {
      "symbol": "NVDA",
      "weight": 0.5
    },
    {
      "symbol": "BTC-USD",
      "weight": 0.3
    },
    {
      "symbol": "GC=F",
      "weight": 0.2
    }
  ],
  "start_date": "2024-01-01",
  "end_date": "2025-01-01"
}
```

Response:

```json
{
  "success": true,
  "data": {
    "expected_return": 0.18,
    "volatility": 0.24,
    "sharpe_ratio": 1.15,
    "max_drawdown": -0.21
  }
}
```

---

# 31. VaR API

## POST `/risk/var`

Request:

```json
{
  "portfolio_value": 100000,
  "confidence": 0.95,
  "horizon_days": 1,
  "method": "historical",
  "returns": []
}
```

Response:

```json
{
  "success": true,
  "data": {
    "var": 2450,
    "confidence": 0.95,
    "horizon_days": 1,
    "method": "historical"
  }
}
```

---

# 32. CVaR API

## POST `/risk/cvar`

Same basic request.

Response:

```json
{
  "success": true,
  "data": {
    "cvar": 3810,
    "confidence": 0.95,
    "horizon_days": 1
  }
}
```

---

# 33. Monte Carlo API

## POST `/risk/monte-carlo`

Request:

```json
{
  "portfolio": [
    {
      "symbol": "NVDA",
      "weight": 0.5
    },
    {
      "symbol": "BTC-USD",
      "weight": 0.5
    }
  ],
  "initial_value": 100000,
  "simulations": 10000,
  "horizon_days": 252,
  "model": "geometric_brownian_motion"
}
```

Because this can be computationally expensive, return:

```http
202 Accepted
```

```json
{
  "success": true,
  "data": {
    "job_id": "job_mc_123",
    "status": "queued"
  }
}
```

---

# 34. Portfolio APIs

## POST `/portfolio/create`

Request:

```json
{
  "name": "Multi Asset Portfolio",
  "assets": [
    {
      "symbol": "NVDA",
      "weight": 0.4
    },
    {
      "symbol": "BTC-USD",
      "weight": 0.3
    },
    {
      "symbol": "GC=F",
      "weight": 0.3
    }
  ]
}
```

Response:

```json
{
  "success": true,
  "data": {
    "portfolio_id": "port_123",
    "name": "Multi Asset Portfolio"
  }
}
```

---

# 35. Portfolio analysis

## POST `/portfolio/analyze`

Request:

```json
{
  "assets": [
    {
      "symbol": "NVDA",
      "weight": 0.4
    },
    {
      "symbol": "BTC-USD",
      "weight": 0.3
    },
    {
      "symbol": "GC=F",
      "weight": 0.3
    }
  ],
  "start_date": "2024-01-01",
  "end_date": "2025-01-01"
}
```

Response:

```json
{
  "success": true,
  "data": {
    "return": 0.17,
    "volatility": 0.22,
    "sharpe": 1.18,
    "max_drawdown": -0.19,
    "correlation_matrix": []
  }
}
```

---

# 36. Portfolio optimization

## POST `/portfolio/optimize`

Request:

```json
{
  "assets": [
    "NVDA",
    "BTC-USD",
    "GC=F"
  ],
  "objective": "max_sharpe",
  "constraints": {
    "min_weight": 0,
    "max_weight": 0.7,
    "long_only": true
  },
  "start_date": "2024-01-01",
  "end_date": "2025-01-01"
}
```

Response:

```json
{
  "success": true,
  "data": {
    "method": "classical",
    "weights": {
      "NVDA": 0.42,
      "BTC-USD": 0.31,
      "GC=F": 0.27
    },
    "expected_return": 0.19,
    "expected_volatility": 0.21,
    "expected_sharpe": 1.24
  }
}
```

---

# 37. Quantum APIs

Quantum should be isolated behind its own namespace.

## GET `/quantum/status`

Response:

```json
{
  "success": true,
  "data": {
    "enabled": true,
    "simulator": true,
    "providers": [
      {
        "name": "pennylane",
        "available": true
      },
      {
        "name": "qiskit",
        "available": true
      }
    ]
  }
}
```

---

# 38. Quantum regime experiment

## POST `/quantum/regime`

Request:

```json
{
  "symbol": "NVDA",
  "start_date": "2020-01-01",
  "end_date": "2025-01-01",
  "features": [
    "return",
    "volatility",
    "momentum"
  ],
  "model": "vqc",
  "backend": "default.qubit"
}
```

Response:

```json
{
  "success": true,
  "data": {
    "experiment_id": "qexp_123",
    "status": "queued"
  }
}
```

This should generally be asynchronous.

---

# 39. Quantum portfolio optimization

## POST `/quantum/portfolio-optimize`

Request:

```json
{
  "assets": [
    "NVDA",
    "BTC-USD",
    "GC=F"
  ],
  "objective": "risk_adjusted_return",
  "constraints": {
    "max_assets": 3
  },
  "algorithm": "qaoa",
  "backend": "simulator"
}
```

Response:

```json
{
  "success": true,
  "data": {
    "experiment_id": "qexp_456",
    "status": "queued"
  }
}
```

---

# 40. Quantum experiment result

## GET `/quantum/experiments/{id}`

Response:

```json
{
  "success": true,
  "data": {
    "experiment_id": "qexp_456",
    "status": "completed",
    "algorithm": "qaoa",
    "backend": "simulator",
    "result": {
      "weights": {},
      "objective_value": 0.72
    },
    "classical_comparison": {
      "objective_value": 0.69
    },
    "execution_time_ms": 1842
  }
}
```

---

# 41. AI Research APIs

The LLM should **not directly perform financial calculations**.

It should call our backend tools.

## POST `/ai/research`

Request:

```json
{
  "message": "Analyze NVIDIA using a 20/50 SMA crossover from 2023 to 2025 and compare it with buy and hold.",
  "context": {
    "symbol": "NVDA"
  }
}
```

Response:

```json
{
  "success": true,
  "data": {
    "answer": "The backtest shows...",
    "tools_used": [
      "get_price_history",
      "calculate_indicators",
      "run_backtest",
      "compare_strategies"
    ],
    "artifacts": [
      {
        "type": "backtest",
        "id": "bt_123"
      }
    ]
  }
}
```

---

# 42. Natural-language backtesting

## POST `/ai/backtest`

Request:

```json
{
  "prompt": "Backtest a 20 and 50 day SMA crossover on NVIDIA from 2022 to 2025 with $100,000 initial capital and 0.1% transaction costs."
}
```

The LLM converts this into a structured configuration.

Backend validates it.

Then backtesting engine executes it.

Response:

```json
{
  "success": true,
  "data": {
    "backtest_id": "bt_789",
    "parsed_configuration": {
      "symbol": "NVDA",
      "strategy": "sma_crossover",
      "fast_period": 20,
      "slow_period": 50,
      "initial_capital": 100000,
      "transaction_cost": 0.001
    },
    "status": "queued"
  }
}
```

This is a strong demo feature.

---

# 43. AI explanation API

## POST `/ai/explain`

Request:

```json
{
  "artifact_type": "backtest",
  "artifact_id": "bt_123",
  "question": "Why did the strategy underperform during this period?"
}
```

Response:

```json
{
  "success": true,
  "data": {
    "explanation": "...",
    "evidence": [
      {
        "metric": "max_drawdown",
        "value": -0.21
      },
      {
        "metric": "volatility",
        "value": 0.34
      }
    ]
  }
}
```

The AI explanation must be grounded in actual backend results.

---

# 44. Research experiment APIs

## POST `/research/experiments`

Create a reproducible experiment.

Request:

```json
{
  "name": "NVDA SMA Robustness",
  "description": "Testing sensitivity to SMA parameters",
  "configuration": {
    "strategy": "sma_crossover",
    "parameters": {
      "fast": [10, 20, 30],
      "slow": [40, 50, 60]
    }
  }
}
```

Response:

```json
{
  "success": true,
  "data": {
    "experiment_id": "exp_123",
    "status": "created"
  }
}
```

---

## GET `/research/experiments`

Query:

```text
page
page_size
status
type
```

---

## GET `/research/experiments/{id}`

Returns:

```json
{
  "success": true,
  "data": {
    "experiment_id": "exp_123",
    "name": "NVDA SMA Robustness",
    "created_at": "2026-09-19T10:00:00Z",
    "configuration": {},
    "results": {},
    "metrics": {}
  }
}
```

---

# 45. Research comparison

## POST `/research/compare`

Request:

```json
{
  "experiments": [
    "exp_123",
    "exp_456",
    "exp_789"
  ]
}
```

Response:

```json
{
  "success": true,
  "data": {
    "experiments": [],
    "comparison": {
      "return": [],
      "sharpe": [],
      "volatility": [],
      "max_drawdown": []
    }
  }
}
```

---

# 46. Backtest trust report

This is worth making a dedicated endpoint because your project explicitly emphasizes avoiding misleading backtests.

## GET `/backtests/{id}/trust-report`

Response:

```json
{
  "success": true,
  "data": {
    "lookahead_bias_check": {
      "status": "passed"
    },
    "data_leakage_check": {
      "status": "passed"
    },
    "execution_model_check": {
      "status": "passed"
    },
    "transaction_cost_check": {
      "status": "passed"
    },
    "out_of_sample_check": {
      "status": "warning",
      "message": "Limited out-of-sample period"
    },
    "overall": "review"
  }
}
```

Frontend can display:

```text
BACKTEST TRUST

✓ No look-ahead bias detected
✓ No data leakage detected
✓ Transaction costs included
✓ Next-bar execution
⚠ Limited out-of-sample validation
```

This directly supports the project's requirement to minimize look-ahead bias, leakage, unrealistic execution and over-optimization. 

---

# 47. Job APIs

Anything computationally expensive should use the job system.

## GET `/jobs/{job_id}`

Response while running:

```json
{
  "success": true,
  "data": {
    "job_id": "job_123",
    "status": "running",
    "progress": 64,
    "message": "Running simulation 6400/10000"
  }
}
```

Completed:

```json
{
  "success": true,
  "data": {
    "job_id": "job_123",
    "status": "completed",
    "progress": 100,
    "result_type": "monte_carlo",
    "result_id": "mc_123"
  }
}
```

Failed:

```json
{
  "success": true,
  "data": {
    "job_id": "job_123",
    "status": "failed",
    "error": {
      "code": "SIMULATION_FAILED",
      "message": "Insufficient historical data"
    }
  }
}
```

---

# 48. Pagination standard

For list APIs:

```http
GET /assets?page=1&page_size=25
```

Response:

```json
{
  "success": true,
  "data": [],
  "meta": {
    "page": 1,
    "page_size": 25,
    "total": 125,
    "total_pages": 5
  }
}
```

---

# 49. Filtering standard

For example:

```http
GET /assets?asset_class=equity&provider=yahoo&search=NVDA
```

Backtest:

```http
GET /backtests?status=completed&strategy=sma_crossover
```

Experiments:

```http
GET /research/experiments?status=completed
```

---

# 50. Date format

Use ISO 8601 everywhere.

```text
2026-09-19
```

Datetime:

```text
2026-09-19T10:30:00Z
```

Do not return dates in formats like:

```text
19/09/2026
09-19-26
Sep 19 2026
```

The frontend can format them for display.

---

# 51. Financial number conventions

The API should return raw numerical values.

For example:

```json
{
  "return": 0.1824,
  "volatility": 0.2412,
  "sharpe": 1.38
}
```

The frontend decides whether to display:

```text
18.24%
24.12%
1.38
```

This is important because the backend should not contain presentation logic.

---

# 52. API error codes

Create a central error enum:

```text
INVALID_REQUEST
INVALID_PARAMETER
ASSET_NOT_FOUND
DATA_NOT_FOUND
DATA_PROVIDER_ERROR
DATA_VALIDATION_FAILED
INSUFFICIENT_DATA
STRATEGY_NOT_FOUND
INVALID_STRATEGY_PARAMETERS
BACKTEST_FAILED
BACKTEST_NOT_FOUND
JOB_NOT_FOUND
JOB_FAILED
MODEL_NOT_AVAILABLE
QUANTUM_BACKEND_UNAVAILABLE
QUANTUM_EXPERIMENT_FAILED
AI_SERVICE_UNAVAILABLE
RATE_LIMIT_EXCEEDED
UNAUTHORIZED
FORBIDDEN
INTERNAL_ERROR
```

Example:

```json
{
  "success": false,
  "data": null,
  "meta": {
    "request_id": "req_abc"
  },
  "error": {
    "code": "INSUFFICIENT_DATA",
    "message": "At least 252 trading days are required.",
    "details": {
      "required": 252,
      "available": 143
    }
  }
}
```

---

# 53. Request ID

Every API response should contain:

```http
X-Request-ID: req_123456
```

This makes debugging much easier.

Frontend errors can display:

```text
Something went wrong.

Request ID: req_123456
```

The developer can then find that request in backend logs.

---

# 54. API versioning

Start with:

```text
/api/v1
```

Never expose:

```text
/api/sma
```

Use:

```text
/api/v1/indicators/sma
```

If the API changes significantly:

```text
/api/v2
```

This prevents breaking the frontend later.

---

# 55. Frontend API client

Your frontend developer should build one central API client.

```text
frontend/
└── src/
    └── api/
        ├── client.ts
        ├── auth.ts
        ├── assets.ts
        ├── marketData.ts
        ├── indicators.ts
        ├── correlation.ts
        ├── strategies.ts
        ├── backtests.ts
        ├── robustness.ts
        ├── regimes.ts
        ├── risk.ts
        ├── portfolio.ts
        ├── quantum.ts
        ├── ai.ts
        ├── research.ts
        └── jobs.ts
```

Example:

```typescript
const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL;

export async function apiClient<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {

  const response = await fetch(
    `${API_BASE_URL}/api/v1${endpoint}`,
    {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
    }
  );

  if (!response.ok) {
    throw await response.json();
  }

  return response.json();
}
```

Then:

```typescript
export function getAssetHistory(
  symbol: string,
  startDate: string,
  endDate: string
) {
  return apiClient(
    `/assets/${symbol}/history?start_date=${startDate}&end_date=${endDate}`
  );
}
```

The React components never construct raw URLs themselves.

---

# 56. Recommended API-to-page mapping

| Frontend Page    | APIs                                                                                             |
| ---------------- | ------------------------------------------------------------------------------------------------ |
| Overview         | `/health`, `/assets`, `/analytics/summary`                                                       |
| Markets          | `/assets`, `/assets/{symbol}/history`                                                            |
| Asset Analysis   | `/assets/{symbol}/history`, `/analytics/summary`, indicator APIs                                 |
| Quant Analytics  | indicator APIs                                                                                   |
| Correlation      | `/correlation/matrix`, `/correlation/rolling`                                                    |
| Strategies       | `/strategies`, `/strategies/signals`                                                             |
| Backtesting      | `/strategies`, `/backtests`                                                                      |
| Backtest Results | `/backtests/{id}`, `/equity`, `/trades`, `/metrics`, `/benchmark`, `/trust-report`               |
| Robustness       | `/robustness/parameter-stress`, `/cost-stress`, `/walk-forward`                                  |
| Market Regimes   | `/regimes/detect`, `/regimes/compare`                                                            |
| Risk             | `/risk/metrics`, `/risk/var`, `/risk/cvar`, `/risk/monte-carlo`                                  |
| Portfolio        | `/portfolio/create`, `/portfolio/analyze`, `/portfolio/optimize`                                 |
| Quantum Lab      | `/quantum/status`, `/quantum/regime`, `/quantum/portfolio-optimize`, `/quantum/experiments/{id}` |
| AI Research      | `/ai/research`, `/ai/backtest`, `/ai/explain`                                                    |
| Research         | `/research/experiments`, `/research/compare`                                                     |
| Settings         | `/auth/me`, configuration endpoints if needed                                                    |

---

# 57. Complete endpoint inventory

For the frontend designer/developer, this is the concise master list:

```text
/api/v1

AUTH
POST   /auth/register
POST   /auth/login
GET    /auth/me

SYSTEM
GET    /health

ASSETS
GET    /assets
GET    /assets/{symbol}/history

DATA
POST   /data/validate

ANALYTICS
POST   /analytics/summary

INDICATORS
POST   /indicators/sma
POST   /indicators/ema
POST   /indicators/returns
POST   /indicators/volatility
POST   /indicators/sharpe
POST   /indicators/drawdown

CORRELATION
POST   /correlation/matrix
POST   /correlation/rolling

STRATEGIES
GET    /strategies
POST   /strategies/signals
POST   /strategies/regime-adaptive

BACKTESTING
POST   /backtests
GET    /backtests
GET    /backtests/{id}
GET    /backtests/{id}/equity
GET    /backtests/{id}/trades
GET    /backtests/{id}/metrics
GET    /backtests/{id}/benchmark
GET    /backtests/{id}/trust-report

ROBUSTNESS
POST   /robustness/parameter-stress
POST   /robustness/cost-stress
POST   /robustness/walk-forward

REGIMES
POST   /regimes/detect
POST   /regimes/compare
GET    /regimes/{asset}

RISK
POST   /risk/metrics
POST   /risk/var
POST   /risk/cvar
POST   /risk/monte-carlo

PORTFOLIO
POST   /portfolio/create
POST   /portfolio/analyze
POST   /portfolio/optimize

QUANTUM
GET    /quantum/status
POST   /quantum/regime
POST   /quantum/portfolio-optimize
GET    /quantum/experiments/{id}

AI
POST   /ai/research
POST   /ai/backtest
POST   /ai/explain

RESEARCH
POST   /research/experiments
GET    /research/experiments
GET    /research/experiments/{id}
POST   /research/compare

JOBS
GET    /jobs/{job_id}
```

That's approximately **50 frontend-facing endpoints**, but they are organized into clear domains rather than exposing internal implementation details.

## 58. One important architectural rule

The API should **not expose internal services directly**.

For example, don't create:

```text
/api/v1/pandas/calculate
/api/v1/sklearn/model
/api/v1/qiskit/run
/api/v1/database/query
/api/v1/yfinance/download
```

Instead expose business capabilities:

```text
/api/v1/backtests
/api/v1/regimes/detect
/api/v1/portfolio/optimize
/api/v1/assets/{symbol}/history
```

That gives you a stable API even if the implementation changes from Pandas to another library, from K-Means to another model, or from one market-data provider to another.

The original project specifically calls for normalized market data, quantitative analytics, strategy backtesting, benchmark comparison, robustness analysis, regime analysis, risk/portfolio functionality, interactive visualization, and future AI/ML/quantum capabilities. 

### What I would hand to the backend + frontend teams

The next artifact should be an **API Contract / OpenAPI specification** containing every endpoint above with exact Pydantic request/response schemas. That can become the single source of truth so the backend developer implements FastAPI from it and the frontend developer generates TypeScript types from the same contract.
