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
    <div className="card" style={{ padding: 20 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 14 }}>
        <div className="eyebrow">Market News</div>
        <span className="mono" style={{ fontSize: 10, color: "var(--text-muted)" }}>
          Powered by cryptocurrency.cv
        </span>
      </div>

      {state.loading && <SkeletonBlock height={160} />}

      {!state.loading && !state.available && (
        <EmptyState
          title="Data unavailable"
          description="Live crypto news feed is currently unreachable from cryptocurrency.cv."
        />
      )}

      {!state.loading && state.available && state.articles.length === 0 && (
        <EmptyState title="No news right now" description="Check back shortly, or broaden your asset selection." />
      )}

      {!state.loading && state.available && state.articles.length > 0 && (
        <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          {state.articles.map((a, i) => (
            <div key={i} style={{ paddingBottom: 12, borderBottom: i < state.articles.length - 1 ? "1px solid var(--hairline)" : "none" }}>
              <div style={{ display: "flex", justifyContent: "space-between", gap: 10 }}>
                <span className="mono" style={{ fontSize: 10.5, color: "var(--accent-strong)", fontWeight: 600 }}>
                  {a.related_symbol || "CRYPTO"}
                </span>
                <span className="mono" style={{ fontSize: 10.5, color: "var(--text-muted)" }}>
                  {a.source} · {a.published_at ? a.published_at.slice(0, 10) : ""}
                </span>
              </div>
              <div style={{ fontSize: 13.5, marginTop: 4, lineHeight: 1.4 }}>
                {a.url ? (
                  <a
                    href={a.url}
                    target="_blank"
                    rel="noreferrer"
                    style={{ color: "inherit", textDecoration: "none" }}
                    onMouseOver={(e) => (e.currentTarget.style.textDecoration = "underline")}
                    onMouseOut={(e) => (e.currentTarget.style.textDecoration = "none")}
                  >
                    {a.headline}
                  </a>
                ) : (
                  a.headline
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

