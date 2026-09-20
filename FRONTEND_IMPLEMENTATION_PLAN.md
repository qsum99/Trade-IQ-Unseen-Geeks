# Frontend Implementation Plan — Quantitative Multi-Asset Financial Intelligence & Backtesting Platform

> Role: Frontend developer (hackathon team). Source of truth: `docs/` in
> `https://github.com/qsum99/quantum-hackthon.git` (`master`, commits `a3dba38`, `22c7ef5`).
> Analyzed: `arch.md`, `api.md`, `features.md`, `frontend_requirements.md`, `implementation_plan.md`, `math_eq.md`, `work_divide.md`.

## 1. Repo & Architecture Summary

- Repo currently contains **only `docs/`** — no `frontend/` or `backend/` code yet.
- Architecture (`docs/arch.md`): **backend-centric, API-first**.
  - Backend owns ALL business logic (FastAPI + Pydantic, NumPy/Pandas/SciPy, scikit-learn, PennyLane/Qiskit isolated as experimental).
  - **Frontend communicates ONLY via `REST /api/v1/`** — never touches PostgreSQL, NSE/Zerodha/Yahoo/Binance/FRED, ML models, Qiskit/PennyLane, or the LLM directly.
  - Frontend must NEVER calculate Sharpe/indicators, run Python, or contain financial business logic. It displays data, collects params, calls APIs, renders charts.
- Standard API envelope (`docs/api.md`): `{ success, data, meta, error }`, ISO-8601 dates, raw numbers from backend (frontend formats `%`/`₹`/`$`), `202 Accepted + GET /jobs/{id}` polling for long jobs (backtest sweeps, Monte Carlo, quantum).
- ~50 endpoints grouped: `auth, health, assets, data, indicators, correlation, strategies, backtests, robustness, regimes, risk, portfolio, quantum, ai, research, jobs`.
- Team split (`docs/work_divide.md`): Satish = data/quant/schemas (`market_api.py`, `formulas.py`), Samarth = strategies/backtesting/execution/costs, Somesh = risk/portfolio/validation/AI/quantum. Frontend consumes all three — freeze shared contracts on Day 0.

## 2. Tech Stack (exact, per docs — do not substitute)

| Layer    | Choice |
| -------- | ------ |
| Core     | Next.js (App Router) + TypeScript + React |
| UI       | Tailwind CSS + shadcn/ui + Radix UI + Lucide Icons |
| Server/API state | TanStack Query (React Query) + fetch/axios + Zod |
| Charts   | Plotly.js (`react-plotly.js`); TradingView Lightweight Charts optional only |
| Tables   | TanStack Table |
| Forms    | React Hook Form + Zod |
| UI state | Zustand (small global UI state only — NO giant Redux store) |
| Mocks    | MSW (Mock Service Worker) — build UI without waiting for backend |
| Config   | `NEXT_PUBLIC_API_BASE_URL` (never hardcode `localhost:8000` in components) |
| Fonts    | Inter/Geist + IBM Plex Mono for numbers (tabular numerals) |
| Themes   | Light `#F8F9FB/#FFFFFF/#E6E8EC`, Dark `#0B0D10/#111419/#242830`; semantic colors only (green=positive, red=negative, amber=warning, blue=info, purple=experimental) |

## 3. Page Map (14 pages, 10–12 in primary nav)

`Overview | Markets | Assets | Analytics | Correlation | Strategies | Backtesting | Robustness | Regimes | Risk & Portfolio | Quantum Lab | AI Research (+ Research, Settings in lower nav)`

Page → API mapping (`docs/api.md`):

| Page | Endpoints |
| ---- | --------- |
| Overview | `GET /health`, `GET /assets`, `POST /analytics/summary` |
| Markets | `GET /assets`, `GET /assets/{symbol}/history` |
| Asset Analysis | `history`, `analytics/summary`, indicator APIs |
| Quant Analytics | `POST /indicators/*` |
| Correlation | `POST /correlation/matrix`, `/correlation/rolling` |
| Strategies | `GET /strategies`, `POST /strategies/signals` |
| Backtesting (CENTERPIECE) | `POST /backtests`, `GET /backtests/{id}[/equity\|/trades\|/metrics\|/benchmark\|/trust-report]` |
| Robustness | `POST /robustness/{parameter-stress,cost-stress,walk-forward}` |
| Regimes | `POST /regimes/{detect,compare}`, `GET /regimes/{asset}` |
| Risk/Portfolio | `POST /risk/*`, `POST /portfolio/*` |
| Quantum Lab | `GET /quantum/status`, `POST /quantum/*` (badge EXPERIMENTAL) |
| AI Research | `POST /ai/{research,backtest,explain}` (answers must link back to backtest/regime artifacts) |
| Research | `GET/POST /research/experiments`, `POST /research/compare` |

## 4. Folder Architecture (create as scaffolded)

```text
frontend/
├── app/
│   ├── overview/ markets/ assets/ analytics/ correlation/
│   ├── strategies/ backtesting/ robustness/ regimes/
│   ├── risk/ portfolio/ quantum/ ai/ research/ settings/
├── src/
│   ├── api/        # client.ts, endpoints.ts, assets.ts, indicators.ts,
│   │               # backtests.ts, strategies.ts, regimes.ts, risk.ts,
│   │               # portfolio.ts, quantum.ts, ai.ts, research.ts, jobs.ts
│   ├── hooks/      # useAssets(), useBacktest(), useRegime(), ...
│   ├── types/      # generated from backend OpenAPI — single source of truth
│   ├── components/ # layout/ navigation/ charts/ tables/ forms/ cards/
│   │               # metrics/ backtest/ regime/ risk/ quantum/
│   ├── lib/        # formatting (numbers/dates), constants
│   ├── styles/     # theme tokens
│   └── mocks/      # MSW handlers mirroring api.md example payloads
└── .env.local      # NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

Shared reusable components first (don't rebuild per page):
`MetricCard, ChartContainer, DateRangePicker, AssetSelector, StrategySelector, DataTable, StatusBadge, RegimeBadge, BacktestConfigPanel, BacktestMetricGrid, EquityCurve, DrawdownChart, CorrelationHeatmap, ParameterHeatmap, RiskDistribution`.

## 5. Non-Negotiable Rules

1. One central `apiClient<T>(endpoint, options)` — components never build URLs.
2. Base URL only via `NEXT_PUBLIC_API_BASE_URL`.
3. TS types generated from backend OpenAPI; MSW mocks match the same shapes → swapping mock→real backend = config change only.
4. No financial math in UI (no Sharpe/SMA in components).
5. Numbers: backend returns `0.1824`, UI renders `18.24%`. Dates: backend ISO, UI formats.
6. Long ops: `POST → 202 {job_id} → poll GET /jobs/{id} → render` with staged progress UI (`Loading data ✓ → Signals ✓ → Execution ● → Metrics ○`).
7. Every backtest result shows execution assumptions (`Next Bar, cost 0.10%, slippage 0.05%`) + Trust Report (`✓ no look-ahead, ✓ costs applied, ⚠ limited OOS…`) + disclaimer (research tool, not guaranteed returns).

## 6. Phased Build (hackathon order)

- **Phase 0 (with backend, 2–3h):** freeze OpenAPI schemas, envelope, error codes, pagination, date/number conventions.
- **Phase 1 — shell + system:** Next.js scaffold, Tailwind+shadcn, theme tokens, app shell (sidebar 240–260px / collapsed 68–72px, topbar search `⌘K` stub), `apiClient`, TanStack Query provider, MSW with 5 core mocks (assets, history, analytics/summary, backtest result, correlation matrix).
- **Phase 2 — hero flow (MVP demo):** Overview → Asset Analysis (candles + SMA/EMA + volume tabs) → **Backtest workspace**: left config panel → equity curve → strategy-vs-buy&hold → trades table → trust report.
- **Phase 3:** Correlation heatmap + rolling, Robustness tabs (walk-forward / param heatmap / cost stress), Regimes timeline + K-Means/HMM/quantum compare, Risk/Portfolio/Monte Carlo tabs.
- **Phase 4:** Quantum Lab (honest classical-vs-quantum compare, never "quantum = better"), AI Research (grounded answers + artifact links), Research history, Settings (appearance, defaults). Then responsive/tablet-mobile condensation, skeletons/empty/error states, keyboard nav, WCAG 2.2 AA, chart interactions (tooltip/crosshair/zoom/range).

## 7. Definition of Done

All pages + light/dark + responsive + design system + API client + env-configured base URL + OpenAPI types + MSW + loading/empty/error/skeleton + validated forms + keyboard nav + financial formatting + zero direct DB/provider access + zero hardcoded data/URLs + backend swappable by config change.

## 8. Git Workflow

```bash
# origin: https://github.com/qsum99/quantum-hackthon.git (branch: master)
git checkout -b feature/frontend-shell
git add frontend FRONTEND_IMPLEMENTATION_PLAN.md
git commit -m "feat(frontend): shell + api client + mocks"
git push -u origin feature/frontend-shell
# branches: main ← develop ← feature/satish-quant-data | feature/samarth-backtesting | feature/somesh-risk-quantum | feature/frontend-*
```

## 9. Immediate Checklist (you, frontend)

- [ ] Scaffold app + shadcn + deps (this session)
- [ ] `api/client.ts` + `endpoints.ts` + env
- [ ] MSW handlers for assets/history/summary/backtest/correlation
- [ ] Shell + Overview + Asset page against mocks
- [ ] Backtest workspace end-to-end against mocks
- [ ] Get OpenAPI URL from backend team → generate `src/types/` → replace mocks
