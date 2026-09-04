import { useEffect, useMemo, useState } from "react";
import { api } from "../../api/client";
import { SkeletonBlock } from "../Common/SkeletonLoader";
import { ErrorState } from "../Common/EmptyState";

export function AssetSelector({ selected, onChange }) {
  const [query, setQuery] = useState("");
  const [filterClass, setFilterClass] = useState("all");
  const [assets, setAssets] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    api
      .getAssets()
      .then((data) => !cancelled && setAssets(data))
      .catch(() => !cancelled && setError("Asset catalog currently unavailable"))
      .finally(() => !cancelled && setLoading(false));
    return () => {
      cancelled = true;
    };
  }, []);

  const filtered = useMemo(() => {
    if (!assets) return [];
    let list = assets;

    // Filter by asset class
    if (filterClass === "crypto") {
      list = list.filter((a) => a.asset_class === "crypto" || a.symbol.includes("/"));
    } else if (filterClass === "us_equity") {
      list = list.filter((a) => a.asset_class === "us_equity" || a.asset_class === "equity");
    } else if (filterClass === "options") {
      list = list.filter((a) => a.asset_class === "options");
    }

    const q = query.trim().toLowerCase();
    if (!q) return list;

    const qNormalized = q.replace(/[\/\-_]/g, "");

    return list.filter((a) => {
      const sym = a.symbol.toLowerCase();
      const symNormalized = sym.replace(/[\/\-_]/g, "");
      const name = (a.name || "").toLowerCase();
      return (
        sym.includes(q) ||
        symNormalized.includes(qNormalized) ||
        name.includes(q)
      );
    });
  }, [assets, query, filterClass]);

  function toggle(symbol) {
    if (selected.includes(symbol)) {
      onChange(selected.filter((s) => s !== symbol));
    } else {
      onChange([...selected, symbol]);
    }
  }

  function selectAllFiltered() {
    const tradable = filtered.filter((a) => a.tradable).map((a) => a.symbol);
    const merged = Array.from(new Set([...selected, ...tradable]));
    onChange(merged);
  }

  function clearAll() {
    onChange([]);
  }

  return (
    <div className="card" style={{ padding: "22px 24px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <div>
          <div className="eyebrow">Permitted Asset Universe</div>
          <p style={{ fontSize: 13, color: "var(--text-secondary)", marginTop: 2 }}>
            Choose the assets your autonomous trading strategy is authorized to scan, price, and trade.
          </p>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <button className="btn btn--ghost btn--sm" onClick={selectAllFiltered} style={{ fontSize: 11 }}>
            Select Filtered
          </button>
          <button className="btn btn--ghost btn--sm" onClick={clearAll} style={{ fontSize: 11 }}>
            Clear
          </button>
        </div>
      </div>

      <div style={{ display: "flex", gap: 10, marginBottom: 14 }}>
        <input
          type="text"
          placeholder="Search by symbol or name (e.g. BTC, ETH, AAPL, SPY, SOL)…"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          style={{
            flex: 1,
            padding: "10px 14px",
            borderRadius: "var(--radius-sm)",
            border: "1px solid var(--hairline-strong)",
            background: "rgba(5, 7, 14, 0.8)",
            color: "var(--text-primary)",
            fontSize: 13.5,
          }}
        />

        <div style={{ display: "flex", gap: 4 }}>
          {[
            { key: "all", label: "All" },
            { key: "crypto", label: "Crypto" },
            { key: "us_equity", label: "Equities" },
            { key: "options", label: "Options / Alpha" },
          ].map((item) => (
            <button
              key={item.key}
              className={`btn btn--sm ${filterClass === item.key ? "btn--primary" : "btn--ghost"}`}
              onClick={() => setFilterClass(item.key)}
              style={{ fontSize: 11.5 }}
            >
              {item.label}
            </button>
          ))}
        </div>
      </div>

      {error && <ErrorState message={error} />}
      {loading && !error && <SkeletonBlock height={280} />}

      {!loading && !error && (
        <div style={{ maxHeight: 360, overflowY: "auto", display: "flex", flexDirection: "column", gap: 6, paddingRight: 4 }}>
          {filtered.length === 0 && (
            <div style={{ padding: 30, textAlign: "center", color: "var(--text-muted)", fontSize: 13 }}>
              {filterClass === "crypto" && !query
                ? "Crypto assets unavailable (API feed unreachable or unauthorized for this account)."
                : `No tradable assets matched your query “${query}”.`}
            </div>
          )}
          {filtered.slice(0, 100).map((a) => {
            const checked = selected.includes(a.symbol);
            const isCrypto = a.asset_class === "crypto" || a.symbol.includes("/");
            const isOptions = a.asset_class === "options";

            return (
              <div
                key={a.symbol}
                onClick={() => a.tradable && toggle(a.symbol)}
                className={`card card--interactive ${checked ? "card--active" : ""}`}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: 14,
                  padding: "10px 16px",
                  borderRadius: "var(--radius-sm)",
                  cursor: a.tradable ? "pointer" : "not-allowed",
                  opacity: a.tradable ? 1 : 0.4,
                  background: checked ? "rgba(99, 102, 241, 0.12)" : "rgba(255, 255, 255, 0.02)",
                  border: checked ? "1px solid var(--accent-strong)" : "1px solid rgba(255, 255, 255, 0.04)",
                }}
              >
                <input
                  type="checkbox"
                  checked={checked}
                  disabled={!a.tradable}
                  onChange={() => toggle(a.symbol)}
                  style={{ accentColor: "var(--accent-strong)", width: 16, height: 16 }}
                />
                <div style={{ flex: 1 }}>
                  <div style={{ display: "flex", gap: 10, alignItems: "baseline" }}>
                    <span className="mono" style={{ fontWeight: 700, fontSize: 14, color: "var(--text-primary)" }}>
                      {a.symbol}
                    </span>
                    <span style={{ fontSize: 12.5, color: "var(--text-muted)" }}>{a.name}</span>
                  </div>
                </div>
                <span
                  className="mono"
                  style={{
                    fontSize: 10,
                    fontWeight: 700,
                    padding: "2px 7px",
                    borderRadius: "var(--radius-xs)",
                    background: isCrypto
                      ? "rgba(6, 182, 212, 0.15)"
                      : isOptions
                      ? "rgba(245, 158, 11, 0.15)"
                      : "rgba(99, 102, 241, 0.15)",
                    color: isCrypto
                      ? "var(--cyan)"
                      : isOptions
                      ? "#fbbf24"
                      : "var(--accent-strong)",
                  }}
                >
                  {isCrypto ? "CRYPTO" : isOptions ? "OPTIONS" : "EQUITY"} · {a.exchange}
                </span>
                {!a.tradable && (
                  <span className="mono" style={{ fontSize: 10, color: "var(--sell-strong)", fontWeight: 700 }}>
                    UNAVAILABLE
                  </span>
                )}
              </div>
            );
          })}
        </div>
      )}

      <div
        style={{
          marginTop: 16,
          paddingTop: 14,
          borderTop: "1px solid var(--hairline)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          fontSize: 12.5,
          color: "var(--text-muted)",
        }}
      >
        <span>
          <strong style={{ color: "var(--text-primary)" }}>{selected.length}</strong> asset{selected.length === 1 ? "" : "s"} selected
        </span>
        <span className="mono" style={{ fontSize: 11 }}>
          Deterministic sandbox: Agent is strictly restricted to chosen list
        </span>
      </div>
    </div>
  );
}
