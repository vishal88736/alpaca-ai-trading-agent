import { useEffect, useState } from "react";
import { api } from "../../api/client";
import { SkeletonBlock } from "../Common/SkeletonLoader";
import { ErrorState } from "../Common/EmptyState";

const STRATEGY_ICONS = {
  momentum: "📈",
  mean_reversion: "📉",
  market_making: "⚡",
  cross_exchange_arbitrage: "🔄",
  funding_arbitrage: "🌐",
};

export function StrategySelector({ selected, onSelect }) {
  const [strategies, setStrategies] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api
      .getStrategies()
      .then(setStrategies)
      .catch(() => setError("Strategy catalog currently unavailable"));
  }, []);

  if (error) return <ErrorState message={error} />;
  if (!strategies) return <SkeletonBlock height={280} />;

  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(280px, 1fr))", gap: 16 }}>
      {strategies.map((s) => {
        const active = selected === s.key;
        const icon = STRATEGY_ICONS[s.key] || "⚡";

        return (
          <button
            key={s.key}
            onClick={() => onSelect(s.key)}
            className={`card card--interactive ${active ? "card--active" : ""}`}
            style={{
              textAlign: "left",
              padding: "22px 20px",
              cursor: "pointer",
              position: "relative",
              display: "flex",
              flexDirection: "column",
              justifyContent: "space-between",
            }}
          >
            <div>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start", marginBottom: 12 }}>
                <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                  <span style={{ fontSize: 20 }}>{icon}</span>
                  <div style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: 16, color: "var(--text-primary)" }}>
                    {s.display_name}
                  </div>
                </div>

                <div
                  style={{
                    width: 18,
                    height: 18,
                    borderRadius: "50%",
                    border: active ? "5px solid var(--accent-strong)" : "2px solid var(--hairline-strong)",
                    background: active ? "#ffffff" : "transparent",
                    transition: "all 0.15s ease",
                  }}
                />
              </div>

              <p style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.55, marginTop: 4 }}>
                {s.description}
              </p>
            </div>

            <div style={{ marginTop: 16, display: "flex", alignItems: "center", gap: 8 }}>
              {s.requires_external_venue ? (
                <span
                  className="mono"
                  style={{
                    fontSize: 10,
                    fontWeight: 700,
                    color: "var(--warning-strong)",
                    background: "var(--warning-soft)",
                    padding: "3px 8px",
                    borderRadius: "var(--radius-xs)",
                    border: "1px solid rgba(245, 158, 11, 0.25)",
                  }}
                >
                  MULTI-VENUE
                </span>
              ) : (
                <span
                  className="mono"
                  style={{
                    fontSize: 10,
                    fontWeight: 700,
                    color: "var(--buy-strong)",
                    background: "var(--buy-soft)",
                    padding: "3px 8px",
                    borderRadius: "var(--radius-xs)",
                    border: "1px solid rgba(16, 185, 129, 0.25)",
                  }}
                >
                  ALPACA READY
                </span>
              )}
              <span className="mono" style={{ fontSize: 10.5, color: "var(--text-muted)" }}>
                Key: {s.key}
              </span>
            </div>
          </button>
        );
      })}
    </div>
  );
}

