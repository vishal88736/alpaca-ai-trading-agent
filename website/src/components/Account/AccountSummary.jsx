import { SkeletonCard } from "../Common/SkeletonLoader";
import { ErrorState } from "../Common/EmptyState";

function fmtUsd(v) {
  if (v == null) return "—";
  const sign = v < 0 ? "-" : "";
  return `${sign}$${Math.abs(v).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function StatCard({ label, value, delta, icon, highlightColor }) {
  const isPositive = delta != null && delta >= 0;

  return (
    <div
      className="card card--interactive"
      style={{
        padding: "20px 22px",
        position: "relative",
        overflow: "hidden",
        display: "flex",
        flexDirection: "column",
        justifyContent: "space-between",
      }}
    >
      {highlightColor && (
        <div
          style={{
            position: "absolute",
            top: -20,
            right: -20,
            width: 100,
            height: 100,
            borderRadius: "50%",
            background: highlightColor,
            filter: "blur(40px)",
            opacity: 0.15,
            pointerEvents: "none",
          }}
        />
      )}

      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div className="eyebrow">{label}</div>
        {icon && <span style={{ fontSize: 16, opacity: 0.85 }}>{icon}</span>}
      </div>

      <div style={{ marginTop: 12 }}>
        <div
          className="mono"
          style={{
            fontSize: 26,
            fontWeight: 700,
            color: "var(--text-primary)",
            letterSpacing: "-0.03em",
          }}
        >
          {value}
        </div>

        {delta != null && (
          <div style={{ marginTop: 6, display: "flex", alignItems: "center", gap: 6 }}>
            <span
              className="mono"
              style={{
                fontSize: 11.5,
                fontWeight: 600,
                padding: "2px 8px",
                borderRadius: "var(--radius-full)",
                background: isPositive ? "var(--buy-soft)" : "var(--sell-soft)",
                color: isPositive ? "var(--buy-strong)" : "var(--sell-strong)",
                border: `1px solid ${isPositive ? "rgba(16, 185, 129, 0.25)" : "rgba(244, 63, 94, 0.25)"}`,
              }}
            >
              {isPositive ? "▲ +" : "▼ "}
              {fmtUsd(Math.abs(delta))}
            </span>
            <span style={{ fontSize: 11, color: "var(--text-muted)" }}>today</span>
          </div>
        )}
      </div>
    </div>
  );
}

export function AccountSummary({ account, loading, error }) {
  if (loading) {
    return (
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 16 }}>
        {Array.from({ length: 4 }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    );
  }

  if (error) return <ErrorState message="Account data unavailable" />;
  if (!account) return null;

  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: 16 }}>
      <StatCard
        label="Portfolio Value"
        value={fmtUsd(account.portfolio_value)}
        icon="💼"
        highlightColor="var(--accent)"
      />
      <StatCard
        label="Buying Power"
        value={fmtUsd(account.buying_power)}
        icon="⚡"
        highlightColor="var(--cyan)"
      />
      <StatCard
        label="Cash Balance"
        value={fmtUsd(account.cash)}
        icon="💵"
        highlightColor="rgba(255, 255, 255, 0.2)"
      />
      <StatCard
        label="Today's P&L"
        value={fmtUsd(account.todays_pl)}
        delta={account.todays_pl}
        icon="📈"
        highlightColor={account.todays_pl >= 0 ? "var(--buy)" : "var(--sell)"}
      />
    </div>
  );
}

export function AccountDetailRow({ account }) {
  if (!account) return null;
  const rows = [
    ["Account Status", account.status?.toUpperCase() || "ACTIVE"],
    ["Equity", fmtUsd(account.equity)],
    ["Long Market Value", fmtUsd(account.long_market_value)],
    ["Short Market Value", fmtUsd(account.short_market_value)],
    ["Total Unrealized P&L", fmtUsd(account.total_pl)],
    ["Account ID", account.account_id ? `${account.account_id.slice(0, 8)}...` : "—"],
  ];

  return (
    <div className="card" style={{ padding: "22px 24px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <div className="eyebrow">Account Telemetry</div>
        <span className="badge badge--neutral" style={{ fontSize: 10 }}>Alpaca Paper</span>
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", rowGap: 14, columnGap: 24 }}>
        {rows.map(([label, value]) => (
          <div key={label} style={{ display: "flex", justifyContent: "space-between", fontSize: 13, borderBottom: "1px solid rgba(255, 255, 255, 0.03)", paddingBottom: 8 }}>
            <span style={{ color: "var(--text-muted)" }}>{label}</span>
            <span className="mono" style={{ color: "var(--text-primary)", fontWeight: 600 }}>
              {value ?? "—"}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

