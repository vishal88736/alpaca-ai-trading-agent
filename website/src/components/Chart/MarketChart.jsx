import { useEffect, useRef, useState } from "react";
import { createChart, ColorType } from "lightweight-charts";
import { api } from "../../api/client";
import { SkeletonBlock } from "../Common/SkeletonLoader";
import { ErrorState } from "../Common/EmptyState";

const TIMEFRAMES = ["1m", "5m", "15m", "1h", "1D"];

export function MarketChart({ symbol }) {
  const containerRef = useRef(null);
  const chartRef = useRef(null);
  const seriesRef = useRef(null);
  const [timeframe, setTimeframe] = useState("15m");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Initialize chart once
  useEffect(() => {
    if (!containerRef.current) return undefined;

    const chart = createChart(containerRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: "transparent" },
        textColor: "#a6adba",
        fontFamily: "IBM Plex Mono, monospace",
        fontSize: 11,
      },
      grid: {
        vertLines: { color: "rgba(255,255,255,0.03)" },
        horzLines: { color: "rgba(255,255,255,0.03)" },
      },
      rightPriceScale: { borderColor: "#242933" },
      timeScale: { borderColor: "#242933" },
      crosshair: { mode: 0 },
      autoSize: true,
    });

    const series = chart.addCandlestickSeries({
      upColor: "#35d68f",
      downColor: "#ff5d76",
      borderVisible: false,
      wickUpColor: "#35d68f",
      wickDownColor: "#ff5d76",
    });

    chartRef.current = chart;
    seriesRef.current = series;

    return () => {
      chart.remove();
    };
  }, []);

  // Load data on symbol/timeframe change
  useEffect(() => {
    if (!symbol) return;
    let cancelled = false;
    setLoading(true);
    setError(null);

    api
      .getMarketData(symbol, timeframe)
      .then((data) => {
        if (cancelled) return;
        const bars = (data.bars || []).map((b) => ({
          time: Math.floor(new Date(b.timestamp).getTime() / 1000),
          open: b.open,
          high: b.high,
          low: b.low,
          close: b.close,
        }));
        seriesRef.current?.setData(bars);
        chartRef.current?.timeScale().fitContent();
      })
      .catch(() => {
        if (!cancelled) {
          setError("Data unavailable");
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
    <div className="card" style={{ padding: 20 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
        <div>
          <div className="eyebrow">Live Market Chart</div>
          <div style={{ fontFamily: "var(--font-display)", fontSize: 18, fontWeight: 600, marginTop: 2 }}>
            {symbol || "Select an asset"}
          </div>
        </div>
        <div style={{ display: "flex", gap: 4 }}>
          {TIMEFRAMES.map((tf) => (
            <button
              key={tf}
              onClick={() => setTimeframe(tf)}
              className="mono"
              style={{
                fontSize: 11.5,
                padding: "5px 10px",
                borderRadius: 6,
                border: "1px solid var(--hairline-strong)",
                background: timeframe === tf ? "var(--accent-soft)" : "transparent",
                color: timeframe === tf ? "var(--accent-strong)" : "var(--text-muted)",
                cursor: "pointer",
              }}
            >
              {tf}
            </button>
          ))}
        </div>
      </div>

      {error && <ErrorState message={error} />}
      {loading && !error && <SkeletonBlock height={360} />}
      <div ref={containerRef} style={{ height: 360, display: loading || error ? "none" : "block" }} />
    </div>
  );
}
