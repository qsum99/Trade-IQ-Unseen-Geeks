# Quant Platform API Documentation

**Base URL:** `http://localhost:8000/api/v1`
**Version:** 1.0.0
**Content-Type:** `application/json`

---

## Rate Limiting
- **Default:** 100 requests/minute per IP
- **Response Header:** `X-Request-ID` on every response

---

## Standard Response Format

### Success
```json
{
  "success": true,
  "data": {},
  "meta": {"request_id": "req_abc123"},
  "error": null
}
```

### Error
```json
{
  "success": false,
  "data": null,
  "meta": {"request_id": "req_abc123"},
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable message",
    "details": {}
  }
}
```

---

## Endpoints

### Health & System

#### GET `/api/v1/health`
Check service health and dependency status.

**Response:**
```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "version": "1.0.0",
    "environment": "development",
    "services": {
      "database": "healthy",
      "market_data": "healthy",
      "quant_engine": "healthy",
      "ml_engine": "healthy",
      "quantum_engine": "available"
    }
  },
  "meta": {"request_id": "req_abc123"},
  "error": null
}
```

---

### Assets & Market Data

#### GET `/api/v1/assets`
List all supported assets with filtering.

**Query Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| asset_class | string | - | Filter by asset class (equity, crypto, commodity, index) |
| search | string | - | Search by symbol or name |
| page | int | 1 | Page number |
| page_size | int | 25 | Items per page |

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "symbol": "NVDA",
      "name": "NVIDIA Corporation",
      "asset_class": "equity",
      "currency": "USD",
      "exchange": "NASDAQ",
      "provider": "yahoo",
      "active": true
    }
  ],
  "meta": {"page": 1, "page_size": 25, "total": 100},
  "error": null
}
```

#### GET `/api/v1/assets/{symbol}/history`
Get historical OHLCV data for a symbol.

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| start_date | string | Yes | Start date (ISO 8601) |
| end_date | string | Yes | End date (ISO 8601) |
| interval | string | No | "1d" (default) |

**Response:**
```json
{
  "success": true,
  "data": {
    "symbol": "NVDA",
    "interval": "1d",
    "currency": "USD",
    "data": [
      {
        "timestamp": "2024-01-02T00:00:00+00:00",
        "symbol": "NVDA",
        "open": 49.24,
        "high": 49.29,
        "low": 47.60,
        "close": 48.17,
        "adjusted_close": 48.03,
        "volume": 411254000,
        "currency": "USD",
        "exchange": "YAHOO",
        "provider": "yahoo",
        "interval": "1d"
      }
    ]
  },
  "meta": {},
  "error": null
}
```

#### POST `/api/v1/data/validate`
Validate data quality for a symbol.

**Request Body:**
```json
{
  "symbol": "NVDA",
  "start_date": "2024-01-01",
  "end_date": "2024-03-01",
  "provider": "yahoo"
}
```

---

### Quantitative Analytics

#### POST `/api/v1/indicators/sma`
Simple Moving Average.

**Request Body:**
```json
{
  "symbol": "NVDA",
  "start_date": "2024-01-01",
  "end_date": "2024-03-01",
  "period": 20
}
```

#### POST `/api/v1/indicators/ema`
Exponential Moving Average.

#### POST `/api/v1/indicators/returns`
Calculate returns (simple or log).

#### POST `/api/v1/indicators/volatility`
Rolling volatility.

#### POST `/api/v1/indicators/sharpe`
Sharpe ratio.

#### POST `/api/v1/indicators/drawdown`
Maximum drawdown analysis.

#### POST `/api/v1/analytics/summary`
Combined analytics for an asset.

**Request Body:**
```json
{
  "symbol": "NVDA",
  "start_date": "2024-01-01",
  "end_date": "2024-03-01",
  "indicators": {
    "sma": [20, 50],
    "ema": [20],
    "returns": true,
    "volatility": true,
    "sharpe": true,
    "drawdown": true
  }
}
```

#### POST `/api/v1/correlation/matrix`
Correlation matrix for multiple assets.

**Request Body:**
```json
{
  "symbols": ["NVDA", "BTC-USD", "GC=F"],
  "start_date": "2024-01-01",
  "end_date": "2024-03-01",
  "method": "pearson"
}
```

#### POST `/api/v1/correlation/rolling`
Rolling correlation between two assets.

---

### Strategies

#### GET `/api/v1/strategies`
List available strategies.

**Response:**
```json
{
  "success": true,
  "data": [
    {
      "id": "sma_crossover",
      "name": "SMA Crossover",
      "description": "Generates signals using fast and slow SMA",
      "parameters": [
        {"name": "fast_period", "type": "integer", "default": 20},
        {"name": "slow_period", "type": "integer", "default": 50}
      ]
    },
    {
      "id": "ema_trend",
      "name": "EMA Trend",
      "description": "Generates signals using fast and slow EMA trend",
      "parameters": [...]
    },
    {
      "id": "momentum",
      "name": "Momentum",
      "description": "Generates signals from lookback price momentum",
      "parameters": [...]
    },
    {
      "id": "mean_reversion",
      "name": "Mean Reversion",
      "description": "Generates signals from rolling z-score of close price",
      "parameters": [...]
    },
    {
      "id": "regime_adaptive",
      "name": "Regime Adaptive",
      "description": "Selects per-bar signals from mapped strategies by regime label",
      "parameters": [...]
    }
  ],
  "meta": {},
  "error": null
}
```

#### POST `/api/v1/strategies/signals`
Generate signals for a strategy.

**Request Body:**
```json
{
  "symbol": "NVDA",
  "strategy": "sma_crossover",
  "parameters": {"fast_period": 20, "slow_period": 50},
  "start_date": "2024-01-01",
  "end_date": "2024-03-01"
}
```

#### POST `/api/v1/strategies/regime-adaptive`
Run regime-adaptive strategy.

**Request Body:**
```json
{
  "symbol": "NVDA",
  "regime_model": "kmeans",
  "mapping": {"bull": "momentum", "bear": "mean_reversion"},
  "strategy_params": {},
  "regime_timeline": ["bull", "bear", "bull", "high_volatility"],
  "start_date": "2024-01-01",
  "end_date": "2024-03-01"
}
```

---

### Backtesting

#### POST `/api/v1/backtests`
Run a backtest.

**Request Body (api.md §18 style):**
```json
{
  "name": "NVDA SMA 20/50",
  "symbol": "NVDA",
  "strategy": {
    "type": "sma_crossover",
    "parameters": {"fast_period": 20, "slow_period": 50}
  },
  "period": {"start_date": "2023-01-01", "end_date": "2025-01-01"},
  "capital": {"initial": 100000, "position_sizing": "full"},
  "execution": {
    "transaction_cost": 0.001,
    "slippage": 0.0005,
    "execution_price": "next_open"
  },
  "benchmark": "buy_and_hold"
}
```

**Alternative (flat style):**
```json
{
  "symbol": "NVDA",
  "strategy": "sma_crossover",
  "parameters": {"fast_period": 20, "slow_period": 50},
  "start_date": "2024-01-01",
  "end_date": "2024-03-01",
  "initial_capital": 100000,
  "transaction_cost": 0.001,
  "slippage": 0.0005,
  "execution_price": "next_open"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "backtest_id": "bt_abc123",
    "status": "completed",
    "strategy": "sma_crossover",
    "symbol": "NVDA",
    "trades": [],
    "equity": [...],
    "metrics": {
      "total_return": 0.15,
      "sharpe": 1.2,
      "volatility": 0.25,
      "max_drawdown": -0.12,
      "total_trades": 15,
      "win_rate": 0.6,
      "profit_factor": 1.8,
      "average_trade": 0.01
    },
    "benchmark": {
      "curve": [...],
      "compare": {
        "strategy_return": 0.15,
        "benchmark_return": 0.10,
        "excess_return": 0.05,
        "tracking_error": 0.12,
        "information_ratio": 0.42,
        "upside_capture": 110.5,
        "downside_capture": 95.2,
        "strategy_sharpe": 1.2,
        "benchmark_sharpe": 1.0,
        "strategy_mdd": -0.12,
        "benchmark_mdd": -0.15
      }
    }
  },
  "meta": {"request_id": "req_abc123"},
  "error": null
}
```

#### GET `/api/v1/backtests`
List all backtests.

#### GET `/api/v1/backtests/{id}`
Get backtest details.

#### GET `/api/v1/backtests/{id}/equity`
Get equity curve.

#### GET `/api/v1/backtests/{id}/trades`
Get trade list.

#### GET `/api/v1/backtests/{id}/metrics`
Get performance metrics.

#### GET `/api/v1/backtests/{id}/benchmark`
Get benchmark comparison.

#### GET `/api/v1/backtests/{id}/trust-report`
Get trust/validation report.

---

### Risk Management

#### POST `/api/v1/risk/metrics`
Compute comprehensive risk metrics.

**Request Body:**
```json
{
  "symbol": "NVDA",
  "start_date": "2024-01-01",
  "end_date": "2024-03-01",
  "benchmark_symbol": "^GSPC",
  "risk_free_rate": 0.05,
  "confidence_levels": [0.95, 0.99]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "symbol": "NVDA",
    "volatility": 0.0144,
    "annualized_volatility": 0.218,
    "sharpe_ratio": -0.39,
    "sortino_ratio": -0.56,
    "calmar_ratio": -0.21,
    "omega_ratio": 0.97,
    "max_drawdown": -0.29,
    "max_drawdown_duration_days": 0,
    "beta": -0.012,
    "alpha": -0.11,
    "treynor_ratio": 9.38,
    "information_ratio": -1.18,
    "tracking_error": 0.33,
    "downside_deviation": 0.159,
    "var_95": 0.023,
    "var_99": 0.031,
    "cvar_95": 0.028,
    "cvar_99": 0.034
  },
  "meta": {"request_id": "req_abc123"},
  "error": null
}
```

#### POST `/api/v1/risk/var`
Compute Value-at-Risk.

#### POST `/api/v1/risk/cvar`
Compute Conditional VaR (Expected Shortfall).

#### POST `/api/v1/risk/monte-carlo`
Run Monte Carlo simulation.

#### POST `/api/v1/risk/tail`
Tail risk analysis.

---

### Portfolio Management

#### POST `/api/v1/portfolio/analyze`
Analyze portfolio metrics.

**Request Body:**
```json
{
  "symbols": ["NVDA", "BTC-USD", "GC=F"],
  "weights": [0.5, 0.3, 0.2],
  "start_date": "2024-01-01",
  "end_date": "2024-03-01"
}
```

#### POST `/api/v1/portfolio/optimize`
Optimize portfolio weights.

**Request Body:**
```json
{
  "symbols": ["NVDA", "BTC-USD", "GC=F"],
  "start_date": "2024-01-01",
  "end_date": "2024-03-01",
  "method": "max_sharpe",
  "min_weight": 0.0,
  "max_weight": 1.0
}
```

**Methods:** `equal_weight`, `inverse_vol`, `min_variance`, `max_sharpe`, `risk_parity`

---

### Quantum Computing

#### GET `/api/v1/quantum/status`
Check quantum computing availability.

#### GET `/api/v1/quantum/hardware-report`
Get IBM Quantum hardware report.

#### POST `/api/v1/quantum/regime`
Run quantum regime detection (PennyLane VQC).

**Request Body:**
```json
{
  "symbol": "NVDA",
  "start_date": "2024-01-01",
  "end_date": "2024-03-01",
  "features": ["return", "volatility", "momentum"],
  "model": "vqc",
  "backend": "default.qubit"
}
```

#### POST `/api/v1/quantum/portfolio-optimize`
Quantum portfolio optimization (QAOA).

**Request Body:**
```json
{
  "symbols": ["NVDA", "BTC-USD", "GC=F"],
  "start_date": "2024-01-01",
  "end_date": "2024-03-01",
  "objective": "risk_adjusted_return",
  "constraints": {"max_assets": 3},
  "algorithm": "qaoa",
  "backend": "simulator"
}
```

#### GET `/api/v1/quantum/experiments/{id}`
Get experiment result.

#### GET `/api/v1/quantum/experiments`
List experiments.

---

### Validation & Robustness

#### POST `/api/v1/robustness/walk-forward`
Walk-forward validation.

#### POST `/api/v1/robustness/cost-stress`
Cost sensitivity analysis.

#### POST `/api/v1/robustness/reality-check`
White's Reality Check.

#### POST `/api/v1/robustness/deflated-sharpe`
Deflated Sharpe Ratio.

---

### AI Research Assistant

#### POST `/api/v1/ai/research`
Natural language research query.

**Request Body:**
```json
{
  "message": "Compare SMA and EMA strategies on BTC during high-volatility periods.",
  "context": {"symbol": "BTC-USD"}
}
```

#### POST `/api/v1/ai/explain-backtest`
Explain backtest results.

---

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| INVALID_REQUEST | 400 | Malformed request |
| INVALID_PARAMETER | 422 | Invalid parameter value |
| ASSET_NOT_FOUND | 404 | Asset not found |
| DATA_NOT_FOUND | 404 | Data not available |
| DATA_PROVIDER_ERROR | 503 | External provider error |
| DATA_VALIDATION_FAILED | 422 | Data quality check failed |
| INSUFFICIENT_DATA | 422 | Not enough data points |
| STRATEGY_NOT_FOUND | 404 | Strategy not found |
| INVALID_STRATEGY_PARAMETERS | 422 | Invalid strategy params |
| BACKTEST_FAILED | 500 | Backtest execution failed |
| BACKTEST_NOT_FOUND | 404 | Backtest not found |
| JOB_NOT_FOUND | 404 | Job not found |
| JOB_FAILED | 500 | Background job failed |
| MODEL_NOT_AVAILABLE | 503 | ML model not available |
| QUANTUM_BACKEND_UNAVAILABLE | 503 | Quantum backend down |
| QUANTUM_EXPERIMENT_FAILED | 500 | Quantum experiment failed |
| AI_SERVICE_UNAVAILABLE | 503 | AI service down |
| RATE_LIMIT_EXCEEDED | 429 | Rate limit exceeded |
| INTERNAL_ERROR | 500 | Internal server error |

---

## Example Usage

### Python
```python
import requests

BASE = "http://localhost:8000/api/v1"

# Get asset list
r = requests.get(f"{BASE}/assets?asset_class=equity")
print(r.json())

# Run SMA indicator
r = requests.post(f"{BASE}/indicators/sma", json={
    "symbol": "NVDA",
    "start_date": "2024-01-01",
    "end_date": "2024-03-01",
    "period": 20
})
print(r.json())

# Run backtest
r = requests.post(f"{BASE}/backtests", json={
    "symbol": "NVDA",
    "strategy": {"type": "sma_crossover", "parameters": {"fast_period": 20, "slow_period": 50}},
    "period": {"start_date": "2023-01-01", "end_date": "2025-01-01"},
    "capital": {"initial": 100000, "position_sizing": "full"},
    "execution": {"transaction_cost": 0.001, "slippage": 0.0005},
    "benchmark": "buy_and_hold"
})
bt = r.json()["data"]["backtest_id"]
```

### JavaScript/TypeScript
```typescript
const BASE = "http://localhost:8000/api/v1";

async function runBacktest() {
  const res = await fetch(`${BASE}/backtests`, {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({
      symbol: "NVDA",
      strategy: {type: "sma_crossover", parameters: {fast_period: 20, slow_period: 50}},
      period: {start_date: "2023-01-01", end_date: "2025-01-01"},
      capital: {initial: 100000, position_sizing: "full"},
      execution: {transaction_cost: 0.001, slippage: 0.0005},
      benchmark: "buy_and_hold"
    })
  });
  return res.json();
}
```

---

## Rate Limiting
- **Default:** 100 requests/minute per IP
- **Headers:** `X-Request-ID` on every response
- **Exceeded:** Returns 429 with `RATE_LIMIT_EXCEEDED` code

---

## Testing
```bash
# Run tests
uv run pytest tests --ignore=tests/samarth -q

# Samarth tests
uv run pytest tests/samarth -q

# Stress test
uv run pytest tests/test_stress.py -v
```

---

## OpenAPI/Swagger
Available at: `http://localhost:8000/docs` or `http://localhost:8000/openapi.json`