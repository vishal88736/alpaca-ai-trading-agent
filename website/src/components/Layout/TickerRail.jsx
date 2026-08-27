import { useEffect, useState } from "react";
import { api } from "../../api/client";

/**
 * TickerRail — Live streaming financial ticker readout with real-time rates.
 */
export function TickerRail({ items = [] }) {
  const [liveMarketItems, setLiveMarketItems] = useState([]);

  useEffect(() => {
    let cancelled = false;

    async function fetchTickers() {
      try {
        const data = await api.getLiveTickers();
        if (!cancelled && Array.isArray(data) && data.length > 0) {
          setLiveMarketItems(data);
        }
      } catch (err) {
        // Keep previous state if temporary network blip
      }
    }

    fetchTickers();
    const interval = setInterval(fetchTickers, 6000);

    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  // Merge open positions with live market stream
  const activeItems = items.length > 0 ? items : liveMarketItems;
  const displayItems = activeItems.length > 0 ? activeItems : liveMarketItems;
  const loop = displayItems.length > 0 ? [...displayItems, ...displayItems] : [];

  return (
    <div
      style={{
        borderBottom: "1px solid var(--hairline)",
        background: "rgba(5, 7, 14, 0.95)",
        overflow: "hidden",
        whiteSpace: "nowrap",
        height: 36,
        display: "flex",
        alignItems: "center",
        position: "relative",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 6,
          padding: "0 16px",
          background: "rgba(10, 14, 26, 0.95)",
          borderRight: "1px solid var(--hairline)",
          zIndex: 2,
          height: "100%",
        }}
      >
        <span className="dot dot--pulse" style={{ color: "var(--buy-strong)" }} />
        <span className="eyebrow" style={{ fontSize: 9.5, color: "var(--text-secondary)" }}>
          LIVE FEED
        </span>
      </div>

      <div
        className="ticker-track"
        style={{
          display: "flex",
          gap: 16,
          animation: "ticker-scroll 35s linear infinite",
          paddingLeft: 16,
        }}
      >
        {loop.map((item, i) => (
          <div
            key={`${item.symbol}-${i}`}
            className="mono"
            style={{
              fontSize: 11.5,
              display: "inline-flex",
              alignItems: "center",
              gap: 8,
              padding: "3px 10px",
              background: "rgba(255, 255, 255, 0.02)",
              borderRadius: "var(--radius-full)",
              border: "1px solid rgba(255, 255, 255, 0.04)",
            }}
          >
            <span style={{ color: "var(--text-secondary)", fontWeight: 600 }}>{item.symbol}</span>
            <span style={{ color: "var(--text-primary)", fontWeight: 600 }}>
              ${item.price != null ? item.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }) : "—"}
            </span>
            {item.changePct != null && (
              <span
                style={{
                  fontSize: 10.5,
                  fontWeight: 600,
                  color: item.changePct >= 0 ? "var(--buy-strong)" : "var(--sell-strong)",
                }}
              >
                {item.changePct >= 0 ? "+" : ""}
                {item.changePct.toFixed(2)}%
              </span>
            )}
          </div>
        ))}
      </div>

      <style>{`
        .ticker-track:hover {
          animation-play-state: paused;
        }
        @keyframes ticker-scroll {
          from { transform: translateX(0); }
          to { transform: translateX(-50%); }
        }
        @media (prefers-reduced-motion: reduce) {
          @keyframes ticker-scroll { from, to { transform: translateX(0); } }
        }
      `}</style>
    </div>
  );
}


