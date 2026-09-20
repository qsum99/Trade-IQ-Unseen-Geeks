# Frontend Design & Implementation Specification

This specification is intended to be handed directly to the frontend designer/developer. The frontend should be designed as a **premium quantitative-finance research application**, not as a generic admin dashboard.

The backend integration should be planned from day one through a single API client layer, with **no hardcoded financial data in UI components**.

---

# 1. Frontend Product Direction

## Product character

The interface should feel:

* Clean
* Minimal
* Premium
* Analytical
* Trustworthy
* Professional
* Data-dense without feeling crowded
* Fast
* Modern
* Institutional-finance inspired
* Accessible to both technical and non-technical users

Think:

```text
Bloomberg-level information density
+
Linear-level cleanliness
+
Stripe-level polish
+
Modern quantitative-research tooling
```

Do **not** make it look like:

* a crypto trading app
* a gaming dashboard
* a generic Bootstrap admin panel
* a neon "AI" interface
* an overly animated SaaS landing page

---

# 2. Recommended Frontend Technology

## Core

```text
Next.js
TypeScript
React
```

## UI

```text
Tailwind CSS
shadcn/ui
Radix UI
Lucide Icons
```

## Data

```text
TanStack Query
Axios or native fetch
Zod
```

## Charts

```text
Plotly.js
```

Optional:

```text
TradingView Lightweight Charts
```

## Tables

```text
TanStack Table
```

## Forms

```text
React Hook Form
Zod
```

## State

Use:

```text
TanStack Query → server/API state
Zustand → small amount of global UI state
```

Do **not** put all backend data into a huge global Redux store.

---

# 3. Overall Page Structure

I recommend **12 primary pages**, with several nested views/drawers rather than creating 25+ separate pages.

```text
1. Overview
2. Markets
3. Asset Analysis
4. Quant Analytics
5. Correlation
6. Strategies
7. Backtesting
8. Robustness
9. Market Regimes
10. Risk & Portfolio
11. Quantum Lab
12. AI Research
```

Additionally:

```text
13. Research / Experiments
14. Settings
```

So:

### **14 total application pages**

But the main navigation should expose approximately **10–12 primary destinations**, while Research and Settings can sit in the lower navigation.

---

# 4. Global Application Layout

Every authenticated application page should use the same shell.

```text
┌──────────────────────────────────────────────────────────────────────┐
│ Logo        Search / Command Center              Notifications  User │
├──────────────┬───────────────────────────────────────────────────────┤
│              │                                                       │
│ Overview     │                                                       │
│ Markets      │                  PAGE CONTENT                         │
│ Assets       │                                                       │
│ Analytics    │                                                       │
│ Strategies   │                                                       │
│ Backtesting  │                                                       │
│ Robustness   │                                                       │
│ Regimes      │                                                       │
│ Risk         │                                                       │
│ Portfolio    │                                                       │
│ Quantum Lab  │                                                       │
│ AI Research  │                                                       │
│              │                                                       │
│──────────────│                                                       │
│ Research     │                                                       │
│ Settings     │                                                       │
└──────────────┴───────────────────────────────────────────────────────┘
```

---

# 5. Sidebar Design

The sidebar should be:

### Desktop

```text
Width: 240–260px
```

### Collapsed

```text
Width: 68–72px
```

### Navigation

```text
OVERVIEW

Markets
Assets
Analytics
Correlation

RESEARCH

Strategies
Backtesting
Robustness
Regimes
Risk & Portfolio

EXPERIMENTAL

Quantum Lab
AI Research

WORKSPACE

Research
Settings
```

Use section labels rather than showing 15 icons with no grouping.

---

# 6. Top Navigation

Top bar:

```text
┌───────────────────────────────────────────────────────────────┐
│ ☰  RegimeIQ     Search assets, strategies...    ● API  Avatar │
└───────────────────────────────────────────────────────────────┘
```

### Components

#### Global search

Should search:

* assets
* strategies
* backtests
* experiments
* saved research
* reports

Example:

```text
Search...

⌘ K
```

This can eventually become a command palette.

---

# 7. Page 1: Overview Dashboard

This is the most important page.

## Purpose

Give the user a quick understanding of:

* market state
* asset performance
* risk
* active research
* recent backtests
* regime conditions

---

## Layout

```text
┌──────────────────────────────────────────────────────────────┐
│ Good afternoon                         19 Sep 2026            │
│ Quantitative Market Overview                                  │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Market Regime      Portfolio Risk       Best Asset           │
│  HIGH VOL           Moderate             BTC +12.4%            │
│                                                              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│              Market Performance                               │
│        [ multi-asset performance chart ]                      │
│                                                              │
├───────────────────────────────┬──────────────────────────────┤
│ Asset Snapshot                │ Market Regime                 │
│ BTC     +12.4%   42% vol      │ Current: High Volatility     │
│ GOLD     +4.1%   16% vol      │ Confidence: 81%              │
│ NVDA    +18.2%   37% vol      │                              │
├───────────────────────────────┼──────────────────────────────┤
│ Strategy Performance          │ Recent Research               │
│ SMA      +14.2%               │ EMA BTC Backtest             │
│ Momentum +19.4%               │ Portfolio Experiment         │
│ MeanRev   +8.1%               │ Regime Analysis              │
└───────────────────────────────┴──────────────────────────────┘
```

---

# 8. KPI Cards

Keep KPI cards very minimal.

Example:

```text
BTC
$67,420
+2.41%
```

Don't use huge cards containing five metrics.

Use:

```text
Value
Change
Small secondary metric
Sparkline
```

---

# 9. Page 2: Markets

This is the asset discovery page.

## Layout

```text
Markets

[Search asset...] [Asset Class ▼] [Exchange ▼]

──────────────────────────────────────────────

Equities
┌────────┬─────────┬────────┬────────┬────────┐
│ Asset  │ Price   │ 1D     │ 1M     │ Vol    │
├────────┼─────────┼────────┼────────┼────────┤
│ NVDA   │ ...     │ ...    │ ...    │ ...    │
│ RELI   │ ...     │ ...    │ ...    │ ...    │
└────────┴─────────┴────────┴────────┴────────┘

Crypto

Commodities

Indices

Macro
```

---

# 10. Page 3: Asset Analysis

This should be one of the most visually strong pages.

## Header

```text
BTC / USD
Bitcoin

$67,420.20     +2.41%

[1D] [1W] [1M] [6M] [1Y] [5Y] [MAX]
```

---

## Main chart

```text
┌──────────────────────────────────────────────────────────┐
│                                                          │
│                    Candlestick Chart                     │
│                                                          │
│  ─── SMA 20                                             │
│  ─── SMA 100                                            │
│                                                          │
└──────────────────────────────────────────────────────────┘
```

Below:

```text
Volume
```

---

## Tabs

```text
Overview
Indicators
Returns
Volatility
Drawdown
Regimes
```

This avoids making the page vertically enormous.

---

# 11. Page 4: Quant Analytics

Dedicated quantitative analysis workspace.

## Layout

```text
Quant Analytics

Asset: BTC
Period: 2020–2026

┌─────────────┬─────────────┬─────────────┬─────────────┐
│ Return      │ Volatility  │ Sharpe      │ Drawdown    │
│ +82.4%      │ 41.2%       │ 1.42        │ -31.5%      │
└─────────────┴─────────────┴─────────────┴─────────────┘

Performance
[ chart ]

Volatility
[ chart ]

Drawdown
[ chart ]
```

Allow users to toggle:

```text
Daily
Weekly
Monthly
Rolling
Annualized
```

---

# 12. Page 5: Correlation

This page should feel like a research tool.

## Main visualization

Large heatmap:

```text
             BTC    GOLD   NVDA   NIFTY
BTC          1.00   .21    .36     .41
GOLD         .21    1.00  -.04     .08
NVDA         .36   -.04    1.00     .54
NIFTY        .41    .08     .54     1.00
```

Use subtle cells and excellent typography.

---

## Below

```text
Rolling Correlation

BTC ↔ GOLD
[ time-series chart ]

BTC ↔ NVDA
[ time-series chart ]
```

Controls:

```text
Correlation Method
Window
Assets
Date Range
```

---

# 13. Page 6: Strategies

## Layout

```text
Strategies

[ Create Strategy ]

┌─────────────────────────────────────────────────────┐
│ SMA Crossover                                      │
│ Trend following                                   │
│                                                    │
│ Fast: 20    Slow: 100                              │
│                                                    │
│ [ View ] [ Backtest ]                              │
└─────────────────────────────────────────────────────┘
```

Cards should be compact.

Available:

```text
SMA Crossover
EMA Trend
Momentum
Mean Reversion
Buy & Hold
Regime Adaptive
```

---

# 14. Strategy Detail

Clicking a strategy opens:

```text
Strategy
SMA Crossover

Description
Parameters
Signals
Historical Performance
Compatible Assets
```

Then:

```text
[ Backtest Strategy ]
```

---

# 15. Page 7: Backtesting

This should be a **research workspace**, not just a form.

## Left configuration panel

```text
BACKTEST

Asset
[ BTC ▼ ]

Strategy
[ SMA Crossover ▼ ]

Period
[ 2020 ] → [ 2026 ]

Initial Capital
[ ₹100,000 ]

Fast Window
[ 20 ]

Slow Window
[ 100 ]

Transaction Cost
[ 0.10% ]

Slippage
[ 0.05% ]

Execution
[ Next Bar ]

[ RUN BACKTEST ]
```

---

## Right side

Before execution:

```text
Configure your experiment
```

After execution:

```text
Results
```

---

# 16. Backtest Result Layout

```text
SMA Crossover / BTC

Return       Sharpe       Volatility       Drawdown
+84.2%       1.31         32.4%            -18.4%

──────────────────────────────────────────────

Equity Curve
[ large chart ]

──────────────────────────────────────────────

Strategy vs Buy & Hold
[ comparison chart ]

──────────────────────────────────────────────

Trades
[ table ]

──────────────────────────────────────────────

Backtest Trust
✓ No look-ahead
✓ No leakage
✓ Costs applied
✓ Walk-forward available
```

---

# 17. Page 8: Robustness

This should visually communicate:

> "Does this strategy actually hold up?"

## Tabs

```text
Walk Forward
Parameter Sensitivity
Cost Stress
Regime Performance
```

---

## Walk-forward

```text
Training
████████████

Validation
████

Testing
████
```

Then:

```text
Window 1
Window 2
Window 3
Window 4
```

---

# 18. Parameter Sensitivity

Heatmap:

```text
       Slow Window
       50  75 100 125 150
Fast
10     ...
20     ...
30     ...
40     ...
50     ...
```

Allow metric selector:

```text
Return
Sharpe
Drawdown
```

This is an excellent visual feature.

---

# 19. Cost Stress

Chart:

```text
Performance
│\
│ \
│  \
│   \
│    \____
└──────────────
  Cost →
```

Show:

```text
0%
0.05%
0.10%
0.25%
0.50%
1%
```

---

# 20. Page 9: Market Regimes

This should feel visually different from the normal dashboard.

## Header

```text
Market Regime Intelligence

BTC

Current Regime
HIGH VOLATILITY

Confidence
81%

Detected by
K-Means
```

---

## Timeline

```text
2022     2023     2024     2025     2026

████████  Bull
        ████████  Bear
                ███ High Vol
                    █████ Low Vol
```

Use subtle regime backgrounds.

---

## Model comparison

```text
Model             Regime       Confidence
K-Means           High Vol     81%
HMM               High Vol     76%
Quantum VQC       High Vol     72%
```

Do not visually imply that one model is superior simply through styling.

---

# 21. Regime Performance

```text
Strategy Performance by Regime

              Bull   Bear   High Vol   Low Vol
SMA           +18%   -7%     -14%       +8%
EMA           +21%   -4%     -11%       +11%
Momentum      +29%   -12%    -20%       +14%
Mean Rev       +6%   +5%     +13%       +2%
```

---

# 22. Page 10: Risk & Portfolio

I recommend combining Risk and Portfolio into one workspace with tabs.

```text
Risk & Portfolio

[ Risk ] [ Portfolio ] [ Monte Carlo ]
```

---

## Risk

```text
VaR
₹12,420

CVaR
₹18,720

Volatility
24.4%

Maximum Drawdown
-17.8%
```

Then:

```text
Risk Distribution
[ chart ]
```

---

# 23. Monte Carlo

```text
Monte Carlo Simulation

10,000 simulations

                 ╭──────╮
              ╭──╯      ╰──╮
          ╭───╯             ╰───╮
──────────┴───────────────────────

5th percentile
Median
95th percentile
```

Controls:

```text
Number of simulations
Horizon
Confidence
Portfolio
```

---

# 24. Portfolio

```text
Portfolio Builder

Assets
☑ BTC
☑ GOLD
☑ NVDA
☑ NIFTY

Optimization
○ Minimum Volatility
○ Mean Variance
○ Risk Parity
○ Quantum Experiment

[ OPTIMIZE ]
```

Results:

```text
BTC       35%
GOLD      25%
NVDA      25%
NIFTY     15%
```

---

# 25. Page 11: Quantum Lab

This should clearly communicate that quantum functionality is experimental.

Don't make it look like the whole platform depends on quantum computing.

Header:

```text
Quantum Lab

Experimental quantitative research
```

Badge:

```text
EXPERIMENTAL
```

---

## Experiments

```text
┌──────────────────────────────┐
│ Quantum Regime Detection     │
│ PennyLane / VQC              │
│                              │
│ [ Run Experiment ]           │
└──────────────────────────────┘

┌──────────────────────────────┐
│ Quantum Portfolio Optimizer  │
│ Qiskit / QAOA                │
│                              │
│ [ Run Experiment ]           │
└──────────────────────────────┘
```

---

## Experiment result

```text
Classical
K-Means
Sharpe: 1.21

Quantum
VQC
Sharpe: 1.17

Execution Time
Classical: 1.2s
Quantum simulation: 8.4s
```

This is much more credible than displaying:

> "Quantum = better"

---

# 26. Page 12: AI Research

This should feel like a research assistant, not a generic chatbot.

## Layout

```text
┌───────────────────────────────────────────────────────────────┐
│ AI Research Assistant                                         │
│                                                               │
│ Ask questions about your market research                      │
│                                                               │
│ ┌───────────────────────────────────────────────────────────┐ │
│ │ Compare BTC momentum and mean reversion during high-vol   │ │
│ │ periods.                                                  │ │
│ └───────────────────────────────────────────────────────────┘ │
│                                                               │
│                         [ Analyze ]                            │
└───────────────────────────────────────────────────────────────┘
```

---

## Result

```text
Research Summary

The momentum strategy generated...

Evidence
• Backtest ID: BT-1029
• Period: 2020–2026
• Regime: High Volatility
• Trades: 82

[ View Backtest ]
[ View Regime Analysis ]
```

The AI should always expose links back to the underlying quantitative result.

---

# 27. Research Page

This is essentially the user's research history.

```text
Research

Experiments
Saved Backtests
Saved Comparisons
Reports
```

Table:

```text
Experiment       Asset    Strategy      Date       Status
────────────────────────────────────────────────────────
BTC SMA          BTC      SMA           Sep 19     Complete
NVDA EMA         NVDA     EMA           Sep 18     Complete
Portfolio Test   Multi    Risk Parity   Sep 18     Complete
```

---

# 28. Settings Page

Sections:

```text
Profile
Appearance
Data Sources
API Preferences
Notifications
Security
Research Defaults
```

Appearance:

```text
Light
Dark
System
```

---

# 29. Design System

The designer should establish a proper design system before designing pages.

## Typography

Recommended:

### Primary

**Inter**

or

**Geist**

### Numeric/data font

Consider:

**IBM Plex Mono**

for:

* prices
* percentages
* API IDs
* experiment IDs
* timestamps

Example:

```text
$67,420.20
+2.41%
1.42
-18.4%
```

Use tabular numerals.

---

# 30. Color System

Keep the interface largely neutral.

### Light

```text
Background       #F8F9FB
Surface          #FFFFFF
Border           #E6E8EC
Primary Text     #111318
Secondary Text   #667085
```

### Dark

```text
Background       #0B0D10
Surface          #111419
Border           #242830
Primary Text     #F5F7FA
Secondary Text   #98A2B3
```

Don't overuse color.

---

# 31. Semantic Colors

Only use strong colors for meaning.

```text
Positive    Green
Negative    Red
Warning     Amber
Information Blue
Experimental Purple
```

Avoid gradients everywhere.

Avoid neon.

Avoid rainbow charts.

---

# 32. Charts

Charts should be:

* minimal
* thin
* readable
* interactive
* consistent

Avoid:

```text
3D charts
heavy gridlines
large legends
unnecessary gradients
decorative chart backgrounds
```

Use:

```text
Tooltip
Crosshair
Zoom
Range selection
Legend toggles
```

---

# 33. Dark Theme

Dark mode should not simply invert colors.

Use:

```text
#0B0D10
```

for the background and slightly lighter surfaces.

Example:

```text
Background
    #0B0D10

Card
    #111419

Elevated card
    #161A20

Border
    #242830
```

Charts should also adapt.

---

# 34. Light Theme

Use:

```text
Background
    #F8F9FB

Card
    #FFFFFF

Border
    #E6E8EC
```

Avoid pure white everywhere.

---

# 35. Cards

Don't make everything a card.

Use cards only for:

* KPIs
* independent analytical modules
* experiment summaries
* configuration sections

Charts can sit directly on the page.

This makes the application feel more premium.

---

# 36. Spacing System

Use an 8-point spacing system.

```text
4px
8px
12px
16px
24px
32px
40px
48px
64px
```

Default:

```text
Page padding: 32px
Section gap: 32px
Card padding: 20–24px
```

---

# 37. Responsive Design

### Desktop

Primary experience:

```text
1440px+
```

### Laptop

```text
1280px
```

### Tablet

```text
768–1024px
```

### Mobile

Don't try to reproduce the full desktop dashboard.

Use:

```text
Bottom navigation
Condensed charts
Stacked KPI cards
Horizontal scrolling tables
```

The application should remain usable, but desktop is the primary quantitative research experience.

---

# 38. Loading States

Never show blank screens.

Use:

```text
Skeleton
```

For example:

```text
┌──────────────────────────────┐
│ ████████████████             │
│ ████████                     │
│                              │
│ ████████████████████████     │
└──────────────────────────────┘
```

For long backtests:

```text
Running Backtest...

Loading historical data      ✓
Generating signals           ✓
Running execution            ✓
Calculating metrics          ●
Generating report            ○
```

---

# 39. Empty States

Example:

```text
No backtests yet

Run your first strategy backtest
to begin analyzing performance.

[ Create Backtest ]
```

Not:

```text
No data.
```

---

# 40. Error States

Example:

```text
Unable to load market data

The selected data provider did not
respond successfully.

[ Retry ]

Provider status
NSE       ● Operational
Yahoo     ● Operational
Binance   ● Operational
```

---

# 41. API Integration Architecture

This should be explicitly given to the frontend developer.

Create:

```text
frontend/
└── src/
    ├── api/
    │   ├── client.ts
    │   ├── endpoints.ts
    │   ├── assets.ts
    │   ├── indicators.ts
    │   ├── backtests.ts
    │   ├── strategies.ts
    │   ├── regimes.ts
    │   ├── risk.ts
    │   ├── portfolio.ts
    │   ├── quantum.ts
    │   ├── ai.ts
    │   └── research.ts
```

---

# 42. API Base URL

Do not hardcode:

```text
http://localhost:8000
```

inside components.

Use:

```env
NEXT_PUBLIC_API_BASE_URL=
```

Example:

```env
NEXT_PUBLIC_API_BASE_URL=https://api.yourdomain.com/api/v1
```

Local:

```env
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api/v1
```

---

# 43. API Client

Create one centralized client:

```typescript
const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL;

export async function apiClient<T>(
  endpoint: string,
  options?: RequestInit
): Promise<T> {
  const response = await fetch(
    `${API_BASE_URL}${endpoint}`,
    {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options?.headers,
      },
    }
  );

  if (!response.ok) {
    throw new Error("API request failed");
  }

  return response.json();
}
```

Then components never construct URLs themselves.

---

# 44. React Query Structure

Example:

```text
useAssets()
useAssetHistory()
useIndicators()
useCorrelation()
useBacktest()
useBacktestMetrics()
useRegime()
useRisk()
usePortfolio()
useQuantumExperiment()
useResearch()
```

This gives you:

* caching
* refetching
* loading states
* error states
* stale data management

---

# 45. API Mocking Before Backend Is Ready

This is particularly important for your team.

The frontend developer should **not wait for the backend to be completed**.

Use:

```text
MSW
```

Mock Service Worker.

Flow:

```text
Frontend
    ↓
API client
    ↓
MSW mock API
    ↓
Fake JSON
```

When backend becomes available:

```text
Frontend
    ↓
API client
    ↓
Real FastAPI
```

No component rewrite required.

---

# 46. Define API Contracts First

Before backend implementation finishes, establish:

```text
OpenAPI specification
```

Frontend can then generate TypeScript types.

For example:

```text
Backend OpenAPI
      ↓
TypeScript API Types
      ↓
Frontend
```

This is one of the most important recommendations for the team.

---

# 47. Frontend Folder Architecture

```text
frontend/
│
├── app/
│   ├── overview/
│   ├── markets/
│   ├── assets/
│   ├── analytics/
│   ├── correlation/
│   ├── strategies/
│   ├── backtesting/
│   ├── robustness/
│   ├── regimes/
│   ├── risk/
│   ├── portfolio/
│   ├── quantum/
│   ├── ai/
│   ├── research/
│   └── settings/
│
├── components/
│   ├── layout/
│   ├── navigation/
│   ├── charts/
│   ├── tables/
│   ├── forms/
│   ├── cards/
│   ├── metrics/
│   ├── backtest/
│   ├── regime/
│   ├── risk/
│   └── quantum/
│
├── api/
│
├── hooks/
│
├── types/
│
├── lib/
│
├── styles/
│
└── mocks/
```

---

# 48. Component Design Rules

Build reusable components first.

Examples:

```text
MetricCard
ChartContainer
DateRangePicker
AssetSelector
StrategySelector
DataTable
StatusBadge
ConfidenceBadge
RegimeBadge
BacktestConfigPanel
BacktestMetricGrid
EquityCurve
DrawdownChart
CorrelationHeatmap
ParameterHeatmap
RiskDistribution
```

Don't create a separate custom chart component from scratch for every page.

---

# 49. Design References

For visual direction, the designer can study:

### Linear

For:

* spacing
* typography
* navigation
* dark mode
* command palette
* minimal interfaces

[Linear](https://linear.app/?utm_source=chatgpt.com)

### Stripe

For:

* premium visual hierarchy
* typography
* restrained color
* polished interaction patterns

[Stripe](https://stripe.com/?utm_source=chatgpt.com)

### Vercel

For:

* minimal design
* dark/light themes
* developer-oriented UI
* typography

[Vercel](https://vercel.com/?utm_source=chatgpt.com)

### TradingView

For:

* financial chart interaction
* asset analysis
* technical indicators
* time-range controls

[TradingView](https://www.tradingview.com/?utm_source=chatgpt.com)

### Bloomberg Terminal

Use primarily as inspiration for **information hierarchy and analytical density**, not visual styling.

---

# 50. Design Principles to Give the Designer

Give them these rules directly:

### 1. Information first

Every visual element must help the user understand the market or research result.

### 2. No unnecessary decoration

No:

* floating blobs
* excessive gradients
* neon glows
* meaningless animations
* giant illustrations inside analytics pages

### 3. Use whitespace strategically

Premium doesn't mean empty.

It means **organized density**.

### 4. Consistent numbers

Always align:

```text
$67,420.20
+2.41%
1.42
-18.42%
```

using tabular numerals.

### 5. Consistent chart language

The same asset should have the same visual identity throughout the application.

### 6. Color has meaning

Don't use green simply because it "looks nice."

Green means positive.

Red means negative.

Amber means warning.

Purple means experimental/quantum.

---

# 51. Micro-interactions

Use subtle interactions:

```text
Hover
Tooltip
Chart crosshair
Tab transition
Button loading
Skeleton
Toast
Drawer
Modal
```

Avoid:

```text
3D transitions
large page animations
constant motion
parallax
```

The product should feel fast.

---

# 52. Accessibility Requirements

Minimum:

```text
WCAG 2.2 AA-oriented design
```

Include:

* keyboard navigation
* visible focus states
* sufficient contrast
* accessible form labels
* semantic HTML
* screen-reader labels
* don't use color as the only indicator
* keyboard-accessible charts where practical

For example:

Don't show only:

```text
● ● ●
```

Use:

```text
High Volatility
```

as text as well.

---

# 53. Important Financial UX Requirements

The designer should pay special attention to:

### Numbers

Use consistent:

```text
₹
$
%
bps
```

### Date ranges

Always show:

```text
Start → End
```

### Data source

Show where useful:

```text
Source: NSE
Updated: 14:32
```

### Model

For regime results:

```text
Model: K-Means
```

For quantum:

```text
Model: VQC
Experimental
```

### Backtest

Show:

```text
Execution: Next Bar
Transaction Cost: 0.10%
Slippage: 0.05%
```

This prevents users from misunderstanding the result.

---

# 54. Design the Application Around Three Primary User Actions

The entire interface should make these three actions extremely easy:

### 1. Analyze an asset

```text
Asset → Indicators → Risk → Regime
```

### 2. Test a strategy

```text
Strategy → Backtest → Robustness → Compare
```

### 3. Research a portfolio

```text
Assets → Correlation → Risk → Optimization → Monte Carlo
```

The AI assistant should be able to initiate any of these flows through the backend APIs.

---

# 55. Most Important Page: Backtest Workspace

If development time becomes limited, prioritize:

```text
Backtest configuration
        ↓
Results
        ↓
Equity curve
        ↓
Benchmark comparison
        ↓
Trade history
        ↓
Robustness
        ↓
Trust report
```

That should become the centerpiece of the application.

---

# 56. Recommended Initial Design Sequence

Tell the designer to work in this order:

```text
1. Design system
2. Global application shell
3. Sidebar
4. Top navigation
5. Overview
6. Asset analysis
7. Backtesting workspace
8. Backtest results
9. Robustness
10. Regime analysis
11. Risk/Portfolio
12. Correlation
13. Strategies
14. Quantum Lab
15. AI Research
16. Research
17. Settings
18. Responsive states
19. Loading/error/empty states
20. Dark/light theme
```

Don't design 14 pages independently.

Build the design system first and derive the pages from it.

---

# 57. Final Frontend Navigation

The final navigation I would give the designer is:

```text
┌─────────────────────────────┐
│ LOGO                        │
│                             │
│ OVERVIEW                    │
│   Overview                  │
│                             │
│ MARKETS                     │
│   Markets                   │
│   Assets                    │
│   Analytics                 │
│   Correlation               │
│                             │
│ RESEARCH                    │
│   Strategies                │
│   Backtesting               │
│   Robustness                │
│   Regimes                   │
│   Risk & Portfolio          │
│                             │
│ EXPERIMENTAL                │
│   Quantum Lab               │
│   AI Research               │
│                             │
│ WORKSPACE                   │
│   Research                  │
│   Settings                 │
└─────────────────────────────┘
```

---

# 58. Frontend Definition of Done

The frontend should not be considered complete until:

```text
✓ All pages designed
✓ Light theme
✓ Dark theme
✓ Responsive layout
✓ Design system established
✓ Component library established
✓ API client implemented
✓ API base URL configurable
✓ OpenAPI-compatible types
✓ MSW mock API available
✓ Loading states
✓ Empty states
✓ Error states
✓ Skeleton states
✓ Form validation
✓ Accessible navigation
✓ Keyboard navigation
✓ Chart interactions
✓ Consistent financial number formatting
✓ Consistent date/time formatting
✓ No direct database access
✓ No direct market-provider access
✓ No hardcoded backend URLs
✓ No financial calculations inside UI
✓ No hardcoded production market data
✓ Backend can be connected by changing API configuration
```

## Final frontend philosophy

**The frontend should feel like a professional quantitative research workstation, not a collection of dashboards.**

The user's mental flow should always be:

**Explore → Analyze → Experiment → Validate → Understand.**

And technically:

**Next.js → API Client → FastAPI → Services → Quant/ML/AI/Quantum → Database/Data Providers.**

That separation should be treated as a non-negotiable architectural requirement from the first Figma design through the final implementation.
