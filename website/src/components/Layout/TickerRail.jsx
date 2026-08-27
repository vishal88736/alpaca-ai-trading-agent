import { useEffect, useState } from "react";
import { api } from "../../api/client";

const DEFAULT_MARKET_TICKERS = [
  { symbol: "BTC/USD", price: 80031.98, changePct: 1.45 },
  { symbol: "ETH/USD", price: 2482.10, changePct: 0.82 },
  { symbol: "SOL/USD", price: 108.45, changePct: 3.12 },
  { symbol: "NVDA", price: 128.40, changePct: 2.15 },
  { symbol: "AAPL", price: 224.30, changePct: -0.42 },
  { symbol: "TSLA", price: 212.80, changePct: 1.88 },
  { symbol: "SPY", price: 585.60, changePct: 0.54 },
  { symbol: "QQQ", price: 494.20, changePct: 0.72 },
  { symbol: "MSFT", price: 428.15, changePct: -0.18 },
  { symbol: "AMZN", price: 186.50, changePct: 1.05 },
];

/**
 * TickerRail — Continuous infinite marquee ticker tape streaming real-time rates.
 */
export function TickerRail({ items = [] }) {
  const [liveMarketItems, setLiveMarketItems] = useState(DEFAULT_MARKET_TICKERS);

  useEffect(() => {
    let cancelled = false;

    async function fetchTickers() {
      try {
        const data = await api.getLiveTickers();
        if (!cancelled && Array.isArray(data) && data.length > 0) {
          setLiveMarketItems(data);
        }
      } catch {
        // Fallback to existing stream on network delay
      }
    }

    fetchTickers();
    const interval = setInterval(fetchTickers, 6000);

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  // Merge open portfolio positions at the front of the ticker
  const combined = [
    ...(items || []).filter((p) => p && p.symbol),
    ...liveMarketItems,
  ];

  // Deduplicate by symbol
  const uniqueSymbols = new Map();
  combined.forEach((item) => {
    if (item && item.symbol && !uniqueSymbols.has(item.symbol)) {
      uniqueSymbols.set(item.symbol, item);
    }
  });

  const baseList = Array.from(uniqueSymbols.values());
  // Duplicate list 3 times to ensure a seamless infinite seamless loop
  const loop = [...baseList, ...baseList, ...baseList, ...baseList];

  return (
    <div
      style={{
        borderBottom: "1px solid var(--hairline)",
        background: "rgba(5, 7, 14, 0.96)",
        overflow: "hidden",
        height: 38,
        display: "flex",
        alignItems: "center",
        position: "relative",
        userSelect: "none",
      }}
    >
      {/* Live Badge Fixed Header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 6,
          padding: "0 18px",
          background: "#080c18",
          borderRight: "1px solid var(--hairline-strong)",
          zIndex: 10,
          height: "100%",
          flexShrink: 0,
          boxShadow: "4px 0 12px rgba(0, 0, 0, 0.4)",
        }}
      >
        <span className="dot dot--pulse" style={{ color: "var(--buy-strong)" }} />
        <span className="eyebrow" style={{ fontSize: 9.5, color: "var(--text-primary)", fontWeight: 700 }}>
          LIVE FEED
        </span>
      </div>

      {/* Infinite Scrolling Track */}
      <div
        className="ticker-marquee-track"
        style={{
          display: "flex",
          alignItems: "center",
          gap: 14,
          width: "max-content",
          flexShrink: 0,
          animation: "ticker-marquee 30s linear infinite",
          willChange: "transform",
        }}
      >
        {loop.map((item, idx) => {
          const positive = (item.changePct || 0) >= 0;
          return (
            <div
              key={`${item.symbol}-${idx}`}
              className="mono"
              style={{
                flexShrink: 0,
                fontSize: 12,
                display: "inline-flex",
                alignItems: "center",
                gap: 8,
                padding: "4px 12px",
                background: "rgba(255, 255, 255, 0.025)",
                borderRadius: "var(--radius-full)",
                border: "1px solid rgba(255, 255, 255, 0.05)",
                transition: "border-color 0.2s ease",
              }}
            >
              <span style={{ color: "var(--text-secondary)", fontWeight: 600 }}>{item.symbol}</span>
              <span style={{ color: "var(--text-primary)", fontWeight: 700 }}>
                ${item.price != null
                  ? item.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })
                  : "—"}
              </span>
              {item.changePct != null && (
                <span
                  style={{
                    fontSize: 11,
                    fontWeight: 700,
                    color: positive ? "var(--buy-strong)" : "var(--sell-strong)",
                  }}
                >
                  {positive ? "+" : ""}
                  {Number(item.changePct).toFixed(2)}%
                </span>
              )}
            </div>
          );
        })}
      </div>

      <style>{`
        @keyframes ticker-marquee {
          0% {
            transform: translateX(0);
          }
          100% {
            transform: translateX(-50%);
          }
        }
        .ticker-marquee-track:hover {
          animation-play-state: paused;
        }
      `}</style>
    </div>
  );
}
