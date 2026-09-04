import { useEffect, useState } from "react";
import { AppShell } from "../components/Layout/AppShell";
import { api } from "../api/client";

function RegimeBadge({ regime }) {
  const cls =
    regime === "BULLISH"
      ? "badge badge--live"
      : regime === "BEARISH"
        ? "badge badge--danger"
        : regime === "HIGH_VOLATILITY"
          ? "badge badge--danger"
          : "badge badge--paper";
  return <span className={cls}>{regime || "UNKNOWN"}</span>;
}

export function Agents() {
  const [events, setEvents] = useState(null);
  const [regime, setRegime] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;
    async function load() {
      const [evRes, regRes] = await Promise.allSettled([api.getAgentEvents(100), api.getMarketRegime()]);
      if (cancelled) return;
      if (evRes.status === "fulfilled") setEvents(evRes.value);
      if (regRes.status === "fulfilled") setRegime(regRes.value);
      setLoading(false);
    }
    load();
    const interval = setInterval(load, 8000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  return (
    <AppShell>
      <div style={{ marginBottom: 24 }}>
        <div className="eyebrow">Pipeline Activity</div>
        <h2 style={{ fontSize: 24, marginTop: 6 }}>Agent Activity</h2>
        <p style={{ marginTop: 6, fontSize: 13.5 }}>
          What each agent actually did, in order. An agent appears here only after it ran — a green badge in the UI
          never substitutes for a real execution event.
        </p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 2fr", gap: 20, alignItems: "start" }}>
        <div className="card" style={{ padding: 20 }}>
          <div className="eyebrow" style={{ marginBottom: 12 }}>
            Market Regime
          </div>
          {regime ? (
            <>
              <div style={{ marginBottom: 10 }}>
                <RegimeBadge regime={regime.regime} />
              </div>
              <div className="mono" style={{ fontSize: 13, marginBottom: 10 }}>
                Confidence {(regime.confidence * 100).toFixed(0)}% · Vol {regime.volatility} · Mom {regime.momentum}
              </div>
              <ul style={{ margin: 0, paddingLeft: 18, fontSize: 13, color: "var(--text-secondary)" }}>
                {(regime.observations || []).map((o, i) => (
                  <li key={i} style={{ marginBottom: 4 }}>
                    {o}
                  </li>
                ))}
              </ul>
            </>
          ) : (
            <p style={{ fontSize: 13 }}>{loading ? "Loading…" : "Regime unavailable."}</p>
          )}
        </div>

        <div className="card" style={{ padding: 20 }}>
          <div className="eyebrow" style={{ marginBottom: 14 }}>
            Agent Events
          </div>
          {!events ? (
            <p style={{ fontSize: 13 }}>{loading ? "Loading…" : "No events yet. Start automation to generate activity."}</p>
          ) : events.length === 0 ? (
            <p style={{ fontSize: 13 }}>No events yet. Start automation to generate activity.</p>
          ) : (
            <div style={{ display: "flex", flexDirection: "column", gap: 10 }}>
              {events.map((e, i) => (
                <div
                  key={i}
                  style={{
                    padding: "10px 14px",
                    borderRadius: "var(--radius-sm)",
                    border: "1px solid var(--hairline)",
                    background: "var(--surface-raised)",
                    fontSize: 12.5,
                  }}
                >
                  <div style={{ display: "flex", gap: 8, alignItems: "center", marginBottom: 4, flexWrap: "wrap" }}>
                    <span className="badge badge--neutral">{e.agent}</span>
                    <span className="mono" style={{ fontWeight: 700 }}>
                      {e.action}
                    </span>
                    {e.symbol && <span className="mono muted">{e.symbol}</span>}
                  </div>
                  <div style={{ color: "var(--text-secondary)" }}>{e.details}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
