import { useState } from "react";
import { SkeletonBlock } from "../Common/SkeletonLoader";
import { EmptyState, ErrorState } from "../Common/EmptyState";

export function DecisionLog({ decisions, loading, error }) {
  const [expandedId, setExpandedId] = useState(null);

  if (loading) return <SkeletonBlock height={280} />;
  if (error) return <ErrorState message="Decision telemetry log unavailable" />;
  if (!decisions || decisions.length === 0) {
    return <EmptyState title="No decisions logged yet" description="Every AI evaluation and deterministic risk decision will be recorded in this audit log." />;
  }

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
      {decisions.map((d) => {
        const expanded = expandedId === d.id;
        const buy = d.signal === "BUY";
        const approved = d.risk_decision?.approved;

        return (
          <div
            key={d.id}
            className="card"
            style={{
              padding: 0,
              overflow: "hidden",
              position: "relative",
              borderColor: expanded ? "var(--accent)" : undefined,
            }}
          >
            <div
              style={{
                position: "absolute",
                left: 0,
                top: 0,
                bottom: 0,
                width: 4,
                background: approved ? "var(--buy-strong)" : "var(--sell-strong)",
              }}
            />

            <button
              onClick={() => setExpandedId(expanded ? null : d.id)}
              style={{
                width: "100%",
                display: "flex",
                justifyContent: "space-between",
                alignItems: "center",
                padding: "16px 20px 16px 24px",
                background: "transparent",
                border: "none",
                cursor: "pointer",
                textAlign: "left",
              }}
            >
              <div style={{ display: "flex", gap: 14, alignItems: "center" }}>
                <span className="mono" style={{ fontSize: 11.5, color: "var(--text-muted)", fontWeight: 600 }}>
                  {new Date(d.timestamp).toLocaleTimeString()}
                </span>
                <span style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: 15, color: "var(--text-primary)" }}>
                  {d.symbol}
                </span>
                <span
                  className="mono"
                  style={{
                    fontSize: 11,
                    fontWeight: 700,
                    padding: "2px 8px",
                    borderRadius: "var(--radius-full)",
                    color: buy ? "var(--buy-strong)" : "var(--sell-strong)",
                    background: buy ? "var(--buy-soft)" : "var(--sell-soft)",
                    border: `1px solid ${buy ? "rgba(16, 185, 129, 0.25)" : "rgba(244, 63, 94, 0.25)"}`,
                  }}
                >
                  {d.signal}
                </span>
                <span className="mono" style={{ fontSize: 11, color: "var(--text-secondary)", background: "rgba(255, 255, 255, 0.03)", padding: "2px 8px", borderRadius: "var(--radius-xs)" }}>
                  {d.strategy}
                </span>
              </div>

              <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <span
                  className="mono"
                  style={{
                    fontSize: 11,
                    fontWeight: 700,
                    padding: "3px 10px",
                    borderRadius: "var(--radius-full)",
                    color: approved ? "var(--buy-strong)" : "var(--sell-strong)",
                    background: approved ? "var(--buy-soft)" : "var(--sell-soft)",
                    border: `1px solid ${approved ? "rgba(16, 185, 129, 0.3)" : "rgba(244, 63, 94, 0.3)"}`,
                  }}
                >
                  {d.risk_decision ? (approved ? "RISK PASSED" : "RISK REJECTED") : "NO INTENT"}
                </span>
                <span style={{ fontSize: 12, color: "var(--text-muted)" }}>{expanded ? "▲" : "▼"}</span>
              </div>
            </button>

            {expanded && (
              <div style={{ padding: "0 24px 18px", borderTop: "1px solid var(--hairline)", background: "rgba(0, 0, 0, 0.15)" }}>
                <div style={{ marginTop: 12 }}>
                  <div className="eyebrow" style={{ fontSize: 9.5, marginBottom: 4 }}>Agent Reasoning</div>
                  <p style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.55 }}>{d.reasoning}</p>
                </div>

                <div style={{ display: "flex", flexWrap: "wrap", gap: 20, marginTop: 12, fontSize: 12 }}>
                  <span className="muted mono">
                    Confidence: <strong style={{ color: "var(--text-primary)" }}>{Math.round((d.confidence || 0) * 100)}%</strong>
                  </span>
                  <span className="muted mono">
                    News Sentiment: <strong style={{ color: "var(--text-primary)" }}>{d.news_sentiment || "NEUTRAL"}</strong>
                  </span>
                  <span className="muted mono">
                    Execution Result: <strong style={{ color: d.execution_result?.startsWith("FILLED") ? "var(--buy-strong)" : "var(--text-primary)" }}>{d.execution_result || "NONE"}</strong>
                  </span>
                </div>

                {d.risk_decision?.checks_failed?.length > 0 && (
                  <div style={{ marginTop: 14 }}>
                    <div className="eyebrow" style={{ marginBottom: 6, color: "var(--sell-strong)" }}>
                      Deterministic Risk Check Violations
                    </div>
                    <div style={{ display: "flex", flexWrap: "wrap", gap: 6 }}>
                      {d.risk_decision.checks_failed.map((c) => (
                        <span
                          key={c}
                          className="mono"
                          style={{
                            fontSize: 11,
                            fontWeight: 600,
                            color: "var(--sell-strong)",
                            background: "var(--sell-soft)",
                            border: "1px solid rgba(244, 63, 94, 0.3)",
                            padding: "3px 10px",
                            borderRadius: "var(--radius-xs)",
                          }}
                        >
                          ✕ {c}
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

