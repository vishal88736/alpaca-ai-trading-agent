import { StatusIndicator } from "../Common/StatusIndicator";

export function AutomationSummary({ strategyName, assets, risk, timeframe }) {
  return (
    <div className="card" style={{ padding: 20 }}>
      <div className="eyebrow" style={{ marginBottom: 14 }}>
        Strategy Summary
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 12, fontSize: 13.5 }}>
        <Row label="Strategy" value={strategyName || "—"} />
        <Row label="Assets" value={assets.length ? assets.join(", ") : "None selected"} />
        <Row label="Max position" value={`${risk.max_position_pct}%`} />
        <Row label="Max daily loss" value={`${risk.max_daily_loss_pct}%`} />
        <Row label="Timeframe" value={timeframe} />
        <Row label="Mode" value="Paper Trading" accent="var(--warning)" />
      </div>
    </div>
  );
}

function Row({ label, value, accent }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between" }}>
      <span style={{ color: "var(--text-muted)" }}>{label}</span>
      <span className="mono" style={{ color: accent || "var(--text-primary)", fontWeight: 600 }}>
        {value}
      </span>
    </div>
  );
}

export function AutomationMonitor({ status, onPause, onResume, onStop, onEmergencyStop }) {
  if (!status) return null;
  const running = status.state === "RUNNING";
  const paused = status.state === "PAUSED";
  const idle = status.state === "IDLE" || status.state === "STOPPED";

  return (
    <div className="card" style={{ padding: 20 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <StatusIndicator state={status.state} label={`AUTOMATION ${status.state.replace(/_/g, " ")}`} />
        <div style={{ display: "flex", gap: 8 }}>
          {running && (
            <button className="btn btn--ghost btn--sm" onClick={onPause}>
              Pause
            </button>
          )}
          {paused && (
            <button className="btn btn--ghost btn--sm" onClick={onResume}>
              Resume
            </button>
          )}
          {!idle && (
            <button className="btn btn--ghost btn--sm" onClick={onStop}>
              Stop
            </button>
          )}
          {!idle && (
            <button className="btn btn--danger btn--sm" onClick={onEmergencyStop}>
              Emergency Stop
            </button>
          )}
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(110px, 1fr))", gap: 16, marginBottom: 18 }}>
        <Metric label="Strategy" value={status.strategy || "—"} mono={false} />
        <Metric label="Signals" value={status.signals_count} />
        <Metric label="Trades" value={status.trades_count} />
        <Metric label="Winning" value={status.winning_trades} accent="var(--buy)" />
        <Metric label="Losing" value={status.losing_trades} accent="var(--sell)" />
        <Metric
          label="Current P&L"
          value={`${status.current_pnl >= 0 ? "+" : ""}$${status.current_pnl.toFixed(2)}`}
          accent={status.current_pnl >= 0 ? "var(--buy)" : "var(--sell)"}
        />
      </div>

      {status.latest_decision && (
        <div style={{ borderTop: "1px solid var(--hairline)", paddingTop: 16 }}>
          <div className="eyebrow" style={{ marginBottom: 10 }}>
            Latest Decision
          </div>
          <LatestDecision decision={status.latest_decision} />
        </div>
      )}
    </div>
  );
}

function Metric({ label, value, accent, mono = true }) {
  return (
    <div>
      <div className="eyebrow" style={{ marginBottom: 4 }}>
        {label}
      </div>
      <div className={mono ? "mono" : ""} style={{ fontSize: 16, fontWeight: 600, color: accent }}>
        {value}
      </div>
    </div>
  );
}

function LatestDecision({ decision }) {
  const buy = decision.signal === "BUY";
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 8, fontSize: 13 }}>
      <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
        <span style={{ fontFamily: "var(--font-display)", fontWeight: 600, fontSize: 15 }}>{decision.symbol}</span>
        <span
          className="mono"
          style={{
            fontSize: 11,
            padding: "3px 8px",
            borderRadius: 5,
            color: buy ? "var(--buy)" : "var(--sell)",
            background: buy ? "var(--buy-soft)" : "var(--sell-soft)",
          }}
        >
          {decision.signal}
        </span>
        <span className="mono muted" style={{ fontSize: 11 }}>
          {Math.round(decision.confidence * 100)}% confidence
        </span>
      </div>
      <p style={{ fontSize: 13 }}>{decision.reasoning}</p>
      <div style={{ display: "flex", gap: 16, fontSize: 11.5 }}>
        <span className="muted">News: {decision.news_sentiment || "—"}</span>
        <span className={decision.execution_result?.startsWith("FILLED") ? "positive" : "muted"}>
          Result: {decision.execution_result || "pending"}
        </span>
      </div>
    </div>
  );
}
