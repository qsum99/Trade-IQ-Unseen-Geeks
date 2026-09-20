"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import Link from "next/link";
import { ArrowRight, ChevronDown, Sparkles, ShieldCheck, Activity, BarChart2 } from "lucide-react";

const TOTAL_FRAMES = 471;

const getFramePath = (index: number) => {
  const n = String(index).padStart(3, "0");
  return `/hero-frames/frame_${n}.webp`;
};

export function HeroScrollAnimation() {
  const containerRef = useRef<HTMLDivElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [loadedCount, setLoadedCount] = useState(0);
  const [isInitialReady, setIsInitialReady] = useState(false);
  const [progress, setProgress] = useState(0);

  const imagesRef = useRef<(HTMLImageElement | null)[]>(new Array(TOTAL_FRAMES).fill(null));
  const isLoadedRef = useRef<boolean[]>(new Array(TOTAL_FRAMES).fill(false));
  const currentFrameRef = useRef(0);
  const targetFrameRef = useRef(0);
  const animFrameIdRef = useRef<number | null>(null);

  const drawFrame = useCallback((frameIdx: number) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;

    let imgToDraw: HTMLImageElement | null = null;
    if (isLoadedRef.current[frameIdx] && imagesRef.current[frameIdx]) {
      imgToDraw = imagesRef.current[frameIdx];
    } else {
      for (let i = frameIdx - 1; i >= 0; i--) {
        if (isLoadedRef.current[i] && imagesRef.current[i]) { imgToDraw = imagesRef.current[i]; break; }
      }
      if (!imgToDraw) {
        for (let i = frameIdx + 1; i < TOTAL_FRAMES; i++) {
          if (isLoadedRef.current[i] && imagesRef.current[i]) { imgToDraw = imagesRef.current[i]; break; }
        }
      }
    }

    if (!imgToDraw) return;

    const canvasW = canvas.width;
    const canvasH = canvas.height;
    const imgW = imgToDraw.naturalWidth || 1600;
    const imgH = imgToDraw.naturalHeight || 900;
    const imgAspect = imgW / imgH;
    const canvasAspect = canvasW / canvasH;

    let drawW: number, drawH: number, drawX: number, drawY: number;
    if (canvasAspect > imgAspect) {
      drawW = canvasW; drawH = canvasW / imgAspect; drawX = 0; drawY = (canvasH - drawH) / 2;
    } else {
      drawH = canvasH; drawW = canvasH * imgAspect; drawX = (canvasW - drawW) / 2; drawY = 0;
    }

    ctx.clearRect(0, 0, canvasW, canvasH);
    ctx.drawImage(imgToDraw, drawX, drawY, drawW, drawH);
  }, []);

  const updateCanvasSize = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const dpr = window.devicePixelRatio || 1;
    const rect = canvas.getBoundingClientRect();
    const targetW = Math.floor(rect.width * dpr);
    const targetH = Math.floor(rect.height * dpr);
    if (canvas.width !== targetW || canvas.height !== targetH) {
      canvas.width = targetW;
      canvas.height = targetH;
      drawFrame(Math.round(currentFrameRef.current));
    }
  }, [drawFrame]);

  useEffect(() => {
    let isCancelled = false;
    const firstImg = new Image();
    firstImg.src = getFramePath(1);
    imagesRef.current[0] = firstImg;
    firstImg.onload = () => {
      if (isCancelled) return;
      isLoadedRef.current[0] = true;
      setLoadedCount((c) => c + 1);
      setIsInitialReady(true);
      updateCanvasSize();
      drawFrame(0);

      const initialBatchSize = 40;
      for (let i = 1; i < initialBatchSize; i++) {
        const img = new Image();
        img.src = getFramePath(i + 1);
        imagesRef.current[i] = img;
        img.onload = () => { if (isCancelled) return; isLoadedRef.current[i] = true; setLoadedCount((c) => c + 1); };
      }

      let nextIndex = initialBatchSize;
      const loadNextChunk = () => {
        if (isCancelled || nextIndex >= TOTAL_FRAMES) return;
        const chunkSize = 15;
        const end = Math.min(TOTAL_FRAMES, nextIndex + chunkSize);
        for (let i = nextIndex; i < end; i++) {
          const img = new Image();
          img.src = getFramePath(i + 1);
          imagesRef.current[i] = img;
          img.onload = () => { if (isCancelled) return; isLoadedRef.current[i] = true; setLoadedCount((c) => c + 1); };
        }
        nextIndex = end;
        if (nextIndex < TOTAL_FRAMES) setTimeout(loadNextChunk, 40);
      };
      setTimeout(loadNextChunk, 100);
    };
    return () => { isCancelled = true; };
  }, [drawFrame, updateCanvasSize]);

  useEffect(() => {
    const loop = () => {
      const target = targetFrameRef.current;
      const current = currentFrameRef.current;
      const diff = target - current;
      if (Math.abs(diff) > 0.05) {
        currentFrameRef.current = current + diff * 0.22;
        drawFrame(Math.round(currentFrameRef.current));
      } else if (current !== target) {
        currentFrameRef.current = target;
        drawFrame(Math.round(target));
      }
      animFrameIdRef.current = requestAnimationFrame(loop);
    };
    animFrameIdRef.current = requestAnimationFrame(loop);
    return () => { if (animFrameIdRef.current) cancelAnimationFrame(animFrameIdRef.current); };
  }, [drawFrame]);

  useEffect(() => {
    const handleScroll = () => {
      if (!containerRef.current) return;
      const rect = containerRef.current.getBoundingClientRect();
      const totalScrollable = rect.height - window.innerHeight;
      if (totalScrollable <= 0) return;
      const scrolled = -rect.top;
      const rawProgress = Math.max(0, Math.min(1, scrolled / totalScrollable));
      setProgress(rawProgress);
      const frameIndex = Math.min(TOTAL_FRAMES - 1, Math.max(0, Math.floor(rawProgress * (TOTAL_FRAMES - 1))));
      targetFrameRef.current = frameIndex;
    };
    window.addEventListener("scroll", handleScroll, { passive: true });
    window.addEventListener("resize", updateCanvasSize, { passive: true });
    handleScroll();
    return () => { window.removeEventListener("scroll", handleScroll); window.removeEventListener("resize", updateCanvasSize); };
  }, [updateCanvasSize]);

  // suppress unused warning
  void loadedCount;

  return (
    <div ref={containerRef} className="relative h-[480vh] w-full bg-[#07090D]">
      <div className="sticky top-0 h-screen w-full overflow-hidden flex items-center justify-center">
        {/* Canvas */}
        <canvas
          ref={canvasRef}
          className="h-full w-full object-cover transition-opacity duration-700"
          style={{ opacity: isInitialReady ? 1 : 0 }}
        />

        {/* Vignette */}
        <div className="pointer-events-none absolute inset-0 bg-gradient-to-t from-[#07090D] via-transparent to-[#07090D]/60" />
        <div className="pointer-events-none absolute inset-0 bg-gradient-to-r from-[#07090D]/80 via-transparent to-[#07090D]/80" />

        {/* Nav */}
        <header className="absolute top-0 left-0 right-0 z-30 flex items-center justify-between px-6 py-5 md:px-12 backdrop-blur-md bg-[#07090D]/40 border-b border-white/5">
          <Link href="/" className="flex items-center gap-2.5 transition-transform duration-300 hover:scale-[1.03]">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img src="/logo-dark.png" alt="TradeIQ Logo" className="h-8 w-8 object-contain" />
            <span className="text-lg font-bold tracking-tight text-white">TradeIQ</span>
          </Link>
          <nav className="hidden lg:flex items-center gap-5 text-xs font-medium text-slate-300">
            <Link href="/overview" className="hover:text-white transition-colors">Overview</Link>
            <Link href="/markets" className="hover:text-white transition-colors">Markets</Link>
            <Link href="/news" className="hover:text-white transition-colors flex items-center gap-1.5">
              <span className="h-1.5 w-1.5 rounded-full bg-red-500 animate-ping inline-block" />
              Live News
            </Link>
            <Link href="/paper-trading" className="hover:text-white transition-colors">Paper Trading</Link>
            <Link href="/strategies" className="hover:text-white transition-colors">Strategies</Link>
            <Link href="/backtesting" className="hover:text-white transition-colors">Backtest</Link>
            <Link href="/robustness" className="hover:text-white transition-colors">Robustness</Link>
            <Link href="/risk" className="hover:text-white transition-colors">Risk &amp; Portfolio</Link>
            <Link href="/ai" className="hover:text-white transition-colors">AI Research</Link>
          </nav>
          <div className="flex items-center gap-3">
            <Link
              href="/overview"
              className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-xs font-semibold text-white shadow-lg shadow-blue-600/25 transition-all duration-300 hover:bg-blue-500 hover:scale-105"
            >
              Launch App <ArrowRight size={13} />
            </Link>
          </div>
        </header>

        {/* ── Overlay 1: TradeIQ Hero (0% – 22%) ── */}
        <div
          className={`absolute inset-0 flex flex-col items-center justify-center text-center px-6 transition-all duration-700 pointer-events-none ${
            progress < 0.22 ? "opacity-100 translate-y-0" : "opacity-0 -translate-y-8"
          }`}
        >
          <div className="pointer-events-auto max-w-3xl">
            <div className="inline-flex items-center gap-2 rounded-full border border-blue-500/20 bg-blue-500/10 px-3.5 py-1 text-xs font-medium text-blue-400 backdrop-blur-md mb-5">
              <Sparkles size={13} />
              Quantitative Multi-Asset Financial Intelligence Platform
            </div>
            <h1 className="text-6xl sm:text-8xl md:text-9xl font-extrabold tracking-tighter text-white leading-[0.95] mb-4">
              TradeIQ
            </h1>
            <p className="text-2xl sm:text-4xl md:text-5xl font-extrabold tracking-tight leading-tight">
              <span className="bg-gradient-to-r from-blue-400 via-sky-300 to-cyan-400 bg-clip-text text-transparent">
                Honest Validation.
              </span>
            </p>
            <p className="mt-5 text-base sm:text-lg text-slate-300 max-w-2xl mx-auto leading-relaxed">
              Backend-centric, API-first quantitative intelligence. Multi-asset data → Quant engine →
              Strategy → Backtest → Risk → Regime → Live Execution. All deterministic. All reproducible.
            </p>
            <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
              <Link
                href="/overview"
                className="pointer-events-auto inline-flex items-center gap-2.5 rounded-xl bg-gradient-to-r from-blue-600 to-blue-500 px-6 py-3.5 text-sm font-semibold text-white shadow-xl shadow-blue-500/25 transition-all duration-300 hover:scale-105"
              >
                Launch Workstation <ArrowRight size={16} />
              </Link>
              <Link
                href="/backtesting"
                className="pointer-events-auto inline-flex items-center gap-2 rounded-xl border border-white/15 bg-white/5 backdrop-blur-md px-5 py-3.5 text-sm font-medium text-white transition-all duration-300 hover:bg-white/10"
              >
                Explore Backtest Lab
              </Link>
            </div>
            <div className="mt-12 flex items-center justify-center gap-2 text-xs font-medium text-slate-400">
              <span>Scroll to explore market continuum</span>
              <ChevronDown size={14} className="animate-bounce" />
            </div>
          </div>
        </div>

        {/* ── Overlay 2: Multi-Asset Data (25% – 46%) ── */}
        <div
          className={`absolute inset-0 flex items-center justify-start px-8 md:px-20 transition-all duration-700 pointer-events-none ${
            progress >= 0.25 && progress <= 0.46
              ? "opacity-100 translate-y-0"
              : progress < 0.25
              ? "opacity-0 translate-y-8"
              : "opacity-0 -translate-y-8"
          }`}
        >
          <div className="pointer-events-auto max-w-lg rounded-2xl border border-white/10 bg-[#07090D]/80 backdrop-blur-xl p-6 md:p-8 shadow-2xl">
            <div className="inline-flex items-center gap-2 rounded-full border border-cyan-500/20 bg-cyan-500/10 px-3 py-1 text-xs font-medium text-cyan-400 mb-3">
              <Activity size={13} />
              Multi-Asset Data Ingestion
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
              4 Global Markets, 1 Unified Quant Engine.
            </h2>
            <p className="mt-3 text-sm text-slate-300 leading-relaxed">
              NSE &amp; Zerodha for Indian equities. Yahoo Finance for global markets. Binance for 24/7 crypto.
              FRED for macro indicators. Every feed normalized with data-quality scoring and outlier detection.
            </p>
            <div className="mt-5 grid grid-cols-2 gap-2.5 text-xs">
              {[
                { src: "🇮🇳 NSE / Zerodha", sub: "Indian Equities" },
                { src: "🌐 Yahoo Finance", sub: "Global Markets" },
                { src: "₿ Binance", sub: "Crypto (24/7)" },
                { src: "🏛️ FRED", sub: "Macro Indicators" },
              ].map((d) => (
                <div key={d.src} className="rounded-lg border border-white/5 bg-white/5 p-2.5">
                  <div className="font-semibold text-white">{d.src}</div>
                  <div className="text-slate-400 mt-0.5">{d.sub}</div>
                </div>
              ))}
            </div>
            <div className="mt-4 flex flex-wrap gap-1.5">
              {["Missing-value detection", "Outlier filtering", "Calendar validation", "Quality score"].map((t) => (
                <span key={t} className="rounded-md border border-cyan-500/20 bg-cyan-500/10 px-2 py-0.5 text-[10px] text-cyan-300">{t}</span>
              ))}
            </div>
          </div>
        </div>

        {/* ── Overlay 3: Regime Intelligence & Quantum (50% – 72%) ── */}
        <div
          className={`absolute inset-0 flex items-center justify-end px-8 md:px-20 transition-all duration-700 pointer-events-none ${
            progress >= 0.50 && progress <= 0.72
              ? "opacity-100 translate-y-0"
              : progress < 0.50
              ? "opacity-0 translate-y-8"
              : "opacity-0 -translate-y-8"
          }`}
        >
          <div className="pointer-events-auto max-w-lg rounded-2xl border border-white/10 bg-[#07090D]/80 backdrop-blur-xl p-6 md:p-8 shadow-2xl">
            <div className="inline-flex items-center gap-2 rounded-full border border-purple-500/20 bg-purple-500/10 px-3 py-1 text-xs font-medium text-purple-400 mb-3">
              <Sparkles size={13} />
              Regime Intelligence Lab
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
              Phase-Adaptive Strategy Switching
            </h2>
            <p className="mt-3 text-sm text-slate-300 leading-relaxed">
              Market features (Returns, Volatility, Momentum, Drawdown, Volume) feed the Regime Engine.
              K-Means clusters states. HMM models transitions. Real-time probability estimation across bull, bear, and high-volatility regimes.
            </p>
            <div className="mt-4 grid grid-cols-2 gap-2 text-xs">
              {[
                { regime: "🟢 Bull", strategy: "Momentum / Trend Following" },
                { regime: "🔴 Bear", strategy: "Defensive / Mean Reversion" },
                { regime: "🟠 High Vol", strategy: "Reduced Exposure / MR" },
                { regime: "🔵 Low Vol", strategy: "Trend Following" },
              ].map((r) => (
                <div key={r.regime} className="rounded-lg border border-white/5 bg-white/5 p-2.5">
                  <div className="font-semibold text-white">{r.regime}</div>
                  <div className="text-slate-400 mt-0.5">{r.strategy}</div>
                </div>
              ))}
            </div>
            <div className="mt-4 flex items-center gap-4 text-xs font-medium border-t border-white/10 pt-3">
              <span className="text-blue-400">● K-Means (Primary)</span>
              <span className="text-cyan-400">● HMM (Secondary)</span>
              <span className="text-purple-400">● GMM Clustering</span>
            </div>
          </div>
        </div>

        {/* ── Overlay 4: Backtest Trust Report (76% – 94%) ── */}
        <div
          className={`absolute inset-0 flex items-center justify-start px-8 md:px-20 transition-all duration-700 pointer-events-none ${
            progress >= 0.76 && progress <= 0.94
              ? "opacity-100 translate-y-0"
              : progress < 0.76
              ? "opacity-0 translate-y-8"
              : "opacity-0 -translate-y-8"
          }`}
        >
          <div className="pointer-events-auto max-w-lg rounded-2xl border border-white/10 bg-[#07090D]/80 backdrop-blur-xl p-6 md:p-8 shadow-2xl">
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-400 mb-3">
              <ShieldCheck size={13} />
              Backtest Trust Report
            </div>
            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-white">
              Every Backtest Is Auditable
            </h2>
            <p className="mt-3 text-sm text-slate-300 leading-relaxed">
              Strict T+1 next-bar execution. Signals at bar T fill on bar T+1 open — never same-bar.
              Walk-forward validation and 2D parameter sensitivity maps expose curve fitting automatically.
            </p>
            <div className="mt-4 space-y-1.5 text-xs">
              {[
                "Zero lookahead bias — T+1 next-bar execution model",
                "Bid-ask slippage + brokerage cost per trade",
                "Walk-forward out-of-sample decay tracking",
                "2D parameter sensitivity heatmaps",
                "Fee break-even stress curves",
                "Regime coverage tag per backtest period",
              ].map((item) => (
                <div key={item} className="text-emerald-300">✓ {item}</div>
              ))}
            </div>
            <div className="mt-4 flex gap-4 text-[11px] text-slate-500 border-t border-white/10 pt-3">
              <span>151 pytest suites</span>
              <span>·</span>
              <span>30.8 req/s stress-tested</span>
              <span>·</span>
              <span>0% lookahead leakage</span>
            </div>
          </div>
        </div>

        {/* ── Overlay 5: Final CTA (95% – 100%) ── */}
        <div
          className={`absolute inset-0 flex flex-col items-center justify-center text-center px-6 transition-all duration-700 pointer-events-none ${
            progress >= 0.95 ? "opacity-100 translate-y-0" : "opacity-0 translate-y-8"
          }`}
        >
          <div className="pointer-events-auto max-w-2xl rounded-3xl border border-white/15 bg-[#07090D]/85 backdrop-blur-2xl p-8 md:p-12 shadow-2xl">
            <h2 className="text-3xl sm:text-5xl font-extrabold tracking-tight text-white">
              Ready to Test Your Edge?
            </h2>
            <p className="mt-4 text-base text-slate-300 leading-relaxed">
              14 research workspaces: backtest sweeps, parameter heatmaps, Monte Carlo VaR, regime detection,
              portfolio optimization, and quantum experiments — all wired to a production FastAPI backend.
            </p>
            <div className="mt-6 grid grid-cols-3 gap-3 text-xs text-center mb-6">
              {[
                { n: "151", l: "Tests Passing" },
                { n: "14", l: "Workspaces" },
                { n: "0%", l: "Lookahead Bias" },
              ].map((s) => (
                <div key={s.l} className="rounded-xl border border-white/10 bg-white/5 p-3">
                  <div className="font-mono text-2xl font-bold text-white">{s.n}</div>
                  <div className="text-slate-400 mt-0.5">{s.l}</div>
                </div>
              ))}
            </div>
            <div className="flex flex-wrap items-center justify-center gap-4">
              <Link
                href="/overview"
                className="inline-flex items-center gap-2.5 rounded-xl bg-blue-600 px-7 py-3.5 text-sm font-semibold text-white shadow-xl shadow-blue-600/30 transition-all duration-300 hover:bg-blue-500 hover:scale-105"
              >
                Open TradeIQ Workstation <ArrowRight size={16} />
              </Link>
              <Link
                href="/markets"
                className="inline-flex items-center gap-2 rounded-xl border border-white/15 bg-white/5 px-6 py-3.5 text-sm font-medium text-white transition-all duration-300 hover:bg-white/10"
              >
                Browse Markets
              </Link>
            </div>
          </div>
        </div>

        {/* Scroll progress indicator */}
        <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-30 flex items-center gap-3 rounded-full border border-white/10 bg-[#07090D]/60 backdrop-blur-md px-4 py-1.5 text-xs text-slate-400">
          <BarChart2 size={12} />
          <span>Scrubbing Continuum</span>
          <div className="h-1.5 w-28 rounded-full bg-white/10 overflow-hidden">
            <div
              className="h-full bg-gradient-to-r from-blue-500 to-cyan-400 transition-all duration-75"
              style={{ width: `${Math.round(progress * 100)}%` }}
            />
          </div>
          <span className="font-mono text-[11px] text-white">{Math.round(progress * 100)}%</span>
        </div>
      </div>
    </div>
  );
}
