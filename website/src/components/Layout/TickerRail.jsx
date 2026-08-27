/**
 * TickerRail — the app's signature element.
 *
 * A thin strip of live, monospaced price data running along the very top
 * of the shell, styled like a real terminal readout rather than a
 * decorative marquee. Symbols are duplicated for a seamless scroll loop.
 * Renders "—" for anything not yet loaded rather than inventing a number.
 */
export function TickerRail({ items = [] }) {
  const loop = items.length ? [...items, ...items] : [];

  return (
    <div
      style={{
        borderBottom: "1px solid var(--hairline)",
        background: "#08090d",
        overflow: "hidden",
        whiteSpace: "nowrap",
        height: 34,
        display: "flex",
        alignItems: "center",
      }}
      aria-hidden={items.length === 0}
    >
      {items.length === 0 ? (
        <span className="mono" style={{ fontSize: 11, color: "var(--text-muted)", paddingLeft: 20 }}>
          Connect an Alpaca account to stream live prices
        </span>
      ) : (
        <div
          style={{
            display: "flex",
            gap: 32,
            animation: "ticker-scroll 32s linear infinite",
            paddingLeft: 20,
          }}
        >
          {loop.map((item, i) => (
            <span key={`${item.symbol}-${i}`} className="mono" style={{ fontSize: 11.5, display: "flex", gap: 8 }}>
              <span style={{ color: "var(--text-muted)" }}>{item.symbol}</span>
              <span style={{ color: "var(--text-primary)" }}>
                {item.price != null ? item.price.toFixed(2) : "—"}
              </span>
              {item.changePct != null && (
                <span className={item.changePct >= 0 ? "positive" : "negative"}>
                  {item.changePct >= 0 ? "▲" : "▼"} {Math.abs(item.changePct).toFixed(2)}%
                </span>
              )}
            </span>
          ))}
        </div>
      )}
      <style>{`
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
