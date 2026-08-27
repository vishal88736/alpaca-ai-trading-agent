import { StatusIndicator } from "../Common/StatusIndicator";

export function AutomationSummary({ strategyName, assets, risk, timeframe }) {
  return (
    <div className="card" style={{ padding: "22px 24px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <div className="eyebrow">Strategy Profile</div>
        <span className="badge badge--paper">Active Plan</span>
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 14, fontSize: 13.5 }}>
        <Row label="Strategy Model" value={strategyName?.toUpperCase() || "—"} accent="var(--accent-strong)" />
        <Row label="Allowed Assets" value={assets.length ? assets.join(", ") : "None selected"} />
        <Row label="Max Position Size" value={`${risk.max_position_pct}% of equity`} />
        <Row label="Max Daily Loss Limit" value={`${risk.max_daily_loss_pct}%`} />
        <Row label="Candle Timeframe" value={timeframe} />
        <Row label="Execution Mode" value="Alpaca Paper Trading" accent="var(--warning-strong)" />
      </div>
    </div>
  );
}

function Row({ label, value, accent }) {
  return (
    <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", borderBottom: "1px solid rgba(255, 255, 255, 0.03)", paddingBottom: 6 }}>
      <span style={{ color: "var(--text-muted)", fontSize: 13 }}>{label}</span>
      <span className="mono" style={{ color: accent || "var(--text-primary)", fontWeight: 600, fontSize: 13.5 }}>
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
    <div className="card" style={{ padding: "22px 24px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 18 }}>
        <StatusIndicator state={status.state} label={`AGENT STATUS: ${status.state.replace(/_/g, " ")}`} />
        <div style={{ display: "flex", gap: 8 }}>
          {running && (
            <button className="btn btn--ghost btn--sm" onClick={onPause}>
              ⏸ Pause
            </button>
          )}
          {paused && (
            <button className="btn btn--ghost btn--sm" onClick={onResume} style={{ borderColor: "var(--accent)" }}>
              ▶ Resume
            </button>
          )}
          {!idle && (
            <button className="btn btn--ghost btn--sm" onClick={onStop}>
              ⏹ Stop
            </button>
          )}
          {!idle && (
            <button className="btn btn--danger btn--sm" onClick={onEmergencyStop}>
              🚨 Kill Switch
            </button>
          )}
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(110px, 1fr))", gap: 12, marginBottom: 18 }}>
        <MetricBox label="Strategy" value={status.strategy || "—"} mono={false} />
        <MetricBox label="Signals" value={status.signals_count} />
        <MetricBox label="Trades" value={status.trades_count} />
        <MetricBox label="Winning" value={status.winning_trades} accent="var(--buy-strong)" />
        <MetricBox label="Losing" value={status.losing_trades} accent="var(--sell-strong)" />
        <MetricBox
          label="Strategy P&L"
          value={`${status.current_pnl >= 0 ? "+" : ""}$${status.current_pnl.toFixed(2)}`}
          accent={status.current_pnl >= 0 ? "var(--buy-strong)" : "var(--sell-strong)"}
        />
      </div>

      {status.latest_decision && (
        <div style={{ borderTop: "1px solid var(--hairline)", paddingTop: 16 }}>
          <div className="eyebrow" style={{ marginBottom: 12 }}>
            Latest AI & Risk Decision
          </div>
          <LatestDecision decision={status.latest_decision} />
        </div>
      )}
    </div>
  );
}

function MetricBox({ label, value, accent, mono = true }) {
  return (
    <div
      style={{
        padding: "10px 12px",
        background: "rgba(255, 255, 255, 0.02)",
        borderRadius: "var(--radius-sm)",
        border: "1px solid rgba(255, 255, 255, 0.04)",
      }}
    >
      <div className="eyebrow" style={{ fontSize: 9.5, marginBottom: 6 }}>
        {label}
      </div>
      <div className={mono ? "mono" : ""} style={{ fontSize: 16, fontWeight: 700, color: accent || "var(--text-primary)" }}>
        {value}
      </div>
    </div>
  );
}

function LatestDecision({ decision }) {
  const buy = decision.signal === "BUY";
  return (
    <div
      style={{
        display: "flex",
        flexDirection: "column",
        gap: 10,
        padding: "14px 16px",
        background: "rgba(255, 255, 255, 0.02)",
        borderRadius: "var(--radius-md)",
        border: "1px solid var(--hairline)",
      }}
    >
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <span style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: 15 }}>{decision.symbol}</span>
          <span
            className="mono"
            style={{
              fontSize: 11,
              fontWeight: 700,
              padding: "3px 10px",
              borderRadius: "var(--radius-full)",
              color: buy ? "var(--buy-strong)" : "var(--sell-strong)",
              background: buy ? "var(--buy-soft)" : "var(--sell-soft)",
              border: `1px solid ${buy ? "rgba(16, 185, 129, 0.3)" : "rgba(244, 63, 94, 0.3)"}`,
            }}
          >
            {decision.signal}
          </span>
        </div>
        <span className="mono" style={{ fontSize: 11.5, color: "var(--accent-strong)", fontWeight: 600 }}>
          {Math.round((decision.confidence || 0) * 100)}% Confidence
        </span>
      </div>

      <p style={{ fontSize: 13, color: "var(--text-secondary)", lineHeight: 1.5 }}>
        {decision.reasoning || "Analyzing real-time indicators..."}
      </p>

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: 11.5, borderTop: "1px solid rgba(255, 255, 255, 0.04)", paddingTop: 8 }}>
        <span className="muted mono">
          Sentiment: <strong style={{ color: "var(--text-primary)" }}>{decision.news_sentiment || "NEUTRAL"}</strong>
        </span>
        <span
          className="mono"
          style={{
            color: decision.execution_result?.startsWith("FILLED") ? "var(--buy-strong)" : "var(--text-muted)",
            fontWeight: 600,
          }}
        >
          Result: {decision.execution_result || "PENDING EVALUATION"}
        </span>
      </div>
    </div>
  );
}

