import { SkeletonCard } from "../Common/SkeletonLoader";
import { ErrorState } from "../Common/EmptyState";

function fmtUsd(v) {
  if (v == null) return "—";
  const sign = v < 0 ? "-" : "";
  return `${sign}$${Math.abs(v).toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function StatCard({ label, value, delta, accent }) {
  return (
    <div className="card" style={{ padding: "18px 20px" }}>
      <div className="eyebrow">{label}</div>
      <div
        className="mono"
        style={{ fontSize: 24, fontWeight: 600, marginTop: 8, color: accent ? "var(--text-primary)" : undefined }}
      >
        {value}
      </div>
      {delta != null && (
        <div className={`mono ${delta >= 0 ? "positive" : "negative"}`} style={{ fontSize: 12.5, marginTop: 4 }}>
          {delta >= 0 ? "▲" : "▼"} {fmtUsd(Math.abs(delta))}
        </div>
      )}
    </div>
  );
}

export function AccountSummary({ account, loading, error }) {
  if (loading) {
    return (
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 14 }}>
        {Array.from({ length: 4 }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    );
  }

  if (error) return <ErrorState message="Account data unavailable" />;
  if (!account) return null;

  return (
    <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: 14 }}>
      <StatCard label="Portfolio Value" value={fmtUsd(account.portfolio_value)} />
      <StatCard label="Cash" value={fmtUsd(account.cash)} />
      <StatCard label="Buying Power" value={fmtUsd(account.buying_power)} />
      <StatCard label="Today's P&L" value={fmtUsd(account.todays_pl)} delta={account.todays_pl} />
    </div>
  );
}

export function AccountDetailRow({ account }) {
  if (!account) return null;
  const rows = [
    ["Account Status", account.status],
    ["Equity", fmtUsd(account.equity)],
    ["Long Market Value", fmtUsd(account.long_market_value)],
    ["Short Market Value", fmtUsd(account.short_market_value)],
    ["Total P&L", fmtUsd(account.total_pl)],
    ["Account ID", account.account_id],
  ];

  return (
    <div className="card" style={{ padding: 20 }}>
      <div className="eyebrow" style={{ marginBottom: 14 }}>
        Account
      </div>
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", rowGap: 12, columnGap: 20 }}>
        {rows.map(([label, value]) => (
          <div key={label} style={{ display: "flex", justifyContent: "space-between", fontSize: 13 }}>
            <span style={{ color: "var(--text-muted)" }}>{label}</span>
            <span className="mono" style={{ color: "var(--text-primary)" }}>
              {value ?? "—"}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
