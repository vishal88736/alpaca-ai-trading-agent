import { useEffect, useRef, useState } from "react";
import { createChart, ColorType } from "lightweight-charts";
import { api } from "../../api/client";
import { ErrorState } from "../Common/EmptyState";

const TIMEFRAMES = ["1m", "5m", "15m", "1h", "1D"];

export function MarketChart({ symbol: propSymbol }) {
  const symbol = propSymbol || "BTC/USD";
  const containerRef = useRef(null);
  const chartRef = useRef(null);
  const seriesRef = useRef(null);
  const [timeframe, setTimeframe] = useState("15m");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [barStats, setBarStats] = useState(null);

  // Initialize chart instance once
  useEffect(() => {
    if (!containerRef.current) return undefined;

    const container = containerRef.current;
    const chart = createChart(container, {
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#94a3b8",
        fontFamily: "JetBrains Mono, IBM Plex Mono, monospace",
        fontSize: 11,
      },
      grid: {
        vertLines: { color: "rgba(255,255,255,0.03)" },
        horzLines: { color: "rgba(255,255,255,0.03)" },
      },
      rightPriceScale: {
        borderColor: "rgba(255,255,255,0.08)",
        scaleMargins: { top: 0.1, bottom: 0.1 },
      },
      timeScale: {
        borderColor: "rgba(255,255,255,0.08)",
        timeVisible: true,
        secondsVisible: false,
      },
      crosshair: {
        mode: 1,
        vertLine: { color: "rgba(99, 102, 241, 0.4)", width: 1, style: 3 },
        horzLine: { color: "rgba(99, 102, 241, 0.4)", width: 1, style: 3 },
      },
      width: container.clientWidth || 600,
      height: 380,
    });

    const series = chart.addCandlestickSeries({
      upColor: "#10b981",
      downColor: "#f43f5e",
      borderVisible: false,
      wickUpColor: "#10b981",
      wickDownColor: "#f43f5e",
    });

    chartRef.current = chart;
    seriesRef.current = series;

    // Handle responsive container resizing
    const resizeObserver = new ResizeObserver((entries) => {
      if (!entries || entries.length === 0) return;
      const { width, height } = entries[0].contentRect;
      if (width > 0 && chart) {
        chart.applyOptions({ width, height: height || 380 });
      }
    });

    resizeObserver.observe(container);

    return () => {
      resizeObserver.disconnect();
      chart.remove();
    };
  }, []);

  // Fetch candlestick data on symbol or timeframe change
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);

    api
      .getMarketData(symbol, timeframe)
      .then((data) => {
        if (cancelled) return;
        const rawBars = data.bars || [];
        if (rawBars.length === 0) {
          setError("No historical bars returned for this symbol.");
          return;
        }

        // Format and sort timestamps strictly ascending
        const mappedBars = rawBars
          .map((b) => ({
            time: Math.floor(new Date(b.timestamp).getTime() / 1000),
            open: Number(b.open),
            high: Number(b.high),
            low: Number(b.low),
            close: Number(b.close),
          }))
          .sort((a, b) => a.time - b.time);

        // Deduplicate timestamps (lightweight-charts requirement)
        const uniqueBars = [];
        let lastTime = null;
        for (const b of mappedBars) {
          if (b.time !== lastTime && !isNaN(b.close)) {
            uniqueBars.push(b);
            lastTime = b.time;
          }
        }

        if (uniqueBars.length > 0) {
          seriesRef.current?.setData(uniqueBars);
          chartRef.current?.timeScale().fitContent();

          const last = uniqueBars[uniqueBars.length - 1];
          const first = uniqueBars[0];
          setBarStats({
            close: last.close,
            high: Math.max(...uniqueBars.slice(-20).map((b) => b.high)),
            low: Math.min(...uniqueBars.slice(-20).map((b) => b.low)),
            changePct: ((last.close - first.open) / (first.open + 1e-8)) * 100,
          });
        }
      })
      .catch((err) => {
        if (!cancelled) {
          setError(err.message || "Failed to load market bars.");
          seriesRef.current?.setData([]);
        }
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, [symbol, timeframe]);

  return (
    <div className="card" style={{ padding: "22px 24px", position: "relative" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 16 }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div className="eyebrow">Real-Time Candlestick Chart</div>
            <span className="badge badge--live" style={{ fontSize: 10 }}>
              Live 15m
            </span>
          </div>

          <div style={{ display: "flex", alignItems: "baseline", gap: 12, marginTop: 4 }}>
            <span style={{ fontFamily: "var(--font-display)", fontSize: 22, fontWeight: 800, color: "var(--text-primary)" }}>
              {symbol}
            </span>
            {barStats && (
              <span className="mono" style={{ fontSize: 18, fontWeight: 700, color: "var(--text-primary)" }}>
                ${barStats.close.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </span>
            )}
            {barStats && (
              <span
                className="mono"
                style={{
                  fontSize: 12,
                  fontWeight: 700,
                  color: barStats.changePct >= 0 ? "var(--buy-strong)" : "var(--sell-strong)",
                }}
              >
                {barStats.changePct >= 0 ? "▲ +" : "▼ "}
                {barStats.changePct.toFixed(2)}%
              </span>
            )}
          </div>
        </div>

        <div style={{ display: "flex", gap: 6, background: "rgba(255, 255, 255, 0.02)", padding: 4, borderRadius: "var(--radius-sm)", border: "1px solid var(--hairline)" }}>
          {TIMEFRAMES.map((tf) => {
            const active = timeframe === tf;
            return (
              <button
                key={tf}
                onClick={() => setTimeframe(tf)}
                className={`mono ${active ? "btn btn--primary btn--sm" : "btn btn--ghost btn--sm"}`}
                style={{
                  fontSize: 11.5,
                  fontWeight: 700,
                  padding: "4px 10px",
                  borderRadius: "var(--radius-xs)",
                }}
              >
                {tf}
              </button>
            );
          })}
        </div>
      </div>

      {error && <ErrorState message={error} />}

      <div style={{ position: "relative", height: 380, width: "100%", overflow: "hidden" }}>
        {loading && (
          <div
            style={{
              position: "absolute",
              inset: 0,
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              background: "rgba(10, 14, 26, 0.65)",
              backdropFilter: "blur(4px)",
              zIndex: 10,
              borderRadius: "var(--radius-md)",
            }}
          >
            <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
              <span className="dot dot--pulse" style={{ color: "var(--accent-strong)" }} />
              <span className="mono" style={{ fontSize: 12, color: "var(--text-secondary)" }}>
                Loading real-time candlestick stream for {symbol}…
              </span>
            </div>
          </div>
        )}
        <div ref={containerRef} style={{ width: "100%", height: 380 }} />
      </div>
    </div>
  );
}
