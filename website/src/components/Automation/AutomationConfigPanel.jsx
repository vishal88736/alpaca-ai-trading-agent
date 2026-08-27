const TIMEFRAMES = ["1m", "5m", "15m", "1h", "1D"];

export function AutomationConfigPanel({ risk, timeframe, onRiskChange, onTimeframeChange }) {
  function setRisk(key, value) {
    onRiskChange({ ...risk, [key]: value });
  }

  const fields = [
    { key: "max_position_pct", label: "Max position (% of portfolio)" },
    { key: "max_portfolio_exposure_pct", label: "Max portfolio exposure (%)" },
    { key: "max_order_size_usd", label: "Max order size ($)" },
    { key: "max_daily_loss_pct", label: "Max daily loss (%)" },
    { key: "max_trades_per_day", label: "Max trades per day" },
    { key: "stop_loss_pct", label: "Stop loss (%)" },
    { key: "take_profit_pct", label: "Take profit (%)" },
  ];

  return (
    <div className="card" style={{ padding: 20 }}>
      <div className="eyebrow" style={{ marginBottom: 14 }}>
        Risk & Automation Settings
      </div>

      <div style={{ marginBottom: 18 }}>
        <label style={{ fontSize: 12.5, color: "var(--text-secondary)", display: "block", marginBottom: 6 }}>
          Timeframe
        </label>
        <div style={{ display: "flex", gap: 6 }}>
          {TIMEFRAMES.map((tf) => (
            <button
              key={tf}
              onClick={() => onTimeframeChange(tf)}
              className="mono"
              style={{
                fontSize: 12,
                padding: "6px 12px",
                borderRadius: 6,
                border: "1px solid var(--hairline-strong)",
                background: timeframe === tf ? "var(--accent-soft)" : "transparent",
                color: timeframe === tf ? "var(--accent-strong)" : "var(--text-muted)",
                cursor: "pointer",
              }}
            >
              {tf}
            </button>
          ))}
        </div>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 16 }}>
        {fields.map((f) => (
          <div key={f.key} style={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <label style={{ fontSize: 12.5, color: "var(--text-secondary)" }}>{f.label}</label>
            <input
              type="number"
              value={risk[f.key] ?? ""}
              onChange={(e) => setRisk(f.key, Number(e.target.value))}
              style={{
                padding: "9px 12px",
                borderRadius: 7,
                border: "1px solid var(--hairline-strong)",
                background: "var(--void)",
                color: "var(--text-primary)",
                fontFamily: "var(--font-mono)",
                fontSize: 13,
              }}
            />
          </div>
        ))}
      </div>
    </div>
  );
}
