const TIMEFRAMES = ["1m", "5m", "15m", "1h", "1D"];

export function AutomationConfigPanel({ risk, timeframe, onRiskChange, onTimeframeChange }) {
  function setRisk(key, value) {
    onRiskChange({ ...risk, [key]: value });
  }

  const fields = [
    { key: "max_position_pct", label: "Max Position Size", unit: "% Equity", step: 0.5 },
    { key: "max_portfolio_exposure_pct", label: "Total Exposure Limit", unit: "% Portfolio", step: 1.0 },
    { key: "max_order_size_usd", label: "Max Order Notional", unit: "USD ($)", step: 100 },
    { key: "max_daily_loss_pct", label: "Max Daily Loss Stop", unit: "% Equity", step: 0.25 },
    { key: "max_trades_per_day", label: "Trade Frequency Cap", unit: "Trades/Day", step: 1 },
    { key: "stop_loss_pct", label: "Default Stop Loss", unit: "% Entry", step: 0.1 },
    { key: "take_profit_pct", label: "Default Take Profit", unit: "% Entry", step: 0.2 },
  ];

  return (
    <div className="card" style={{ padding: "22px 24px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <div>
          <div className="eyebrow">Deterministic Risk Guardrails</div>
          <p style={{ fontSize: 13, color: "var(--text-secondary)", marginTop: 2 }}>
            Every AI trading signal must pass all configured constraints before reaching the order execution gateway.
          </p>
        </div>
        <span className="badge badge--paper">Safety Active</span>
      </div>

      <div style={{ marginBottom: 20 }}>
        <label style={{ fontSize: 12.5, fontWeight: 600, color: "var(--text-secondary)", display: "block", marginBottom: 8 }}>
          Evaluation Candle Timeframe
        </label>
        <div style={{ display: "flex", gap: 8 }}>
          {TIMEFRAMES.map((tf) => {
            const active = timeframe === tf;
            return (
              <button
                key={tf}
                onClick={() => onTimeframeChange(tf)}
                className={`mono ${active ? "btn btn--primary btn--sm" : "btn btn--ghost btn--sm"}`}
                style={{
                  fontSize: 12,
                  fontWeight: 700,
                  minWidth: 46,
                  padding: "6px 14px",
                }}
              >
                {tf}
              </button>
            );
          })}
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(220px, 1fr))", gap: 14 }}>
        {fields.map((f) => (
          <div
            key={f.key}
            style={{
              display: "flex",
              flexDirection: "column",
              gap: 6,
              padding: "12px 14px",
              background: "rgba(255, 255, 255, 0.02)",
              borderRadius: "var(--radius-sm)",
              border: "1px solid rgba(255, 255, 255, 0.04)",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <label style={{ fontSize: 12, fontWeight: 600, color: "var(--text-secondary)" }}>{f.label}</label>
              <span className="mono" style={{ fontSize: 10, color: "var(--text-muted)" }}>{f.unit}</span>
            </div>
            <input
              type="number"
              step={f.step || "any"}
              value={risk[f.key] ?? ""}
              onChange={(e) => setRisk(f.key, Number(e.target.value))}
              style={{
                padding: "8px 12px",
                borderRadius: "var(--radius-xs)",
                border: "1px solid var(--hairline-strong)",
                background: "rgba(5, 7, 14, 0.8)",
                color: "var(--text-primary)",
                fontFamily: "var(--font-mono)",
                fontSize: 14,
                fontWeight: 600,
              }}
            />
          </div>
        ))}
      </div>
    </div>
  );
}

