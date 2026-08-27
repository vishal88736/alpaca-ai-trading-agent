import { SkeletonBlock } from "../Common/SkeletonLoader";
import { EmptyState, ErrorState } from "../Common/EmptyState";

function fmtUsd(v) {
  if (v == null) return "—";
  const sign = v < 0 ? "-" : "";
  return `${sign}$${Math.abs(v).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

export function PositionsList({ positions, loading, error, onSelect }) {
  if (loading) return <SkeletonBlock height={220} />;
  if (error) return <ErrorState message="Positions data unavailable" />;
  if (!positions || positions.length === 0) {
    return <EmptyState title="No open positions" description="Positions will appear here once your strategy places trades." />;
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      {positions.map((p) => {
        const positive = p.unrealized_pl >= 0;
        return (
          <button
            key={p.symbol}
            onClick={() => onSelect?.(p.symbol)}
            className="card"
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              padding: "14px 16px",
              textAlign: "left",
              cursor: onSelect ? "pointer" : "default",
              border: "1px solid var(--hairline)",
              background: "var(--surface)",
            }}
          >
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ fontFamily: "var(--font-display)", fontWeight: 600, fontSize: 14.5 }}>{p.symbol}</span>
                <span
                  className="badge"
                  style={{
                    fontSize: 10,
                    padding: "2px 7px",
                    color: p.side === "short" ? "var(--sell)" : "var(--buy)",
                    borderColor: "transparent",
                    background: p.side === "short" ? "var(--sell-soft)" : "var(--buy-soft)",
                  }}
                >
                  {p.side || "long"}
                </span>
              </div>
              <div className="mono" style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 4 }}>
                {p.quantity} shares · {fmtUsd(p.avg_entry_price)} avg → {fmtUsd(p.current_price)} current
              </div>
            </div>
            <div style={{ textAlign: "right" }}>
              <div className={`mono ${positive ? "positive" : "negative"}`} style={{ fontSize: 15, fontWeight: 600 }}>
                {positive ? "+" : ""}
                {fmtUsd(p.unrealized_pl)}
              </div>
              <div className={`mono ${positive ? "positive" : "negative"}`} style={{ fontSize: 11.5 }}>
                {positive ? "+" : ""}
                {p.unrealized_pl_pct?.toFixed(2)}%
              </div>
            </div>
          </button>
        );
      })}
    </div>
  );
}
