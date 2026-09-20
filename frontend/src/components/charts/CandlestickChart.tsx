"use client";

import {
  useEffect,
  useRef,
  useState,
  useCallback,
  forwardRef,
  useImperativeHandle,
} from "react";
import type {
  IChartApi,
  ISeriesApi,
  CandlestickData,
  HistogramData,
  Time,
  SeriesMarker,
} from "lightweight-charts";
import {
  createChart,
  CandlestickSeries,
  HistogramSeries,
  LineSeries,
  createSeriesMarkers,
  CrosshairMode,
  ColorType,
  LineStyle,
} from "lightweight-charts";
import { Loader2, Wifi, WifiOff, RefreshCw, BarChart2, TrendingUp } from "lucide-react";
import { useTheme } from "@/components/providers";
import type { CandleData } from "@/types/paper-trading";

export interface TradeMarker {
  date: string; // 'YYYY-MM-DD'
  side: "BUY" | "SELL";
  price: number;
}

export interface CandlestickChartHandle {
  appendTick: (candle: CandleData) => void;
}

interface CandlestickChartProps {
  symbol: string;
  period?: string;
  interval?: string;
  /** Auto-stream: poll /api/v1/candles/{symbol}/tick every intervalMs ms */
  liveStream?: boolean;
  liveIntervalMs?: number;
  tradeMarkers?: TradeMarker[];
  onPriceUpdate?: (price: number, change: number, changePct: number, volume: number) => void;
}

function toChartTime(ts: number): Time {
  return ts as Time;
}

export const CandlestickChart = forwardRef<CandlestickChartHandle, CandlestickChartProps>(
  (
    {
      symbol,
      period = "1y",
      interval = "1d",
      liveStream = false,
      liveIntervalMs = 8000,
      tradeMarkers = [],
      onPriceUpdate,
    },
    ref,
  ) => {
    const { theme } = useTheme();
    const themeRef = useRef(theme);
    themeRef.current = theme;

    const containerRef = useRef<HTMLDivElement>(null);
    const chartRef = useRef<IChartApi | null>(null);
    const candleSeriesRef = useRef<ISeriesApi<"Candlestick"> | null>(null);
    const volumeSeriesRef = useRef<ISeriesApi<"Histogram"> | null>(null);
    const smaFastRef = useRef<ISeriesApi<"Line"> | null>(null);
    const smaSlowRef = useRef<ISeriesApi<"Line"> | null>(null);

    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [lastCandle, setLastCandle] = useState<CandleData | null>(null);
    const [candleCount, setCandleCount] = useState(0);
    const [priceInfo, setPriceInfo] = useState<{
      price: number;
      change: number;
      changePct: number;
      volume: number;
      open: number;
      high: number;
      low: number;
    } | null>(null);

    const isStreaming = liveStream && !loading;
    const onPriceUpdateRef = useRef(onPriceUpdate);
    onPriceUpdateRef.current = onPriceUpdate;

    const candlesRef = useRef<CandleData[]>([]);
    const streamIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

    const computeSMA = (candles: CandleData[], smaPeriod: number) => {
      const result: { time: Time; value: number }[] = [];
      for (let i = 0; i < candles.length; i++) {
        if (i < smaPeriod - 1) continue;
        const slice = candles.slice(i - smaPeriod + 1, i + 1);
        const avg = slice.reduce((s, c) => s + c.close, 0) / smaPeriod;
        result.push({ time: toChartTime(candles[i].time), value: parseFloat(avg.toFixed(2)) });
      }
      return result;
    };

    const applyTick = useCallback((candle: CandleData) => {
      if (!candleSeriesRef.current || !volumeSeriesRef.current) return;

      const existing = candlesRef.current;
      const last = existing[existing.length - 1];

      if (last && last.time === candle.time) {
        const updated = {
          ...last,
          high: Math.max(last.high, candle.high),
          low: Math.min(last.low, candle.low),
          close: candle.close,
          volume: candle.volume,
        };
        candlesRef.current[existing.length - 1] = updated;
        candleSeriesRef.current.update({
          time: toChartTime(updated.time),
          open: updated.open,
          high: updated.high,
          low: updated.low,
          close: updated.close,
        });
        volumeSeriesRef.current.update({
          time: toChartTime(updated.time),
          value: updated.volume,
          color: updated.close >= updated.open ? "rgba(16,185,129,0.5)" : "rgba(244,63,94,0.45)",
        });
      } else {
        candlesRef.current = [...existing, candle];
        candleSeriesRef.current.update({
          time: toChartTime(candle.time),
          open: candle.open,
          high: candle.high,
          low: candle.low,
          close: candle.close,
        });
        volumeSeriesRef.current.update({
          time: toChartTime(candle.time),
          value: candle.volume,
          color: candle.close >= candle.open ? "rgba(16,185,129,0.5)" : "rgba(244,63,94,0.45)",
        });

        if (smaFastRef.current && candlesRef.current.length >= 20) {
          const sma20 = computeSMA(candlesRef.current, 20);
          smaFastRef.current.setData(sma20);
        }
        if (smaSlowRef.current && candlesRef.current.length >= 50) {
          const sma50 = computeSMA(candlesRef.current, 50);
          smaSlowRef.current.setData(sma50);
        }
      }

      setCandleCount(candlesRef.current.length);

      const dayStart = existing.find((c) => c.date === candle.date)?.open ?? candle.open;
      const dailyChange = candle.close - dayStart;
      const dailyChangePct = (dailyChange / (dayStart || 1)) * 100;

      setPriceInfo({
        price: candle.close,
        change: dailyChange,
        changePct: dailyChangePct,
        volume: candle.volume,
        open: candle.open,
        high: candle.high,
        low: candle.low,
      });
      setLastCandle(candle);
      onPriceUpdateRef.current?.(candle.close, dailyChange, dailyChangePct, candle.volume);
    }, []);

    useImperativeHandle(
      ref,
      () => ({
        appendTick(candle: CandleData) {
          applyTick(candle);
        },
      }),
      [applyTick],
    );

    const fetchAndInit = useCallback(async () => {
      if (!containerRef.current) return;
      setLoading(true);
      setError(null);

      try {
        const encodedSymbol = encodeURIComponent(symbol);
        const res = await fetch(`/api/v1/candles/${encodedSymbol}?period=${period}&interval=${interval}`);
        const json = await res.json();

        if (!json.success || !Array.isArray(json.data) || json.data.length === 0) {
          setError(json.error ?? "No candle data returned from API.");
          setLoading(false);
          return;
        }

        const rawCandles: CandleData[] = json.data;
        const sorted = [...rawCandles].sort((a, b) => a.time - b.time);
        const deduped: CandleData[] = [];
        for (const c of sorted) {
          if (deduped.length === 0 || c.time > deduped[deduped.length - 1].time) {
            deduped.push(c);
          }
        }
        candlesRef.current = deduped;
        setCandleCount(deduped.length);

        if (chartRef.current) {
          chartRef.current.remove();
          chartRef.current = null;
        }
        if (containerRef.current) {
          containerRef.current.innerHTML = "";
        }

        const isCurrentlyDark = theme === "dark";
        const chart = createChart(containerRef.current, {
          layout: {
            background: { type: ColorType.Solid, color: isCurrentlyDark ? "#111419" : "#ffffff" },
            textColor: isCurrentlyDark ? "#98a2b3" : "#667085",
            fontSize: 11,
          },
          grid: {
            vertLines: { color: isCurrentlyDark ? "#242830" : "#f1f3f6", style: LineStyle.Dotted },
            horzLines: { color: isCurrentlyDark ? "#242830" : "#f1f3f6", style: LineStyle.Dotted },
          },
          crosshair: {
            mode: CrosshairMode.Normal,
            vertLine: {
              color: isCurrentlyDark ? "#334155" : "#cbd5e1",
              labelBackgroundColor: isCurrentlyDark ? "#161a20" : "#e2e8f0",
            },
            horzLine: {
              color: isCurrentlyDark ? "#334155" : "#cbd5e1",
              labelBackgroundColor: isCurrentlyDark ? "#161a20" : "#e2e8f0",
            },
          },
          rightPriceScale: {
            borderColor: isCurrentlyDark ? "#242830" : "#e6e8ec",
            textColor: isCurrentlyDark ? "#98a2b3" : "#667085",
            scaleMargins: { top: 0.08, bottom: 0.25 },
          },
          timeScale: {
            borderColor: isCurrentlyDark ? "#242830" : "#e6e8ec",
            timeVisible: true,
            secondsVisible: false,
            fixLeftEdge: true,
          },
          handleScroll: { vertTouchDrag: true },
        });

        chartRef.current = chart;

        const candleSeries = chart.addSeries(CandlestickSeries, {
          upColor: "#10b981",
          downColor: "#f43f5e",
          borderUpColor: "#10b981",
          borderDownColor: "#f43f5e",
          wickUpColor: "#10b981",
          wickDownColor: "#f43f5e",
        });

        const candleData: CandlestickData[] = deduped.map((c) => ({
          time: toChartTime(c.time),
          open: c.open,
          high: c.high,
          low: c.low,
          close: c.close,
        }));
        candleSeries.setData(candleData);
        candleSeriesRef.current = candleSeries;

        const volSeries = chart.addSeries(HistogramSeries, {
          priceFormat: { type: "volume" },
          priceScaleId: "volume",
        });
        chart.priceScale("volume").applyOptions({
          scaleMargins: { top: 0.8, bottom: 0 },
        });
        const volData: HistogramData[] = deduped.map((c) => ({
          time: toChartTime(c.time),
          value: c.volume,
          color: c.close >= c.open ? "rgba(16,185,129,0.5)" : "rgba(244,63,94,0.45)",
        }));
        volSeries.setData(volData);
        volumeSeriesRef.current = volSeries;

        const smaFastSeries = chart.addSeries(LineSeries, {
          color: "#f59e0b",
          lineWidth: 1,
          priceLineVisible: false,
          lastValueVisible: false,
        });
        smaFastSeries.setData(computeSMA(deduped, 20));
        smaFastRef.current = smaFastSeries;

        const smaSlowSeries = chart.addSeries(LineSeries, {
          color: "#8b5cf6",
          lineWidth: 1,
          priceLineVisible: false,
          lastValueVisible: false,
        });
        smaSlowSeries.setData(computeSMA(deduped, 50));
        smaSlowRef.current = smaSlowSeries;

        chart.timeScale().fitContent();

        const last = deduped[deduped.length - 1];
        const prev = deduped[deduped.length - 2] ?? last;
        const chg = last.close - prev.close;
        const chgPct = (chg / (prev.close || 1)) * 100;
        setPriceInfo({
          price: last.close,
          change: chg,
          changePct: chgPct,
          volume: last.volume,
          open: last.open,
          high: last.high,
          low: last.low,
        });
        setLastCandle(last);
        onPriceUpdateRef.current?.(last.close, chg, chgPct, last.volume);

        const observer = new ResizeObserver((entries) => {
          if (!entries || !entries.length) return;
          const { width, height } = entries[0].contentRect;
          if (width > 0 && height > 0 && chartRef.current) {
            chartRef.current.applyOptions({ width, height });
          }
        });

        if (containerRef.current) observer.observe(containerRef.current);
        setLoading(false);
        return () => observer.disconnect();
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : String(err);
        setError(msg);
        setLoading(false);
      }
    }, [symbol, period, interval, theme]);

    useEffect(() => {
      fetchAndInit();
      return () => {
        if (streamIntervalRef.current) clearInterval(streamIntervalRef.current);
      };
    }, [fetchAndInit]);

    const isUSD =
      symbol.includes("USD") ||
      symbol.includes("USDT") ||
      (!symbol.includes(".NS") && !symbol.includes(".BO"));
    const currSym = isUSD ? "$" : "₹";

    useEffect(() => {
      if (!candleSeriesRef.current || !candlesRef.current.length) return;
      if (tradeMarkers && tradeMarkers.length > 0) {
        const markers: SeriesMarker<Time>[] = tradeMarkers
          .map((m) => {
            const c = candlesRef.current.find((x) => x.date.startsWith(m.date));
            if (!c) return null;
            return {
              time: toChartTime(c.time),
              position: m.side === "BUY" ? "belowBar" : "aboveBar",
              color: m.side === "BUY" ? "#10b981" : "#f43f5e",
              shape: m.side === "BUY" ? "arrowUp" : "arrowDown",
              text: m.side === "BUY" ? `B ${currSym}${m.price}` : `S ${currSym}${m.price}`,
              size: 1,
            } as SeriesMarker<Time>;
          })
          .filter((m): m is SeriesMarker<Time> => m !== null)
          .sort((a, b) => (a.time as number) - (b.time as number));

        if (markers.length > 0) {
          createSeriesMarkers(candleSeriesRef.current, markers);
        }
      }
    }, [tradeMarkers, currSym]);

    useEffect(() => {
      if (streamIntervalRef.current) {
        clearInterval(streamIntervalRef.current);
        streamIntervalRef.current = null;
      }

      if (!liveStream || loading) return;

      const poll = async () => {
        try {
          const encodedSymbol = encodeURIComponent(symbol);
          const res = await fetch(`/api/v1/candles/${encodedSymbol}/tick?interval=${interval}`);
          const json = await res.json();
          if (json.success && json.data) {
            applyTick(json.data as CandleData);
          }
        } catch {
          // Silently keep last data
        }
      };

      streamIntervalRef.current = setInterval(poll, liveIntervalMs);

      return () => {
        if (streamIntervalRef.current) clearInterval(streamIntervalRef.current);
      };
    }, [liveStream, loading, symbol, interval, liveIntervalMs, applyTick]);

    useEffect(() => {
      if (!chartRef.current) return;
      const dark = theme === "dark";
      chartRef.current.applyOptions({
        layout: {
          background: { type: ColorType.Solid, color: dark ? "#111419" : "#ffffff" },
          textColor: dark ? "#98a2b3" : "#667085",
        },
        grid: {
          vertLines: { color: dark ? "#242830" : "#f1f3f6" },
          horzLines: { color: dark ? "#242830" : "#f1f3f6" },
        },
        crosshair: {
          vertLine: {
            color: dark ? "#334155" : "#cbd5e1",
            labelBackgroundColor: dark ? "#161a20" : "#e2e8f0",
          },
          horzLine: {
            color: dark ? "#334155" : "#cbd5e1",
            labelBackgroundColor: dark ? "#161a20" : "#e2e8f0",
          },
        },
        rightPriceScale: {
          borderColor: dark ? "#242830" : "#e6e8ec",
          textColor: dark ? "#98a2b3" : "#667085",
        },
        timeScale: {
          borderColor: dark ? "#242830" : "#e6e8ec",
        },
      });
    }, [theme]);

    useEffect(() => {
      return () => {
        if (chartRef.current) {
          chartRef.current.remove();
          chartRef.current = null;
        }
        if (streamIntervalRef.current) clearInterval(streamIntervalRef.current);
      };
    }, []);

    return (
      <div className="rounded-xl border border-(--color-edge) bg-(--color-surface) overflow-hidden shadow-sm flex flex-col">
        {/* Header */}
        <div className="px-4 py-3 border-b border-(--color-edge) bg-(--color-elev)/40 flex flex-wrap items-center justify-between gap-3">
          <div className="flex items-center gap-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="text-base font-bold text-(--color-ink) font-mono tracking-wide">
                  {symbol}
                </span>
                <span className="text-[10px] text-(--color-muted) font-mono uppercase bg-(--color-elev) px-1.5 py-0.5 rounded border border-(--color-edge)">
                  {interval.toUpperCase()} · {period.toUpperCase()}
                </span>
                {isStreaming && (
                  <span className="flex items-center gap-1 text-[10px] text-emerald-600 dark:text-emerald-400 font-mono font-semibold">
                    <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse" />
                    LIVE
                  </span>
                )}
              </div>
              {priceInfo && (
                <div className="flex items-baseline gap-2 mt-0.5">
                  <span className="text-xl font-bold font-mono text-(--color-ink)">
                    {currSym}
                    {priceInfo.price.toLocaleString(undefined, {
                      minimumFractionDigits: 2,
                      maximumFractionDigits: 2,
                    })}
                  </span>
                  <span
                    className={`text-sm font-mono font-semibold ${
                      priceInfo.change >= 0 ? "text-emerald-600 dark:text-emerald-400" : "text-rose-600 dark:text-rose-400"
                    }`}
                  >
                    {priceInfo.change >= 0 ? "+" : ""}
                    {priceInfo.change.toFixed(2)}
                    &nbsp;(
                    {priceInfo.change >= 0 ? "+" : ""}
                    {priceInfo.changePct.toFixed(2)}%)
                  </span>
                </div>
              )}
            </div>

            {priceInfo && (
              <div className="hidden md:flex gap-3 text-[11px] font-mono text-(--color-muted)">
                <div>
                  <span className="opacity-70">O</span>&nbsp;
                  <span className="text-(--color-ink) font-medium">{priceInfo.open.toFixed(2)}</span>
                </div>
                <div>
                  <span className="text-emerald-600 dark:text-emerald-500">H</span>&nbsp;
                  <span className="text-(--color-ink) font-medium">{priceInfo.high.toFixed(2)}</span>
                </div>
                <div>
                  <span className="text-rose-600 dark:text-rose-500">L</span>&nbsp;
                  <span className="text-(--color-ink) font-medium">{priceInfo.low.toFixed(2)}</span>
                </div>
                <div>
                  <span className="opacity-70">C</span>&nbsp;
                  <span className="text-(--color-ink) font-medium">{priceInfo.price.toFixed(2)}</span>
                </div>
                <div>
                  <span className="opacity-70">Vol</span>&nbsp;
                  <span className="text-cyan-600 dark:text-cyan-400 font-medium">{(priceInfo.volume / 1e6).toFixed(2)}M</span>
                </div>
              </div>
            )}
          </div>

          <div className="flex items-center gap-3">
            <div className="hidden sm:flex items-center gap-3 text-[10px] font-mono">
              <div className="flex items-center gap-1">
                <span className="h-0.5 w-5 bg-amber-500 dark:bg-amber-400 inline-block rounded" />
                <span className="text-(--color-muted)">SMA 20</span>
              </div>
              <div className="flex items-center gap-1">
                <span className="h-0.5 w-5 bg-violet-600 dark:bg-violet-500 inline-block rounded" />
                <span className="text-(--color-muted)">SMA 50</span>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {isStreaming ? (
                <Wifi className="h-3.5 w-3.5 text-emerald-600 dark:text-emerald-400 animate-pulse" />
              ) : (
                <WifiOff className="h-3.5 w-3.5 text-(--color-muted)" />
              )}
              <button
                onClick={fetchAndInit}
                title="Refresh candle data"
                className="p-1.5 rounded hover:bg-(--color-elev) text-(--color-muted) hover:text-(--color-ink) transition cursor-pointer"
              >
                <RefreshCw className="h-3.5 w-3.5" />
              </button>
            </div>
          </div>
        </div>

        {/* Chart Canvas */}
        <div className="relative" style={{ height: 440 }}>
          {loading && (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 bg-(--color-surface)/90 z-20">
              <Loader2 className="h-8 w-8 text-cyan-600 dark:text-cyan-400 animate-spin" />
              <div className="text-xs text-(--color-muted) font-mono">
                Fetching {period.toUpperCase()} · {interval.toUpperCase()} candle data for {symbol}...
              </div>
            </div>
          )}
          {error && !loading && (
            <div className="absolute inset-0 flex flex-col items-center justify-center gap-3 z-20">
              <BarChart2 className="h-10 w-10 text-(--color-muted)" />
              <div className="text-xs text-rose-600 dark:text-rose-400 font-mono text-center max-w-xs">{error}</div>
              <button
                onClick={fetchAndInit}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-(--color-elev) hover:bg-(--color-edge) text-(--color-ink) text-xs font-medium transition cursor-pointer border border-(--color-edge)"
              >
                <RefreshCw className="h-3.5 w-3.5" /> Retry
              </button>
            </div>
          )}
          <div
            ref={containerRef}
            className="w-full h-full"
            style={{ opacity: loading || error ? 0 : 1 }}
          />
        </div>

        {/* Footer */}
        {lastCandle && !loading && !error && (
          <div className="px-4 py-2 border-t border-(--color-edge) flex items-center justify-between text-[10px] font-mono text-(--color-muted)">
            <div className="flex items-center gap-1.5">
              <TrendingUp className="h-3 w-3 text-cyan-600 dark:text-cyan-400/60" />
              <span>
                {candleCount} candles loaded
                {tradeMarkers.length > 0 && ` · ${tradeMarkers.length} signals plotted`}
              </span>
            </div>
            <div>Last bar: {lastCandle.date}</div>
          </div>
        )}
      </div>
    );
  },
);

CandlestickChart.displayName = "CandlestickChart";
