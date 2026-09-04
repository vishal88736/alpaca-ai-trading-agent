import { useEffect, useState } from "react";
import { api } from "../../api/client";

/**
 * TickerRail — Continuous infinite marquee ticker tape streaming real-time rates.
 * No fabricated prices: until the live feed responds, only real portfolio
 * positions are shown and the badge reads OFFLINE.
 */
export function TickerRail({ items = [] }) {
  const [liveMarketItems, setLiveMarketItems] = useState([]);
  const [feedLive, setFeedLive] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function fetchTickers() {
      try {
        const data = await api.getLiveTickers();
        if (!cancelled && Array.isArray(data) && data.length > 0) {
          setLiveMarketItems(data);
          setFeedLive(true);
        }
      } catch {
        if (!cancelled) setFeedLive(false);
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
        <span
          className={feedLive ? "dot dot--pulse" : "dot"}
          style={{ color: feedLive ? "var(--buy-strong)" : "var(--warning-strong)" }}
        />
        <span className="eyebrow" style={{ fontSize: 9.5, color: "var(--text-primary)", fontWeight: 700 }}>
          {feedLive ? "LIVE FEED" : "FEED OFFLINE"}
        </span>
      </div>

      {baseList.length === 0 && (
        <span className="mono muted" style={{ fontSize: 11.5, paddingLeft: 16 }}>
          Market feed unavailable — connect and open positions to see live values here.
        </span>
      )}

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
