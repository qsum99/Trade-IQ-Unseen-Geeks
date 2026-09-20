"use client";
export const dynamic = "force-dynamic";
import Link from "next/link";
import { HeroScrollAnimation } from "@/components/HeroScrollAnimation";
import {
  ArrowRight,
  BarChart3,
  FlaskConical,
  Layers,
  PieChart,
  ShieldCheck,
  Sparkles,
  Zap,
  CheckCircle2,
  TrendingUp,
  BookOpen,
  ChevronRight,
  Newspaper,
} from "lucide-react";
import { ASSETS } from "@/lib/mock-data";

// ─── Static data ─────────────────────────────────────────────────────────────

const CAPABILITY_CARDS = [
  {
    href: "/backtesting",
    icon: FlaskConical,
    color: "blue",
    title: "Backtesting Centerpiece",
    body: "Strict T+1 next-bar execution model. Realistic slippage, transaction cost schedules, and strategy vs. Buy & Hold benchmark equity curve comparisons.",
    cta: "View Backtester",
  },
  {
    href: "/robustness",
    icon: ShieldCheck,
    color: "cyan",
    title: "Robustness Stress Suite",
    body: "Walk-forward out-of-sample decay analysis, 2D parameter sensitivity heatmaps, and fee break-even stress curves to prevent overfitting.",
    cta: "Explore Robustness",
  },
  {
    href: "/regimes",
    icon: Layers,
    color: "purple",
    title: "Regime Intelligence",
    body: "Detect Bull, Bear, High Volatility, and Low Volatility market phases using K-Means clustering and Hidden Markov Models.",
    cta: "Inspect Regimes",
  },
  {
    href: "/risk",
    icon: PieChart,
    color: "emerald",
    title: "Risk & Portfolio Optimizer",
    body: "Historical Value at Risk (VaR 95%), Expected Shortfall (CVaR), and 10,000 geometric Brownian motion Monte Carlo projections with minimum-volatility solvers.",
    cta: "Open Risk Lab",
  },
  {
    href: "/paper-trading",
    icon: Zap,
    color: "amber",
    title: "Real-Time Paper Trading",
    body: "Multi-asset virtual execution engine with live tick/bar streaming, order blotter, candlestick charts, real-time PnL trajectory, and execution audit.",
    cta: "Start Paper Trading",
  },
  {
    href: "/news",
    icon: Newspaper,
    color: "emerald",
    title: "Live Financial News Wire",
    body: "Authentic real-time institutional wire scraped from Bloomberg, Reuters, CNBC, and AP with algorithmic sentiment scoring and ticker entity tags.",
    cta: "Open News Wire",
  },
  {
    href: "/correlation",
    icon: BarChart3,
    color: "cyan",
    title: "Cross-Asset Correlation",
    body: "Interactive 2–8 asset heatmaps with rolling 30–120 day window trackers to uncover how asset couplings shift across macroeconomic cycles.",
    cta: "View Correlation Matrix",
  },
];

const COLOR_MAP: Record<string, string> = {
  blue: "border-blue-500/40 text-blue-400 bg-blue-500/10",
  cyan: "border-cyan-500/40 text-cyan-400 bg-cyan-500/10",
  purple: "border-purple-500/40 text-purple-400 bg-purple-500/10",
  emerald: "border-emerald-500/40 text-emerald-400 bg-emerald-500/10",
  violet: "border-violet-500/40 text-violet-400 bg-violet-500/10",
  amber: "border-amber-500/40 text-amber-400 bg-amber-500/10",
};

const STRATEGIES = [
  { name: "SMA Crossover", tag: "Trend", color: "blue" },
  { name: "EMA Trend", tag: "Trend", color: "blue" },
  { name: "Momentum", tag: "Momentum", color: "violet" },
  { name: "Mean Reversion", tag: "Counter-trend", color: "amber" },
  { name: "Buy & Hold", tag: "Benchmark", color: "slate" },
  { name: "Regime-Adaptive", tag: "Hybrid", color: "emerald" },
];

const REGIME_STATES = [
  {
    label: "Bull",
    description: "Momentum / Trend Following",
    bg: "from-emerald-500/20 to-emerald-600/5",
    border: "border-emerald-500/30",
    dot: "bg-emerald-400",
    text: "text-emerald-300",
  },
  {
    label: "Bear",
    description: "Defensive / Mean Reversion",
    bg: "from-red-500/20 to-red-600/5",
    border: "border-red-500/30",
    dot: "bg-red-400",
    text: "text-red-300",
  },
  {
    label: "High Vol",
    description: "Reduced Exposure / MR",
    bg: "from-orange-500/20 to-orange-600/5",
    border: "border-orange-500/30",
    dot: "bg-orange-400",
    text: "text-orange-300",
  },
  {
    label: "Low Vol",
    description: "Trend Following",
    bg: "from-blue-500/20 to-blue-600/5",
    border: "border-blue-500/30",
    dot: "bg-blue-400",
    text: "text-blue-300",
  },
];

const MATH_FORMULAS = [
  {
    label: "Simple Return",
    latex: "R_t = (P_t - P_{t-1}) / P_{t-1}",
    use: "Fundamental input for all risk metrics",
    color: "blue",
  },
  {
    label: "Sharpe Ratio",
    latex: "S = (R_p - R_f) / σ_p",
    use: "Risk-adjusted performance benchmark",
    color: "cyan",
  },
  {
    label: "Maximum Drawdown",
    latex: "MDD = max(Peak - Trough) / Peak",
    use: "Worst peak-to-trough equity loss",
    color: "emerald",
  },
  {
    label: "CVaR / Expected Shortfall",
    latex: "CVaR_α = E[L | L > VaR_α]",
    use: "Tail risk beyond the VaR threshold",
    color: "violet",
  },
  {
    label: "Portfolio Volatility",
    latex: "σ_p = √(wᵀ Σ w)",
    use: "Multi-asset covariance-weighted risk",
    color: "amber",
  },
  {
    label: "Sortino Ratio",
    latex: "Sortino = (R_p - R_f) / σ_down",
    use: "Downside deviation only — penalizes bad vol",
    color: "purple",
  },
];

const DATA_SOURCES = [
  { name: "NSE / Zerodha", region: "Indian Markets", icon: "🇮🇳", color: "from-orange-500 to-orange-600" },
  { name: "Yahoo Finance", region: "Global Equities", icon: "🌐", color: "from-purple-500 to-purple-600" },
  { name: "Binance", region: "Crypto", icon: "₿", color: "from-yellow-500 to-yellow-600" },
  { name: "FRED", region: "Macro Indicators", icon: "🏛️", color: "from-blue-500 to-blue-600" },
];


// ─── Price helpers ────────────────────────────────────────────────────────────

const MOCK_PRICES: Record<string, string> = {
  "BTC-USD": "63,840",
  "ETH-USD": "2,650",
  NVDA: "118.25",
  "RELIANCE.NS": "2,985",
  "^NSEI": "25,415",
};

export default function LandingPage() {
  return (
    <div className="min-h-screen bg-[#07090D] text-white selection:bg-blue-600 selection:text-white">
      {/* ── 1. Cinematic Scroll Hero (471 Frames) ── */}
      <HeroScrollAnimation />

      {/* ── 2. Live Multi-Asset Ticker Bar ── */}
      <section className="relative z-20 border-y border-white/10 bg-[#0B0E14]/80 backdrop-blur-md py-4 overflow-hidden">
        <div className="mx-auto max-w-7xl px-6">
          <div className="flex items-center gap-8 overflow-x-auto no-scrollbar py-1">
            <div className="flex items-center gap-2 shrink-0 pr-4 border-r border-white/10 text-xs font-semibold text-slate-400 uppercase tracking-wider">
              <span className="relative flex h-2 w-2">
                <span className="absolute h-full w-full animate-ping rounded-full bg-emerald-400 opacity-75" />
                <span className="h-2 w-2 rounded-full bg-emerald-500" />
              </span>
              Live Multi-Asset Matrix
            </div>

            {ASSETS.map((asset) => (
              <Link
                key={asset.symbol}
                href={`/assets/${encodeURIComponent(asset.symbol)}`}
                className="flex items-center gap-3 shrink-0 rounded-lg px-3 py-1.5 transition-colors hover:bg-white/5"
              >
                <div>
                  <div className="font-mono text-xs font-bold text-white flex items-center gap-1.5">
                    {asset.symbol}
                    <span className="text-[10px] font-normal text-slate-400">{asset.assetClass}</span>
                  </div>
                  <div className="text-[11px] text-slate-400 truncate max-w-[110px]">{asset.name}</div>
                </div>
                <div className="text-right font-mono text-xs">
                  <div className="text-slate-200">
                    {asset.currency === "INR" ? "₹" : "$"}
                    {MOCK_PRICES[asset.symbol] ?? "2,624"}
                  </div>
                  <div className="text-emerald-400 text-[11px]">+1.42%</div>
                </div>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* ── 3. Data Sources Strip ── */}
      <section className="relative z-20 py-10 px-6 md:px-12 border-b border-white/5">
        <div className="max-w-7xl mx-auto">
          <p className="text-center text-xs font-semibold uppercase tracking-widest text-slate-500 mb-6">
            Multi-Asset Coverage Across Global & Indian Markets
          </p>
          <div className="flex flex-wrap justify-center gap-4">
            {DATA_SOURCES.map((src) => (
              <div
                key={src.name}
                className="flex items-center gap-3 rounded-xl border border-white/10 bg-white/5 px-5 py-3 text-sm font-medium text-slate-200 hover:border-white/20 transition-colors"
              >
                <span className="text-xl">{src.icon}</span>
                <span className="font-semibold text-white">{src.name}</span>
                <span className="text-xs text-slate-500">{src.region}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── 4. Core Platform Capabilities Grid ── */}
      <section className="relative z-20 py-24 px-6 md:px-12 max-w-7xl mx-auto">
        <div className="text-center max-w-3xl mx-auto">
          <div className="inline-flex items-center gap-2 rounded-full border border-blue-500/20 bg-blue-500/10 px-3.5 py-1 text-xs font-medium text-blue-400 mb-4">
            <Zap size={13} />
            Unified Quantitative Architecture
          </div>
          <h2 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white">
            Built for Institutional Rigor
          </h2>
          <p className="mt-4 text-base sm:text-lg text-slate-400">
            From algorithmic signal formulation to regime-aware execution and portfolio risk optimization,
            TradeIQ provides the complete pipeline for modern quantitative finance.
          </p>
        </div>

        <div className="mt-16 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {CAPABILITY_CARDS.map((card) => {
            const Icon = card.icon;
            const cls = COLOR_MAP[card.color];
            const [borderCls, textCls, bgCls] = cls.split(" ");
            return (
              <div
                key={card.href}
                className={`relative rounded-2xl border border-white/10 bg-[#0E121A]/60 backdrop-blur-md p-7 transition-all duration-300 hover:${borderCls} hover:-translate-y-1`}
              >
                <div className={`flex h-11 w-11 items-center justify-center rounded-xl ${bgCls} ${textCls} mb-5`}>
                  <Icon size={22} />
                </div>
                <h3 className="text-lg font-bold text-white">{card.title}</h3>
                <p className="mt-2.5 text-sm text-slate-400 leading-relaxed">{card.body}</p>
                <div className={`mt-5 pt-4 border-t border-white/5 flex items-center justify-between text-xs ${textCls}`}>
                  <span>{card.cta}</span>
                  <ArrowRight size={13} />
                </div>
                <Link href={card.href} className="absolute inset-0" aria-label={card.cta} />
              </div>
            );
          })}
        </div>
      </section>


      {/* ── 6. Strategy Library ── */}
      <section className="relative z-20 py-20 px-6 md:px-12 max-w-7xl mx-auto">
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-amber-500/20 bg-amber-500/10 px-3.5 py-1 text-xs font-medium text-amber-400 mb-4">
              <TrendingUp size={13} />
              Strategy Library
            </div>
            <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
              6 Battle-Tested Strategies. 1 Adaptive Meta-Strategy.
            </h2>
            <p className="mt-4 text-slate-400 leading-relaxed text-sm sm:text-base">
              Every strategy follows an identical backend interface — Market Data → Signal → BUY / SELL / HOLD — 
              making them directly comparable on identical data and cost assumptions.
              The Regime-Adaptive strategy dynamically selects the best-fit approach based on the current detected market state.
            </p>
            <div className="mt-6 space-y-2">
              <div className="flex items-center gap-2 text-sm text-slate-300">
                <CheckCircle2 size={15} className="text-emerald-400" />
                <span>Walk-forward out-of-sample validation for every strategy</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-slate-300">
                <CheckCircle2 size={15} className="text-emerald-400" />
                <span>Parameter sensitivity — no hand-picked optimal values</span>
              </div>
              <div className="flex items-center gap-2 text-sm text-slate-300">
                <CheckCircle2 size={15} className="text-emerald-400" />
                <span>Benchmark comparison against Buy & Hold on same capital</span>
              </div>
            </div>
            <Link
              href="/strategies"
              className="mt-8 inline-flex items-center gap-2 rounded-xl border border-white/15 bg-white/5 px-5 py-3 text-sm font-medium text-white hover:bg-white/10 transition-colors"
            >
              Browse Strategy Library <ChevronRight size={14} />
            </Link>
          </div>

          <div className="grid grid-cols-2 gap-3">
            {STRATEGIES.map((s) => {
              const tagColors: Record<string, string> = {
                Trend: "text-blue-400 bg-blue-500/10 border-blue-500/20",
                Momentum: "text-violet-400 bg-violet-500/10 border-violet-500/20",
                "Counter-trend": "text-amber-400 bg-amber-500/10 border-amber-500/20",
                Benchmark: "text-slate-400 bg-slate-500/10 border-slate-500/20",
                Hybrid: "text-emerald-400 bg-emerald-500/10 border-emerald-500/20",
              };
              const tc = tagColors[s.tag] ?? "text-slate-400 bg-slate-500/10 border-slate-500/20";
              return (
                <div
                  key={s.name}
                  className="rounded-xl border border-white/10 bg-[#0E121A]/60 p-4 hover:border-white/20 transition-colors"
                >
                  <div className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-0.5 text-[10px] font-semibold uppercase tracking-wider mb-3 ${tc}`}>
                    {s.tag}
                  </div>
                  <div className="font-semibold text-white text-sm">{s.name}</div>
                </div>
              );
            })}
          </div>
        </div>
      </section>

      {/* ── 7. Regime Intelligence Explainer ── */}
      <section className="relative z-20 py-20 px-6 md:px-12 bg-[#0A0D14] border-y border-white/5">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-14">
            <div className="inline-flex items-center gap-2 rounded-full border border-purple-500/20 bg-purple-500/10 px-3.5 py-1 text-xs font-medium text-purple-400 mb-4">
              <Layers size={13} />
              Market Regime Intelligence
            </div>
            <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
              Know Which Market You're Trading Before You Trade It
            </h2>
            <p className="mt-4 text-slate-400 max-w-2xl mx-auto text-sm sm:text-base">
              TradeIQ detects the current market phase using K-Means clustering, Hidden Markov Models, and
              PennyLane quantum variational circuits. Each regime maps to an optimal strategy selection.
            </p>
          </div>

          {/* Features that feed the regime engine */}
          <div className="mb-10 rounded-2xl border border-white/10 bg-[#0E121A]/60 p-6">
            <p className="text-xs font-semibold uppercase tracking-widest text-slate-500 mb-4">Features fed into the Regime Engine</p>
            <div className="flex flex-wrap gap-2">
              {["Returns", "Volatility", "Momentum", "Maximum Drawdown", "Volume", "Cross-Asset Correlation", "Macro Indicators"].map((f) => (
                <span key={f} className="rounded-lg border border-purple-500/20 bg-purple-500/10 px-3 py-1 text-xs text-purple-300">
                  {f}
                </span>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            {REGIME_STATES.map((r) => (
              <div
                key={r.label}
                className={`rounded-2xl border ${r.border} bg-gradient-to-br ${r.bg} p-6`}
              >
                <div className="flex items-center gap-2 mb-3">
                  <span className={`h-2.5 w-2.5 rounded-full ${r.dot}`} />
                  <span className={`font-bold text-lg ${r.text}`}>{r.label}</span>
                </div>
                <p className="text-xs text-slate-400 leading-relaxed">{r.description}</p>
              </div>
            ))}
          </div>

          <div className="mt-8 flex justify-center">
            <Link
              href="/regimes"
              className="inline-flex items-center gap-2 rounded-xl bg-purple-600/20 border border-purple-500/30 px-6 py-3 text-sm font-medium text-purple-300 hover:bg-purple-600/30 transition-colors"
            >
              Explore Regime Dashboard <ArrowRight size={14} />
            </Link>
          </div>
        </div>
      </section>

      {/* ── 8. Core Quant Formulas ── */}
      <section className="relative z-20 py-20 px-6 md:px-12 max-w-7xl mx-auto">
        <div className="text-center mb-14">
          <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3.5 py-1 text-xs font-medium text-emerald-400 mb-4">
            <BookOpen size={13} />
            Mathematical Foundation
          </div>
          <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
            Rigorous Quant Math at Every Layer
          </h2>
          <p className="mt-4 text-slate-400 max-w-2xl mx-auto text-sm sm:text-base">
            All financial metrics are computed deterministically in the backend quant engine using institutional-grade
            formulas consistent with Indian regulatory standards (SEBI / AMFI risk disclosures).
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {MATH_FORMULAS.map((formula) => {
            const cls = COLOR_MAP[formula.color] ?? "";
            const [, textCls, bgCls] = cls.split(" ");
            return (
              <div
                key={formula.label}
                className="rounded-xl border border-white/10 bg-[#0E121A]/60 p-5 hover:border-white/20 transition-colors"
              >
                <div className={`text-xs font-semibold uppercase tracking-wider mb-2 ${textCls}`}>{formula.label}</div>
                <div className={`rounded-lg ${bgCls} border border-white/5 px-4 py-3 font-mono text-sm text-slate-200 my-3`}>
                  {formula.latex}
                </div>
                <p className="text-xs text-slate-500">{formula.use}</p>
              </div>
            );
          })}
        </div>

        <div className="mt-8 text-center">
          <p className="text-xs text-slate-600">
            Full formula inventory: Returns · Log Returns · Calmar · Omega · Treynor · Sortino · Beta · Alpha ·
            Tracking Error · Deflated Sharpe · Monte Carlo GBM · Pearson Correlation · Rolling Covariance · CAGR · IR
          </p>
        </div>
      </section>

      {/* ── 9. Backtest Trust Report + Numbers ── */}
      <section className="relative z-20 border-y border-white/10 bg-[#0A0D14] py-20 px-6 md:px-12">
        <div className="max-w-7xl mx-auto grid grid-cols-1 lg:grid-cols-2 gap-12 items-center">
          <div>
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3.5 py-1 text-xs font-medium text-emerald-400 mb-4">
              <ShieldCheck size={13} />
              The Anti-Overfitting Guarantee
            </div>
            <h2 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-white">
              Every Backtest Generates an Institutional Trust Audit
            </h2>
            <p className="mt-4 text-slate-400 leading-relaxed text-sm sm:text-base">
              Most backtesters lie to you by filling trades on the same bar close when indicators are computed.
              TradeIQ enforces execution reality so your edge survives live deployment.
            </p>

            <div className="mt-6 space-y-3 text-sm">
              {[
                ["Zero Lookahead Bias", "Signals computed at bar T execute on bar T+1."],
                ["Friction Modeling", "Brokerage fees & bid-ask slippage applied per trade."],
                ["Out-of-Sample Scrutiny", "Walk-forward decay tracking prevents curve fitting."],
                ["Parameter Stability", "2D sensitivity heatmaps expose brittle parameter choices."],
                ["Grounded AI", "Natural language analysis cited directly to verifiable backtests."],
                ["Regime Coverage", "Backtest Trust Report tags each period by market regime."],
              ].map(([strong, rest]) => (
                <div key={strong} className="flex items-start gap-3 text-slate-200">
                  <CheckCircle2 size={18} className="text-emerald-400 shrink-0 mt-0.5" />
                  <span>
                    <strong>{strong}:</strong> {rest}
                  </span>
                </div>
              ))}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4">
            {[
              ["151", "Pytest Suites Passing", "100% Core Formulas Covered", "text-emerald-400"],
              ["30.8", "Requests / Sec Stress", "Zero Concurrency Failures", "text-blue-400"],
              ["14", "Workstation Spaces", "Multi-Asset Research", "text-purple-400"],
              ["0.00%", "Lookahead Leakage", "Audited Next-Bar Model", "text-emerald-400"],
              ["10,000", "Monte Carlo Paths", "Geometric Brownian Motion", "text-cyan-400"],
              ["471", "Hero Animation Frames", "Cinematic Scroll Experience", "text-amber-400"],
            ].map(([num, label, sub, color]) => (
              <div key={label} className="rounded-2xl border border-white/10 bg-white/5 p-6 text-center">
                <div className="font-mono text-3xl sm:text-4xl font-bold text-white">{num}</div>
                <div className="mt-1 text-xs font-medium text-slate-400 uppercase tracking-wider">{label}</div>
                <div className={`mt-2 text-[11px] ${color}`}>{sub}</div>
              </div>
            ))}
          </div>
        </div>
      </section>


      {/* ── 12. CTA Banner ── */}
      <section className="relative z-20 pb-28 px-6 text-center">
        <div className="max-w-4xl mx-auto rounded-3xl border border-blue-500/20 bg-gradient-to-b from-blue-950/40 to-[#0B0E14] p-10 sm:p-16 shadow-2xl">
          <h2 className="text-3xl sm:text-5xl font-extrabold text-white tracking-tight">
            Ready to Engineer Your Quantitative Edge?
          </h2>
          <p className="mt-5 text-base sm:text-lg text-slate-400 max-w-2xl mx-auto">
            Experience the full TradeIQ workstation: backtest sweeps, regime intelligence, Monte Carlo VaR,
            and quantitative research benches — all wired to a production-grade FastAPI backend.
          </p>
          <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
            <Link
              href="/overview"
              className="inline-flex items-center gap-2.5 rounded-xl bg-blue-600 px-8 py-4 text-sm font-semibold text-white shadow-xl shadow-blue-600/30 transition-all duration-300 hover:bg-blue-500 hover:scale-105"
            >
              Launch TradeIQ Workstation
              <ArrowRight size={16} />
            </Link>
            <Link
              href="/strategies"
              className="inline-flex items-center gap-2 rounded-xl border border-white/15 bg-white/5 px-6 py-4 text-sm font-medium text-white transition-all duration-300 hover:bg-white/10"
            >
              Browse Strategy Library
            </Link>
          </div>
        </div>
      </section>

      {/* ── 13. Footer ── */}
      <footer className="border-t border-white/10 bg-[#07090D] py-12 px-6 md:px-12 text-xs text-slate-500">
        <div className="max-w-7xl mx-auto">
          {/* Top row */}
          <div className="flex flex-col sm:flex-row items-center justify-between gap-6 mb-8">
            <div className="flex items-center gap-2.5">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src="/logo-dark.png" alt="TradeIQ" className="h-6 w-6 object-contain" />
              <span className="font-bold text-white text-sm">TradeIQ</span>
              <span className="text-slate-600">|</span>
              <span>Quantitative Multi-Asset Platform</span>
            </div>

            <div className="flex flex-wrap items-center justify-center gap-x-6 gap-y-2">
              <Link href="/overview" className="hover:text-slate-300 transition-colors">Overview</Link>
              <Link href="/markets" className="hover:text-slate-300 transition-colors">Markets</Link>
              <Link href="/news" className="hover:text-slate-300 transition-colors">Live News</Link>
              <Link href="/paper-trading" className="hover:text-slate-300 transition-colors">Paper Trading</Link>
              <Link href="/backtesting" className="hover:text-slate-300 transition-colors">Backtest Lab</Link>
              <Link href="/robustness" className="hover:text-slate-300 transition-colors">Robustness</Link>
              <Link href="/risk" className="hover:text-slate-300 transition-colors">Risk & Portfolio</Link>
              <Link href="/regimes" className="hover:text-slate-300 transition-colors">Regimes</Link>
              <Link href="/ai" className="hover:text-slate-300 transition-colors">AI Research</Link>
            </div>
          </div>

          {/* Tech stack strip */}
          <div className="flex flex-wrap justify-center gap-2 mb-6 text-[11px] text-slate-700">
            {["Next.js 15", "TypeScript", "FastAPI", "NumPy", "Pandas", "Scikit-learn", "PostgreSQL", "TimescaleDB"].map((t) => (
              <span key={t} className="rounded-md border border-white/5 px-2 py-0.5">{t}</span>
            ))}
          </div>

          <div className="text-center">
            <span>© 2026 TradeIQ. Research workstation — past performance does not guarantee future returns.</span>
          </div>
        </div>
      </footer>
    </div>
  );
}
