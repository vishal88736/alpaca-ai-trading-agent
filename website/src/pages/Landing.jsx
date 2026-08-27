import { useNavigate } from "react-router-dom";

export function Landing() {
  const navigate = useNavigate();

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <header style={{ padding: "24px 32px", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
        <div style={{ display: "flex", alignItems: "center", gap: 9 }}>
          <span
            style={{
              width: 9,
              height: 9,
              borderRadius: 2,
              background: "linear-gradient(135deg, var(--accent), var(--buy))",
              display: "inline-block",
            }}
          />
          <span style={{ fontFamily: "var(--font-display)", fontWeight: 700, fontSize: 15 }}>
            SIGNAL<span style={{ color: "var(--accent)" }}>/</span>TERMINAL
          </span>
        </div>
        <span className="badge badge--paper">
          <span className="dot dot--pulse" />
          Paper Trading — Hackathon Build
        </span>
      </header>

      <main
        style={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          justifyContent: "center",
          alignItems: "center",
          textAlign: "center",
          padding: "40px 20px",
        }}
      >
        <div className="eyebrow" style={{ marginBottom: 18 }}>
          Autonomous trading, on Alpaca paper accounts
        </div>
        <h1 style={{ fontSize: "clamp(32px, 6vw, 56px)", maxWidth: 780, lineHeight: 1.08 }}>
          An AI trading agent that <span style={{ color: "var(--accent)" }}>reasons</span>, then a risk engine
          that <span style={{ color: "var(--buy)" }}>decides</span>.
        </h1>
        <p style={{ maxWidth: 560, marginTop: 20, fontSize: 15.5 }}>
          Connect an Alpaca paper-trading account, pick a strategy, choose the assets it's allowed to touch, and
          watch every signal pass through a deterministic risk engine before it ever reaches the broker.
        </p>

        <div style={{ display: "flex", gap: 12, marginTop: 32 }}>
          <button className="btn btn--primary" onClick={() => navigate("/connect")}>
            Connect Alpaca Account
          </button>
          <a className="btn btn--ghost" href="https://alpaca.markets/docs/" target="_blank" rel="noreferrer">
            Alpaca Docs
          </a>
        </div>

        <div
          style={{
            marginTop: 60,
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))",
            gap: 14,
            maxWidth: 900,
            width: "100%",
          }}
        >
          {[
            ["5", "Trading strategies, stubbed & ready for your logic"],
            ["1", "Deterministic risk engine, no LLM bypass"],
            ["100%", "Paper trading — no real capital at risk"],
          ].map(([stat, label]) => (
            <div key={label} className="card" style={{ padding: 20 }}>
              <div className="mono" style={{ fontSize: 28, fontWeight: 600, color: "var(--accent-strong)" }}>
                {stat}
              </div>
              <div style={{ fontSize: 12.5, color: "var(--text-muted)", marginTop: 6 }}>{label}</div>
            </div>
          ))}
        </div>
      </main>

      <footer style={{ textAlign: "center", padding: "20px", fontSize: 11.5, color: "var(--text-muted)" }}>
        Built for the Alpaca hackathon. Not financial advice. Paper trading only.
      </footer>
    </div>
  );
}
