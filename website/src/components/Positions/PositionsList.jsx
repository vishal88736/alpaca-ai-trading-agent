import { SkeletonBlock } from "../Common/SkeletonLoader";
import { EmptyState, ErrorState } from "../Common/EmptyState";

function fmtUsd(v) {
  if (v == null) return "—";
  const sign = v < 0 ? "-" : "";
  return `${sign}$${Math.abs(v).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

export function PositionsList({ positions, loading, error, onSelect, selectedSymbol }) {
  if (loading) return <SkeletonBlock height={220} />;
  if (error) return <ErrorState message="Positions data unavailable" />;
  if (!positions || positions.length === 0) {
    return <EmptyState title="No open positions" description="Active positions will appear here once the agent executes trades." />;
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      {positions.map((p) => {
        const positive = p.unrealized_pl >= 0;
        const isSelected = selectedSymbol === p.symbol;

        return (
          <button
            key={p.symbol}
            onClick={() => onSelect?.(p.symbol)}
            className={`card card--interactive ${isSelected ? "card--active" : ""}`}
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              padding: "14px 18px",
              textAlign: "left",
              cursor: "pointer",
              position: "relative",
              overflow: "hidden",
            }}
          >
            <div
              style={{
                position: "absolute",
                left: 0,
                top: 0,
                bottom: 0,
                width: 4,
                background: positive ? "var(--buy-strong)" : "var(--sell-strong)",
              }}
            />

            <div style={{ paddingLeft: 6 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <span style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: 15, color: "var(--text-primary)" }}>
                  {p.symbol}
                </span>
                <span
                  className="mono"
                  style={{
                    fontSize: 10,
                    fontWeight: 700,
                    padding: "2px 8px",
                    borderRadius: "var(--radius-full)",
                    color: p.side === "short" ? "var(--sell-strong)" : "var(--buy-strong)",
                    background: p.side === "short" ? "var(--sell-soft)" : "var(--buy-soft)",
                    border: `1px solid ${p.side === "short" ? "rgba(244, 63, 94, 0.25)" : "rgba(16, 185, 129, 0.25)"}`,
                    textTransform: "uppercase",
                  }}
                >
                  {p.side || "long"}
                </span>
              </div>
              <div className="mono" style={{ fontSize: 12, color: "var(--text-muted)", marginTop: 4 }}>
                {p.quantity} units · Entry {fmtUsd(p.avg_entry_price)} → {fmtUsd(p.current_price)}
              </div>
            </div>

            <div style={{ textAlign: "right" }}>
              <div
                className="mono"
                style={{
                  fontSize: 15,
                  fontWeight: 700,
                  color: positive ? "var(--buy-strong)" : "var(--sell-strong)",
                }}
              >
                {positive ? "+" : ""}
                {fmtUsd(p.unrealized_pl)}
              </div>
              <div
                className="mono"
                style={{
                  fontSize: 11.5,
                  fontWeight: 600,
                  color: positive ? "var(--buy-strong)" : "var(--sell-strong)",
                  marginTop: 2,
                }}
              >
                {positive ? "▲ +" : "▼ "}
                {p.unrealized_pl_pct?.toFixed(2)}%
              </div>
            </div>
          </button>
        );
      })}
    </div>
  );
}

