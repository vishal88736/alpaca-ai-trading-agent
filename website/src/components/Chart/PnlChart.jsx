import { Area, AreaChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { EmptyState } from "../Common/EmptyState";

function fmtUsd(v) {
  return `$${Number(v).toLocaleString(undefined, { maximumFractionDigits: 0 })}`;
}

function ChartTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null;
  return (
    <div className="card" style={{ padding: "8px 12px", fontSize: 12 }}>
      <div className="mono muted">{label}</div>
      <div className="mono" style={{ color: "var(--text-primary)", fontWeight: 600 }}>
        {fmtUsd(payload[0].value)}
      </div>
    </div>
  );
}

/**
 * `series` — real portfolio-value-over-time points from the backend, shape:
 * [{ label: "10:00", value: 100234.5 }, ...]. Renders an empty state rather
 * than a fabricated curve when no series data is available yet.
 */
export function PnlChart({ series }) {
  if (!series || series.length === 0) {
    return (
      <EmptyState
        title="No P&L history yet"
        description="Portfolio value over time will chart here once your account has trading history."
      />
    );
  }

  return (
    <ResponsiveContainer width="100%" height={220}>
      <AreaChart data={series} margin={{ top: 6, right: 6, left: 0, bottom: 0 }}>
        <defs>
          <linearGradient id="pnlFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--accent)" stopOpacity={0.35} />
            <stop offset="100%" stopColor="var(--accent)" stopOpacity={0} />
          </linearGradient>
        </defs>
        <XAxis
          dataKey="label"
          tick={{ fill: "#6b7280", fontSize: 11, fontFamily: "IBM Plex Mono, monospace" }}
          axisLine={{ stroke: "#242933" }}
          tickLine={false}
        />
        <YAxis
          tick={{ fill: "#6b7280", fontSize: 11, fontFamily: "IBM Plex Mono, monospace" }}
          axisLine={false}
          tickLine={false}
          tickFormatter={fmtUsd}
          width={70}
        />
        <Tooltip content={<ChartTooltip />} />
        <Area type="monotone" dataKey="value" stroke="var(--accent)" strokeWidth={2} fill="url(#pnlFill)" />
      </AreaChart>
    </ResponsiveContainer>
  );
}
