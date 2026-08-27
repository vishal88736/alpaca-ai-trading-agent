import { useEffect, useState } from "react";
import { api } from "../../api/client";
import { SkeletonBlock } from "../Common/SkeletonLoader";
import { EmptyState } from "../Common/EmptyState";

export function NewsPanel({ symbols }) {
  const [state, setState] = useState({ loading: true, available: true, articles: [] });

  useEffect(() => {
    let cancelled = false;
    setState((s) => ({ ...s, loading: true }));
    api
      .getNews(symbols)
      .then((res) => !cancelled && setState({ loading: false, available: res.available, articles: res.articles || [] }))
      .catch(() => !cancelled && setState({ loading: false, available: false, articles: [] }));
    return () => {
      cancelled = true;
    };
  }, [symbols]);

  return (
    <div className="card" style={{ padding: "22px 24px" }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 16 }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div className="eyebrow">Real-Time Market Intelligence</div>
          <span className="badge badge--neutral" style={{ fontSize: 10 }}>
            Live Stream
          </span>
        </div>
        <a
          href="https://cryptocurrency.cv"
          target="_blank"
          rel="noreferrer"
          className="mono"
          style={{ fontSize: 11, color: "var(--accent-strong)", opacity: 0.85 }}
        >
          Source: cryptocurrency.cv ↗
        </a>
      </div>

      {state.loading && <SkeletonBlock height={160} />}

      {!state.loading && !state.available && (
        <EmptyState
          title="Data stream unavailable"
          description="Live crypto news feed is currently unreachable from cryptocurrency.cv."
        />
      )}

      {!state.loading && state.available && state.articles.length === 0 && (
        <EmptyState title="No active headlines" description="Check back shortly or broaden your asset selection." />
      )}

      {!state.loading && state.available && state.articles.length > 0 && (
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(280px, 1fr))", gap: 12 }}>
          {state.articles.slice(0, 8).map((a, i) => (
            <a
              key={i}
              href={a.url || "#"}
              target={a.url ? "_blank" : undefined}
              rel="noreferrer"
              className="card card--interactive"
              style={{
                padding: "14px 16px",
                background: "rgba(255, 255, 255, 0.02)",
                border: "1px solid rgba(255, 255, 255, 0.05)",
                display: "flex",
                flexDirection: "column",
                justifyContent: "space-between",
                gap: 10,
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", gap: 8 }}>
                <span
                  className="mono"
                  style={{
                    fontSize: 10.5,
                    color: "var(--accent-strong)",
                    fontWeight: 700,
                    padding: "2px 6px",
                    borderRadius: "var(--radius-xs)",
                    background: "var(--accent-soft)",
                  }}
                >
                  {a.related_symbol || "CRYPTO"}
                </span>
                <span className="mono" style={{ fontSize: 10.5, color: "var(--text-muted)" }}>
                  {a.source}
                </span>
              </div>

              <div
                style={{
                  fontSize: 13.5,
                  fontWeight: 500,
                  color: "var(--text-primary)",
                  lineHeight: 1.45,
                  display: "-webkit-box",
                  WebkitLineClamp: 2,
                  WebkitBoxOrient: "vertical",
                  overflow: "hidden",
                }}
              >
                {a.headline}
              </div>

              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", fontSize: 11, color: "var(--text-muted)" }}>
                <span>{a.published_at ? new Date(a.published_at).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" }) : "Just now"}</span>
                {a.url && <span style={{ color: "var(--accent-strong)" }}>Read Article ↗</span>}
              </div>
            </a>
          ))}
        </div>
      )}
    </div>
  );
}


