import { SkeletonBlock } from "../Common/SkeletonLoader";
import { EmptyState, ErrorState } from "../Common/EmptyState";

function StatusBadge({ status }) {
  const s = (status || "").toLowerCase();
  let color = "var(--warning-strong)";
  let bg = "var(--warning-soft)";
  let border = "rgba(245, 158, 11, 0.25)";

  if (s === "filled") {
    color = "var(--buy-strong)";
    bg = "var(--buy-soft)";
    border = "rgba(16, 185, 129, 0.25)";
  } else if (s === "canceled" || s === "rejected" || s === "expired") {
    color = "var(--sell-strong)";
    bg = "var(--sell-soft)";
    border = "rgba(244, 63, 94, 0.25)";
  }

  return (
    <span
      className="mono"
      style={{
        fontSize: 10.5,
        fontWeight: 700,
        padding: "3px 8px",
        borderRadius: "var(--radius-full)",
        color,
        background: bg,
        border: `1px solid ${border}`,
        letterSpacing: "0.04em",
      }}
    >
      {status?.toUpperCase()}
    </span>
  );
}

export function RecentTrades({ orders, loading, error }) {
  if (loading) return <SkeletonBlock height={220} />;
  if (error) return <ErrorState message="Trade history unavailable" />;
  if (!orders || orders.length === 0) {
    return <EmptyState title="No trades yet" description="Orders placed by the automation engine will appear here." />;
  }

  return (
    <div className="scroll-x">
      <table>
        <thead>
          <tr>
            <th>Time</th>
            <th>Symbol</th>
            <th>Side</th>
            <th>Qty</th>
            <th>Avg Fill Price</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {orders.map((o) => {
            const isBuy = o.side?.toLowerCase() === "buy";
            return (
              <tr key={o.id}>
                <td className="mono" style={{ color: "var(--text-muted)", fontSize: 12 }}>
                  {o.submitted_at ? new Date(o.submitted_at).toLocaleTimeString() : "—"}
                </td>
                <td>
                  <span style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: 14 }}>
                    {o.symbol}
                  </span>
                </td>
                <td>
                  <span
                    className="mono"
                    style={{
                      fontSize: 11,
                      fontWeight: 700,
                      padding: "2px 7px",
                      borderRadius: "var(--radius-xs)",
                      color: isBuy ? "var(--buy-strong)" : "var(--sell-strong)",
                      background: isBuy ? "var(--buy-soft)" : "var(--sell-soft)",
                    }}
                  >
                    {o.side?.toUpperCase()}
                  </span>
                </td>
                <td className="mono" style={{ fontWeight: 600 }}>
                  {o.qty ?? "—"}
                </td>
                <td className="mono" style={{ fontWeight: 600 }}>
                  {o.filled_avg_price != null ? `$${o.filled_avg_price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : "—"}
                </td>
                <td>
                  <StatusBadge status={o.status} />
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}

