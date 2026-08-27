/**
 * Field definitions mirror the Pydantic *Config classes in
 * model/strategies/*.py. Keep these in sync if you change those schemas.
 */
const FIELD_DEFS = {
  market_making: [
    { key: "max_inventory", label: "Maximum inventory", type: "number", default: 100 },
    { key: "spread_bps", label: "Spread (bps)", type: "number", default: 10 },
    { key: "order_size", label: "Order size", type: "number", default: 1 },
    { key: "max_position", label: "Maximum position", type: "number", default: 500 },
    { key: "risk_limit_usd", label: "Risk limit ($)", type: "number", default: 1000 },
  ],
  momentum: [
    { key: "lookback_period", label: "Lookback period (bars)", type: "number", default: 20 },
    { key: "momentum_threshold", label: "Momentum threshold", type: "number", default: 0.02, step: 0.01 },
    { key: "trend_filter", label: "Trend filter", type: "checkbox", default: true },
    { key: "volatility_filter", label: "Volatility filter", type: "checkbox", default: true },
    { key: "position_size", label: "Position size (fraction)", type: "number", default: 0.1, step: 0.01 },
    { key: "stop_loss_pct", label: "Stop loss (%)", type: "number", default: 2 },
    { key: "take_profit_pct", label: "Take profit (%)", type: "number", default: 4 },
  ],
  mean_reversion: [
    { key: "lookback", label: "Lookback (bars)", type: "number", default: 20 },
    { key: "entry_z_score", label: "Entry z-score", type: "number", default: 2, step: 0.1 },
    { key: "exit_z_score", label: "Exit z-score", type: "number", default: 0.5, step: 0.1 },
    { key: "max_position", label: "Maximum position", type: "number", default: 500 },
    { key: "stop_loss_pct", label: "Stop loss (%)", type: "number", default: 3 },
    { key: "position_size", label: "Position size (fraction)", type: "number", default: 0.1, step: 0.01 },
  ],
  funding_arbitrage: [
    { key: "min_funding_rate_spread", label: "Minimum funding rate spread", type: "number", default: 0.0005, step: 0.0001 },
    { key: "hedge_ratio", label: "Hedge ratio", type: "number", default: 1, step: 0.1 },
    { key: "max_position_usd", label: "Max position ($)", type: "number", default: 1000 },
    { key: "external_venue", label: "External venue (required)", type: "text", default: "" },
  ],
  cross_exchange_arbitrage: [
    { key: "min_spread_pct", label: "Minimum spread (%)", type: "number", default: 0.15, step: 0.01 },
    { key: "max_position_usd", label: "Max position ($)", type: "number", default: 1000 },
  ],
};

export function StrategyConfigForm({ strategyKey, values, onChange }) {
  const fields = FIELD_DEFS[strategyKey] || [];

  function setField(key, value) {
    onChange({ ...values, [key]: value });
  }

  if (!strategyKey) return null;

  return (
    <div className="card" style={{ padding: 20 }}>
      <div className="eyebrow" style={{ marginBottom: 14 }}>
        Strategy Configuration
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fill, minmax(200px, 1fr))", gap: 16 }}>
        {fields.map((f) => {
          const value = values[f.key] ?? f.default;
          return (
            <div key={f.key} style={{ display: "flex", flexDirection: "column", gap: 6 }}>
              <label style={{ fontSize: 12.5, color: "var(--text-secondary)" }}>{f.label}</label>
              {f.type === "checkbox" ? (
                <input
                  type="checkbox"
                  checked={!!value}
                  onChange={(e) => setField(f.key, e.target.checked)}
                  style={{ accentColor: "var(--accent)", width: 18, height: 18 }}
                />
              ) : (
                <input
                  type={f.type}
                  step={f.step}
                  value={value}
                  onChange={(e) => setField(f.key, f.type === "number" ? Number(e.target.value) : e.target.value)}
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
              )}
            </div>
          );
        })}
      </div>
      {fields.length === 0 && (
        <p style={{ fontSize: 13 }}>No configurable parameters for this strategy.</p>
      )}
    </div>
  );
}

export { FIELD_DEFS };
