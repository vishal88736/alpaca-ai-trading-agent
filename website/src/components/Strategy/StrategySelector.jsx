import { useEffect, useState } from "react";
import { api } from "../../api/client";
import { SkeletonBlock } from "../Common/SkeletonLoader";
import { ErrorState } from "../Common/EmptyState";

export function StrategySelector({ selected, onSelect }) {
  const [strategies, setStrategies] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    api
      .getStrategies()
      .then(setStrategies)
      .catch(() => setError("Strategy list unavailable"));
  }, []);

  if (error) return <ErrorState message={error} />;
  if (!strategies) return <SkeletonBlock height={280} />;

  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(260px, 1fr))", gap: 14 }}>
      {strategies.map((s) => {
        const active = selected === s.key;
        return (
          <button
            key={s.key}
            onClick={() => onSelect(s.key)}
            className="card"
            style={{
              textAlign: "left",
              padding: 20,
              cursor: "pointer",
              border: active ? "1px solid var(--accent)" : "1px solid var(--hairline)",
              background: active ? "var(--accent-soft)" : undefined,
              position: "relative",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
              <div style={{ fontFamily: "var(--font-display)", fontWeight: 600, fontSize: 16 }}>
                {s.display_name}
              </div>
              {s.requires_external_venue && (
                <span
                  className="mono"
                  style={{
                    fontSize: 9.5,
                    color: "var(--warning)",
                    background: "var(--warning-soft)",
                    padding: "3px 7px",
                    borderRadius: 5,
                    whiteSpace: "nowrap",
                  }}
                >
                  EXTERNAL VENUE
                </span>
              )}
            </div>
            <p style={{ fontSize: 13, marginTop: 8, lineHeight: 1.5 }}>{s.description}</p>
            {s.requires_external_venue && (
              <p style={{ fontSize: 11.5, marginTop: 8, color: "var(--warning)" }}>
                Requires an external market-data/execution venue beyond Alpaca to run fully.
              </p>
            )}
          </button>
        );
      })}
    </div>
  );
}
