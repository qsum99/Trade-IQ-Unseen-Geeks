# Final System Architecture

## Quantitative Multi-Asset Financial Intelligence, Backtesting & Experimental Quantum Analytics Platform



### 1. Architecture Objective

The platform will be designed as a **backend-centric, API-first quantitative financial intelligence system**.

The architecture has four principles:

1. **The backend owns all business logic.**
2. **The frontend communicates only with backend APIs.**
3. **Financial calculations are deterministic and reproducible.**
4. **AI/ML and experimental quantum capabilities are isolated services, never required for the core platform to operate.**

The complete system is:

```text
┌─────────────────────────────────────────────────────────────────────┐
│                         PRESENTATION LAYER                          │
│                                                                     │
│              Next.js + TypeScript + Plotly + UI Components         │
│                                                                     │
│  Dashboard | Assets | Indicators | Backtests | Risk | Regimes      │
│  Correlation | Strategy Analysis | Portfolio | AI Research         │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                           HTTPS / REST
                                 │
┌────────────────────────────────▼────────────────────────────────────┐
│                            API LAYER                                │
│                                                                     │
│                         FastAPI + Pydantic                          │
│                                                                     │
│ Authentication | Validation | Rate Limiting | API Versioning       │
│ Request/Response Schemas | Error Handling | OpenAPI Documentation  │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
                    ▼                         ▼
┌──────────────────────────────┐   ┌─────────────────────────────────┐
│       CORE SERVICES          │   │       INTELLIGENCE SERVICES     │
│                              │   │                                 │
│ Data Service                 │   │ Regime Detection               │
│ Indicator Service            │   │ AI Research Assistant           │
│ Correlation Service          │   │ Backtest Explanation            │
│ Strategy Service             │   │ Experimental Quantum Models     │
│ Backtesting Service          │   │ Portfolio Optimization          │
│ Risk Service                 │   │                                 │
│ Robustness Service           │   │                                 │
└──────────────┬───────────────┘   └───────────────┬─────────────────┘
               │                                   │
               └─────────────────┬─────────────────┘
                                 │
                     ┌───────────▼────────────┐
                     │    QUANT ENGINE        │
                     │                         │
                     │ NumPy | Pandas | SciPy │
                     │ Statsmodels             │
                     └───────────┬────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
              ▼                  ▼                  ▼
       ┌─────────────┐    ┌─────────────┐   ┌──────────────┐
       │ Data Layer  │    │ ML Layer    │   │ Quantum Layer│
       │             │    │             │   │              │
       │ PostgreSQL  │    │ scikit-learn│   │ PennyLane    │
       │ TimescaleDB │    │ HMM         │   │ Qiskit       │
       │ Parquet     │    │             │   │              │
       └──────┬──────┘    └─────────────┘   └──────────────┘
              │
       ┌──────▼──────────────────────────────────────────┐
       │                DATA PROVIDERS                    │
       │                                                  │
       │ NSE | Zerodha | Yahoo Finance | Binance | FRED │
       │ Gold/reference data providers                    │
       └──────────────────────────────────────────────────┘
```

---

# 2. Complete Layered Architecture

## Layer 1: Frontend

### Technology

* Next.js
* TypeScript
* Tailwind CSS
* shadcn/ui
* Plotly
* React Query / TanStack Query

### Responsibility

The frontend is strictly a **presentation and interaction layer**.

It should:

* display data
* collect user parameters
* call APIs
* display API responses
* render charts
* display backtest results
* display regime analysis
* display risk metrics
* display AI-generated explanations

It must **not**:

* calculate Sharpe ratio
* calculate indicators
* access PostgreSQL
* access Zerodha
* access NSE
* call Binance directly
* run Python
* execute quantum circuits
* contain financial business logic

### Frontend flow

```text
User
 ↓
React UI
 ↓
API Client
 ↓
FastAPI
 ↓
Backend Service
 ↓
Response
 ↓
React Query
 ↓
Chart / Table / Visualization
```

---

# 3. API Gateway Layer

## Technology

**FastAPI + Pydantic**

The API layer is the only communication boundary between the frontend and backend.

Base URL:

```text
/api/v1/
```

### Main API domains

```text
/api/v1/assets
/api/v1/data
/api/v1/indicators
/api/v1/correlation
/api/v1/strategies
/api/v1/backtests
/api/v1/robustness
/api/v1/regimes
/api/v1/risk
/api/v1/portfolio
/api/v1/quantum
/api/v1/ai
/api/v1/research
```

---

# 4. Asset & Market Data Service

## Purpose

Provides a unified interface to historical and supported market data.

### External providers

```text
                    Market Data Service
                           │
       ┌──────────┬────────┼────────┬──────────┐
       ▼          ▼        ▼        ▼          ▼
     NSE       Zerodha   Yahoo    Binance     FRED
```

Additional gold/reference sources can be connected through the same provider interface.

### Provider abstraction

```python
class MarketDataProvider:

    def get_history(
        self,
        symbol,
        start_date,
        end_date,
        interval
    ):
        ...
```

Implementations:

```text
NSEProvider
ZerodhaProvider
YahooProvider
BinanceProvider
FREDProvider
GoldProvider
```

The rest of the application never directly depends on these providers.

---

# 5. Canonical Market Data Model

Every provider must be converted into one internal format.

```text
MarketData
────────────────────────
asset_id
symbol
timestamp
open
high
low
close
adjusted_close
volume
currency
exchange
source
interval
```

Therefore:

```text
NSE
 │
Zerodha
 │
Yahoo
 │
Binance
 │
FRED
 │
 ▼
Provider Adapter
 │
 ▼
Canonical MarketData
```

This prevents provider-specific formats from leaking into the quantitative engine.

---

# 6. Data Quality & Validation Engine

Before financial calculations occur:

```text
Raw Data
   ↓
Schema Validation
   ↓
Missing Value Check
   ↓
Duplicate Check
   ↓
OHLC Validation
   ↓
Timestamp Validation
   ↓
Trading Calendar Validation
   ↓
Outlier Detection
   ↓
Source Consistency
   ↓
Clean Data
```

### Checks

* missing observations
* duplicate timestamps
* invalid OHLC relationships
* abnormal price jumps
* volume anomalies
* timezone inconsistencies
* market-calendar mismatches
* incomplete periods
* source discrepancies

Each dataset gets a quality report.

```json
{
  "quality_score": 96.4,
  "missing_values": 2,
  "duplicates": 0,
  "invalid_ohlc": 0,
  "outliers": 3,
  "source": "NSE"
}
```

---

# 7. Data Storage Architecture

## Primary database

### PostgreSQL

For:

* assets
* metadata
* users
* experiments
* strategies
* backtests
* trades
* results
* model configurations

## Time-series storage

### TimescaleDB

For:

* OHLCV
* high-frequency observations
* time-series metrics

## Research storage

### Parquet

For:

* raw historical datasets
* cleaned datasets
* intermediate analytical datasets
* large backtest datasets

Architecture:

```text
                Data Storage
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
   PostgreSQL    TimescaleDB    Parquet
   Metadata      Time Series    Research
```

---

# 8. Quantitative Analytics Engine

This is the core mathematical engine.

## Technology

```text
NumPy
Pandas
SciPy
Statsmodels
```

### Indicators

```text
SMA
EMA
Daily Return
Cumulative Return
Rolling Return
Volatility
Annualized Volatility
Sharpe Ratio
Maximum Drawdown
Rolling Sharpe
```

Optional:

```text
RSI
MACD
ATR
Bollinger Bands
```

The core required metrics remain implemented directly rather than hiding them behind unnecessary abstraction.

---

# 9. Correlation Engine

Inputs:

```text
Asset A
Asset B
Asset C
...
```

Outputs:

```text
Correlation Matrix
Rolling Correlation
```

Example:

```text
             GOLD    BTC    NVDA
GOLD         1.00   0.21   -0.04
BTC          0.21   1.00    0.36
NVDA        -0.04   0.36    1.00
```

The API exposes the result to the frontend.

---

# 10. Strategy Engine

Strategies are implemented behind a common interface.

```python
class Strategy:

    def generate_signals(self, data):
        ...
```

Implement:

```text
SMA Crossover
EMA Trend
Momentum
Mean Reversion
Buy & Hold
```

Potential adaptive strategy:

```text
Regime-Adaptive Strategy
```

The strategy engine outputs signals only.

```text
Market Data
    ↓
Strategy
    ↓
BUY / SELL / HOLD
```

It does not execute trades.

---

# 11. Backtesting Engine

This remains a deterministic event-driven engine.

```text
Historical Data
      ↓
Strategy Signal
      ↓
Signal at T
      ↓
Execution at T+1
      ↓
Position Sizing
      ↓
Transaction Cost
      ↓
Slippage
      ↓
Portfolio Accounting
      ↓
Equity Curve
```

### Inputs

```text
Initial Capital
Asset
Date Range
Strategy
Parameters
Position Size
Transaction Cost
Slippage
Execution Model
```

### Outputs

```text
Total Return
Annualized Return
Sharpe
Volatility
Maximum Drawdown
Number of Trades
Win Rate
Average Trade
Transaction Costs
Equity Curve
Trade History
```

---

# 12. Benchmark Engine

Every strategy can be compared with:

```text
Buy & Hold
```

The comparison API returns:

```text
Strategy
vs
Benchmark
```

Metrics:

```text
Return
Volatility
Sharpe
Maximum Drawdown
Trade Count
Transaction Cost
```

---

# 13. Robustness Engine

This is a major component.

```text
                  Backtest
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
 Walk-Forward   Parameter      Cost Stress
 Validation     Sensitivity
        │            │            │
        └────────────┼────────────┘
                     ▼
              Robustness Report
```

## Walk-forward

```text
Train → Validate → Test
       ↓
     Roll
       ↓
Train → Validate → Test
```

This prevents a single historical period from determining the strategy's apparent quality.

## Parameter sensitivity

For example:

```text
SMA Fast: 5–50
SMA Slow: 50–250
```

Generate a performance surface.

## Transaction-cost stress

```text
0.00%
0.05%
0.10%
0.20%
0.50%
1.00%
```

Observe whether the strategy remains viable under increasing costs.

---

# 14. Market Regime Engine

The regime engine has three levels.

## Level 1: Rule-based baseline

```text
Return
Volatility
Drawdown
Momentum
```

Can identify:

```text
Bull
Bear
High Volatility
Low Volatility
```

## Level 2: Classical ML

### K-Means

```text
Market Features
      ↓
StandardScaler
      ↓
K-Means
      ↓
Market States
```

### HMM

Optional second model:

```text
Market Features
      ↓
Hidden Markov Model
      ↓
Hidden States
      ↓
Regime Labels
```

## Level 3: Experimental Quantum ML

```text
Market Features
      ↓
Feature Encoding
      ↓
Variational Quantum Circuit
      ↓
Quantum Features
      ↓
Classical Classifier
      ↓
Regime
```

This component is optional.

The production platform continues to operate without it.

---

# 15. Regime-Adaptive Strategy Engine

Once regime detection exists:

```text
Market
  ↓
Regime Detector
  ↓
┌──────────────┬──────────────┬──────────────┬──────────────┐
│ Bull         │ Bear         │ High Vol     │ Low Vol      │
│ Momentum     │ Defensive    │ Mean Rev     │ Trend        │
└──────────────┴──────────────┴──────────────┴──────────────┘
```

This creates a natural connection between:

```text
ML
+
Quantitative Strategy
+
Backtesting
```

without making ML responsible for financial accounting.

---

# 16. Risk Engine

The risk engine operates independently from the strategy engine.

### Metrics

```text
Volatility
Sharpe
Maximum Drawdown
VaR
CVaR
Beta
Correlation
```

### Monte Carlo

Classical Monte Carlo should be the initial implementation:

```text
Historical Returns
      ↓
Distribution / Resampling
      ↓
Generate Paths
      ↓
Portfolio Paths
      ↓
Risk Distribution
```

Outputs:

```text
Expected Range
VaR
CVaR
Probability of Loss
Drawdown Distribution
```

---

# 17. Portfolio Engine

Portfolio functionality:

```text
Asset Selection
      ↓
Expected Returns
      ↓
Covariance
      ↓
Constraints
      ↓
Portfolio Optimizer
      ↓
Weights
```

Initial classical optimization:

```text
Minimum Volatility
Mean-Variance
Risk Parity
```

Experimental quantum optimization:

```text
Portfolio Problem
      ↓
QUBO
      ↓
QAOA
      ↓
Candidate Solution
```

The quantum optimizer is isolated from the main optimizer.

---

# 18. Experimental Quantum Layer

The quantum layer contains only research-oriented capabilities.

```text
                  Quantum Service
                        │
             ┌──────────┴──────────┐
             │                     │
       Quantum Regime       Quantum Portfolio
         Experiment            Optimization
             │                     │
         PennyLane                Qiskit
             │                     │
             └──────────┬──────────┘
                        │
                 Experiment Result
```

### Important design principle

Quantum is **not** used for:

```text
SMA
EMA
Sharpe
Volatility
Drawdown
Basic correlation
Basic backtesting
```

Those remain classical.

---

# 19. AI Research Assistant

The AI system should not independently perform financial mathematics.

Architecture:

```text
                    User
                     │
                     ▼
               AI Assistant
                     │
                 Tool Calling
                     │
                     ▼
               Backend APIs
                     │
       ┌─────────────┼─────────────┐
       ▼             ▼             ▼
   Backtesting      Risk         Regime
       API            API           API
       │              │             │
       └──────────────┼─────────────┘
                      ▼
               Structured Results
                      │
                      ▼
                 LLM Response
```

### Tools

```text
get_assets()
get_market_data()
calculate_indicators()
calculate_correlation()
detect_regime()
run_backtest()
compare_strategies()
run_walk_forward()
run_parameter_stress()
run_cost_stress()
calculate_risk()
run_monte_carlo()
optimize_portfolio()
compare_regime_models()
```

The LLM interprets the returned results.

It does not invent metrics.

---

# 20. Natural-Language Research

Example:

> "Backtest an EMA strategy on BTC from 2022 to 2025 with 0.1% transaction costs."

Flow:

```text
Natural Language
      ↓
AI Assistant
      ↓
Tool Selection
      ↓
POST /api/v1/backtests
      ↓
Backtest Engine
      ↓
Result
      ↓
AI Explanation
```

The same APIs remain usable without AI.

---

# 21. Backtest Trust Report

Every completed backtest should generate a machine-readable validation report.

```text
┌──────────────────────────────────────┐
│        BACKTEST TRUST REPORT         │
├──────────────────────────────────────┤
│ Data Quality              PASS       │
│ Missing Data              PASS       │
│ Duplicate Check           PASS       │
│ Look-Ahead Check          PASS       │
│ Leakage Check             PASS       │
│ Walk-Forward              PASS       │
│ Parameter Stability       REVIEW     │
│ Cost Sensitivity          PASS       │
│ Regime Coverage           PASS       │
└──────────────────────────────────────┘
```

This is generated by the backend, not the frontend.

---

# 22. Experiment Management

Every research experiment should be reproducible.

Store:

```text
Experiment ID
Dataset Version
Data Source
Strategy
Parameters
Initial Capital
Transaction Cost
Slippage
Date Range
Model
Random Seed
Software Version
Results
```

Example:

```json
{
  "experiment_id": "EXP-2026-0042",
  "strategy": "SMA_CROSSOVER",
  "fast_window": 20,
  "slow_window": 100,
  "transaction_cost": 0.001,
  "slippage": 0.0005,
  "seed": 42
}
```

---

# 23. API Contract Between Frontend and Backend

The frontend receives structured JSON.

Example:

```http
POST /api/v1/backtests
```

Request:

```json
{
  "asset": "BTC",
  "strategy": "SMA_CROSSOVER",
  "start_date": "2022-01-01",
  "end_date": "2026-01-01",
  "parameters": {
    "fast_window": 20,
    "slow_window": 100
  },
  "initial_capital": 100000,
  "transaction_cost": 0.001,
  "slippage": 0.0005
}
```

Response:

```json
{
  "backtest_id": "BT-10021",
  "status": "completed",
  "metrics": {
    "return": 0.184,
    "sharpe": 1.12,
    "volatility": 0.21,
    "max_drawdown": -0.16,
    "trades": 47
  }
}
```

The frontend simply renders this response.

---

# 24. Authentication and Security

The backend should handle:

```text
Authentication
Authorization
API Keys
Secrets
Rate Limiting
Input Validation
CORS
Audit Logging
```

External credentials must never reach the frontend.

For example:

```text
Zerodha API credentials
        ↓
Backend environment / secret store
        ↓
Zerodha Provider
```

Never:

```text
Frontend
   ↓
Zerodha API key
```

---

# 25. MCP Architecture

MCP should be an **optional AI integration layer**, not the primary application communication mechanism.

```text
                    AI Client
                       │
                    MCP Tools
                       │
                       ▼
                 Backend API
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
        Quant        Risk         Data
```

The frontend continues to use REST APIs.

This allows:

```text
Web UI
AI Assistant
External API Client
MCP Client
```

to all access the same backend capabilities.

---

# 26. Background Job Architecture

Some operations may take longer:

```text
Large backtest
Walk-forward
Parameter sweep
Monte Carlo
Quantum experiment
Portfolio optimization
```

Therefore:

```text
Frontend
   ↓
POST /backtests
   ↓
FastAPI
   ↓
Job Queue
   ↓
Worker
   ↓
Quant Engine
   ↓
Database
   ↓
GET /backtests/{id}
```

For the initial implementation:

```text
FastAPI Background Tasks
```

can be sufficient.

For larger workloads:

```text
Celery + Redis
```

can be introduced.

---

# 27. Observability

Backend should log:

```text
API requests
Execution time
Provider failures
Backtest failures
Model failures
Data-quality problems
Experiment IDs
```

Health endpoints:

```http
GET /health
GET /health/data
GET /health/database
GET /health/providers
GET /health/quantum
```

---

# 28. Testing Architecture

## Unit tests

```text
Indicators
Strategies
Risk calculations
Position sizing
Transaction costs
Portfolio accounting
```

## Integration tests

```text
API → Service → Database
API → Data Provider
API → Backtest Engine
API → ML Model
API → Quantum Service
```

## Regression tests

Maintain fixed historical datasets with known expected results.

Example:

```text
Input Dataset
+
Strategy
+
Parameters
=
Expected Equity Curve
```

This is particularly important for a financial application.

---

# 29. Recommended Repository Structure

```text
quant-platform/
│
├── backend/
│   ├── app/
│   │   ├── main.py
│   │   │
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── assets.py
│   │   │       ├── data.py
│   │   │       ├── indicators.py
│   │   │       ├── correlation.py
│   │   │       ├── strategies.py
│   │   │       ├── backtests.py
│   │   │       ├── robustness.py
│   │   │       ├── regimes.py
│   │   │       ├── risk.py
│   │   │       ├── portfolio.py
│   │   │       ├── quantum.py
│   │   │       └── ai.py
│   │   │
│   │   ├── core/
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── logging.py
│   │   │
│   │   ├── data/
│   │   │   ├── connectors/
│   │   │   ├── ingestion/
│   │   │   ├── validation/
│   │   │   ├── normalization/
│   │   │   └── models/
│   │   │
│   │   ├── quant/
│   │   │   ├── indicators/
│   │   │   ├── returns/
│   │   │   ├── volatility/
│   │   │   ├── correlation/
│   │   │   └── statistics/
│   │   │
│   │   ├── strategies/
│   │   │   ├── base.py
│   │   │   ├── sma.py
│   │   │   ├── ema.py
│   │   │   ├── momentum.py
│   │   │   ├── mean_reversion.py
│   │   │   └── buy_hold.py
│   │   │
│   │   ├── backtest/
│   │   │   ├── engine.py
│   │   │   ├── execution.py
│   │   │   ├── portfolio.py
│   │   │   ├── costs.py
│   │   │   └── benchmark.py
│   │   │
│   │   ├── robustness/
│   │   │   ├── walk_forward.py
│   │   │   ├── parameter_stress.py
│   │   │   ├── cost_stress.py
│   │   │   └── trust_report.py
│   │   │
│   │   ├── regimes/
│   │   │   ├── features.py
│   │   │   ├── kmeans.py
│   │   │   └── hmm.py
│   │   │
│   │   ├── risk/
│   │   │   ├── metrics.py
│   │   │   ├── var.py
│   │   │   ├── cvar.py
│   │   │   └── monte_carlo.py
│   │   │
│   │   ├── portfolio/
│   │   │   ├── optimizer.py
│   │   │   └── constraints.py
│   │   │
│   │   ├── quantum/
│   │   │   ├── regime.py
│   │   │   └── portfolio.py
│   │   │
│   │   └── ai/
│   │       ├── assistant.py
│   │       ├── tools.py
│   │       └── prompts.py
│   │
│   └── tests/
│
├── frontend/
│   ├── app/
│   ├── components/
│   ├── charts/
│   ├── api/
│   ├── hooks/
│   └── types/
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── parquet/
│
├── notebooks/
├── scripts/
├── docker/
├── .env.example
├── docker-compose.yml
├── requirements.txt
└── README.md
```

---

# 30. Final Technology Stack

| Layer                | Technology                             |
| -------------------- | -------------------------------------- |
| Frontend             | Next.js                                |
| Frontend language    | TypeScript                             |
| UI                   | Tailwind + shadcn/ui                   |
| Charts               | Plotly                                 |
| API                  | FastAPI                                |
| API schema           | Pydantic                               |
| Quant                | NumPy + Pandas                         |
| Scientific           | SciPy                                  |
| Statistics           | Statsmodels                            |
| Classical ML         | Scikit-learn                           |
| HMM                  | hmmlearn                               |
| Database             | PostgreSQL                             |
| Time series          | TimescaleDB                            |
| File analytics       | Parquet                                |
| Cache/queue          | Redis                                  |
| Background jobs      | FastAPI Tasks initially / Celery later |
| Backtesting          | Custom event-driven engine             |
| Quantum ML           | PennyLane                              |
| Quantum optimization | Qiskit                                 |
| LLM                  | API-based model with tool calling      |
| Testing              | Pytest                                 |
| Containerization     | Docker                                 |
| CI/CD                | GitHub Actions                         |
| API documentation    | OpenAPI / Swagger                      |

---

# 31. Final Functional Architecture

The complete functional pipeline is:

```text
                         USER
                           │
                           ▼
                    ┌─────────────┐
                    │  FRONTEND   │
                    └──────┬──────┘
                           │
                       REST API
                           │
                           ▼
                    ┌─────────────┐
                    │   FASTAPI   │
                    └──────┬──────┘
                           │
         ┌─────────────────┼──────────────────┐
         │                 │                  │
         ▼                 ▼                  ▼
   MARKET DATA        QUANT ENGINE       AI / ML ENGINE
         │                 │                  │
         │                 │          ┌───────┴────────┐
         │                 │          │                │
         │                 │       Classical        Quantum
         │                 │          ML             ML
         │                 │          │                │
         └────────┬────────┴──────────┴────────────────┘
                  │
                  ▼
             BACKTESTING
                  │
        ┌─────────┼─────────┐
        ▼         ▼         ▼
     Strategy   Risk    Robustness
        │         │         │
        └─────────┼─────────┘
                  ▼
             RESEARCH RESULT
                  │
        ┌─────────┼──────────┐
        ▼         ▼          ▼
    Dashboard   AI Report   Trust Report
```

---

# 32. Final Scope for Submission

### Core production system

**Data**

* Multi-asset market data
* Provider abstraction
* Data normalization
* Data quality validation

**Quant**

* SMA
* EMA
* Returns
* Volatility
* Sharpe
* Drawdown
* Correlation
* Rolling analytics

**Strategies**

* SMA crossover
* EMA trend
* Momentum
* Mean reversion
* Buy & Hold

**Backtesting**

* Initial capital
* Position sizing
* Execution delay
* Transaction costs
* Slippage
* Trade accounting
* Portfolio value

**Robustness**

* Walk-forward validation
* Parameter sensitivity
* Cost sensitivity
* Regime-specific performance

**ML**

* K-Means regime detection
* Optional HMM comparison

**Risk**

* VaR
* CVaR
* Monte Carlo
* Portfolio risk

**AI**

* Natural-language research
* Backtest explanation
* Strategy comparison
* Quantitative report generation

**Quantum**

* Experimental quantum regime detection
* Experimental quantum portfolio optimization

**Interface**

* Fully API-based backend
* Frontend communicates exclusively through backend APIs
* OpenAPI documentation
* No direct frontend-to-database/provider communication

---

## Final architectural principle

The platform should be positioned as:

> **An API-first quantitative financial intelligence platform that combines multi-asset analytics, realistic strategy backtesting, robustness analysis, machine-learning market regime detection, risk analytics, and optional experimental quantum optimization, with an AI research assistant operating entirely through deterministic backend services.**

The **core financial engine remains classical, deterministic, testable and reproducible**. AI adds interpretation and market-state modelling. Quantum computing is isolated as an experimental research capability. The frontend is completely decoupled from data providers, databases, ML models, quantum frameworks and financial calculations.

That gives you a submission architecture that is ambitious enough to demonstrate innovation, but still technically implementable without making the entire system dependent on experimental technology.
