import { useState } from "react";
import { SkeletonBlock } from "../Common/SkeletonLoader";
import { EmptyState, ErrorState } from "../Common/EmptyState";

export function DecisionLog({ decisions, loading, error }) {
  const [expandedId, setExpandedId] = useState(null);

  if (loading) return <SkeletonBlock height={280} />;
  if (error) return <ErrorState message="Decision log unavailable" />;
  if (!decisions || decisions.length === 0) {
    return <EmptyState title="No decisions yet" description="Every AI trading decision — approved or rejected — will be logged here." />;
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
      {decisions.map((d) => {
        const expanded = expandedId === d.id;
        const buy = d.signal === "BUY";
        const approved = d.risk_decision?.approved;
        return (
          <div key={d.id} className="card" style={{ padding: 0, overflow: "hidden" }}>
            <button
              onClick={() => setExpandedId(expanded ? null : d.id)}
              style={{
                width: "100%",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                padding: "14px 18px",
                background: "transparent",
                border: "none",
                cursor: "pointer",
                textAlign: "left",
              }}
            >
              <div style={{ display: "flex", gap: 14, alignItems: "center" }}>
                <span className="mono" style={{ fontSize: 11, color: "var(--text-muted)" }}>
                  {new Date(d.timestamp).toLocaleTimeString()}
                </span>
                <span style={{ fontFamily: "var(--font-display)", fontWeight: 600, fontSize: 14 }}>{d.symbol}</span>
                <span
                  className="mono"
                  style={{
                    fontSize: 10.5,
                    padding: "2px 8px",
                    borderRadius: 5,
                    color: buy ? "var(--buy)" : "var(--sell)",
                    background: buy ? "var(--buy-soft)" : "var(--sell-soft)",
                  }}
                >
                  {d.signal}
                </span>
                <span className="mono" style={{ fontSize: 10.5, color: "var(--text-muted)" }}>
                  {d.strategy}
                </span>
              </div>
              <span
                className="mono"
                style={{ fontSize: 10.5, color: approved ? "var(--buy)" : "var(--sell)" }}
              >
                {d.risk_decision ? (approved ? "RISK APPROVED" : "RISK REJECTED") : "NO INTENT"}
              </span>
            </button>

            {expanded && (
              <div style={{ padding: "0 18px 16px", borderTop: "1px solid var(--hairline)" }}>
                <p style={{ fontSize: 13, marginTop: 12 }}>{d.reasoning}</p>
                <div style={{ display: "flex", gap: 20, marginTop: 10, fontSize: 11.5 }}>
                  <span className="muted">Confidence: {Math.round(d.confidence * 100)}%</span>
                  <span className="muted">News: {d.news_sentiment || "—"}</span>
                  <span className="muted">Execution: {d.execution_result || "—"}</span>
                </div>
                {d.risk_decision?.checks_failed?.length > 0 && (
                  <div style={{ marginTop: 10 }}>
                    <div className="eyebrow" style={{ marginBottom: 6 }}>
                      Failed Risk Checks
                    </div>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                      {d.risk_decision.checks_failed.map((c) => (
                        <span
                          key={c}
                          className="mono"
                          style={{ fontSize: 10.5, color: "var(--sell)", background: "var(--sell-soft)", padding: "2px 8px", borderRadius: 5 }}
                        >
                          {c}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
