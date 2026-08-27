import { SkeletonBlock } from "../Common/SkeletonLoader";
import { EmptyState, ErrorState } from "../Common/EmptyState";

function statusColor(status) {
  const s = (status || "").toLowerCase();
  if (s === "filled") return "var(--buy)";
  if (s === "canceled" || s === "rejected") return "var(--sell)";
  return "var(--warning)";
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
            <th>Price</th>
            <th>Status</th>
          </tr>
        </thead>
        <tbody>
          {orders.map((o) => (
            <tr key={o.id}>
              <td className="mono">{o.submitted_at ? new Date(o.submitted_at).toLocaleTimeString() : "—"}</td>
              <td style={{ fontWeight: 600 }}>{o.symbol}</td>
              <td className={o.side === "buy" ? "positive mono" : "negative mono"}>{o.side?.toUpperCase()}</td>
              <td className="mono">{o.qty ?? "—"}</td>
              <td className="mono">{o.filled_avg_price != null ? `$${o.filled_avg_price.toFixed(2)}` : "—"}</td>
              <td>
                <span className="mono" style={{ color: statusColor(o.status), fontSize: 11.5 }}>
                  {o.status?.toUpperCase()}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
