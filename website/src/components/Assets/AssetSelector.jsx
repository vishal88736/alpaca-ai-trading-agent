import { useEffect, useMemo, useState } from "react";
import { api } from "../../api/client";
import { SkeletonBlock } from "../Common/SkeletonLoader";
import { ErrorState } from "../Common/EmptyState";

export function AssetSelector({ selected, onChange }) {
  const [query, setQuery] = useState("");
  const [assets, setAssets] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    api
      .getAssets()
      .then((data) => !cancelled && setAssets(data))
      .catch(() => !cancelled && setError("Asset data unavailable"))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, []);

  const filtered = useMemo(() => {
    if (!assets) return [];
    const q = query.trim().toLowerCase();
    if (!q) return assets;
    return assets.filter((a) => a.symbol.toLowerCase().includes(q) || a.name.toLowerCase().includes(q));
  }, [assets, query]);

  function toggle(symbol) {
    if (selected.includes(symbol)) {
      onChange(selected.filter((s) => s !== symbol));
    } else {
      onChange([...selected, symbol]);
    }
  }

  return (
    <div className="card" style={{ padding: 20 }}>
      <div className="eyebrow" style={{ marginBottom: 12 }}>
        Select Tradable Assets
      </div>

      <input
        type="text"
        placeholder="Search assets…"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        style={{
          width: "100%",
          padding: "10px 14px",
          borderRadius: 8,
          border: "1px solid var(--hairline-strong)",
          background: "var(--void)",
          color: "var(--text-primary)",
          fontSize: 13.5,
          marginBottom: 14,
        }}
      />

      {error && <ErrorState message={error} />}
      {loading && !error && <SkeletonBlock height={280} />}

      {!loading && !error && (
        <div style={{ maxHeight: 340, overflowY: "auto", display: "flex", flexDirection: "column", gap: 4 }}>
          {filtered.length === 0 && (
            <div style={{ padding: 20, textAlign: "center", color: "var(--text-muted)", fontSize: 13 }}>
              No matching assets.
            </div>
          )}
          {filtered.slice(0, 100).map((a) => {
            const checked = selected.includes(a.symbol);
            return (
              <label
                key={a.symbol}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 12,
                  padding: "10px 10px",
                  borderRadius: 8,
                  cursor: a.tradable ? "pointer" : "not-allowed",
                  opacity: a.tradable ? 1 : 0.4,
                  background: checked ? "var(--accent-soft)" : "transparent",
                }}
              >
                <input
                  type="checkbox"
                  checked={checked}
                  disabled={!a.tradable}
                  onChange={() => toggle(a.symbol)}
                  style={{ accentColor: "var(--accent)" }}
                />
                <div style={{ flex: 1 }}>
                  <div style={{ display: "flex", gap: 8, alignItems: "baseline" }}>
                    <span style={{ fontFamily: "var(--font-mono)", fontWeight: 600, fontSize: 13 }}>{a.symbol}</span>
                    <span style={{ fontSize: 12, color: "var(--text-muted)" }}>{a.name}</span>
                  </div>
                </div>
                <span className="mono" style={{ fontSize: 10.5, color: "var(--text-muted)" }}>
                  {a.asset_class === "crypto" ? "CRYPTO" : "EQUITY"} · {a.exchange}
                </span>
                {!a.tradable && (
                  <span className="mono" style={{ fontSize: 10, color: "var(--sell)" }}>
                    NOT TRADABLE
                  </span>
                )}
              </label>
            );
          })}
        </div>
      )}

      <div
        style={{
          marginTop: 14,
          paddingTop: 14,
          borderTop: "1px solid var(--hairline)",
          fontSize: 12.5,
          color: "var(--text-muted)",
        }}
      >
        {selected.length} asset{selected.length === 1 ? "" : "s"} selected — the strategy can only trade these.
      </div>
    </div>
  );
}
