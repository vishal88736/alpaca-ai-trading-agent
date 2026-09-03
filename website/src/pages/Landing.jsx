import { useNavigate } from "react-router-dom";

export function Landing() {
  const navigate = useNavigate();

  return (
    <div style={{ minHeight: "100vh", display: "flex", flexDirection: "column" }}>
      <header
        style={{
          padding: "18px 36px",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          borderBottom: "1px solid var(--hairline)",
          background: "rgba(5, 7, 14, 0.8)",
          backdropFilter: "blur(20px)",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div
            style={{
              width: 28,
              height: 28,
              borderRadius: 8,
              background: "linear-gradient(135deg, #6366f1 0%, #06b6d4 100%)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              boxShadow: "0 0 16px rgba(99, 102, 241, 0.4)",
            }}
          >
            <span style={{ fontSize: 14, color: "#fff", fontWeight: 800 }}>⚡</span>
          </div>
          <span style={{ fontFamily: "var(--font-display)", fontWeight: 800, fontSize: 16, letterSpacing: "-0.02em" }}>
            SIGNAL<span style={{ color: "var(--accent-strong)" }}>/</span>TERMINAL
          </span>
        </div>
        <span className="badge badge--paper">
          <span className="dot dot--pulse" />
          Paper Trading Terminal
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
          padding: "60px 24px",
          position: "relative",
        }}
      >
        <div
          className="badge badge--neutral"
          style={{
            marginBottom: 24,
            padding: "6px 14px",
            borderColor: "rgba(99, 102, 241, 0.3)",
            background: "rgba(99, 102, 241, 0.08)",
          }}
        >
          <span style={{ color: "var(--accent-strong)" }}>✨ Next-Gen Autonomous Trading</span>
        </div>

        <h1
          style={{
            fontSize: "clamp(36px, 6vw, 62px)",
            maxWidth: 860,
            lineHeight: 1.08,
            letterSpacing: "-0.03em",
          }}
        >
          An AI agent that <span style={{ color: "var(--accent-strong)", textShadow: "0 0 30px rgba(99, 102, 241, 0.4)" }}>reasons</span>,
          paired with a risk engine that <span style={{ color: "var(--buy-strong)", textShadow: "0 0 30px rgba(16, 185, 129, 0.4)" }}>decides</span>.
        </h1>

        <p style={{ maxWidth: 620, marginTop: 22, fontSize: 16.5, color: "var(--text-secondary)", lineHeight: 1.6 }}>
          Run official Alpaca quantitative strategies with real-time AI sentiment orchestration and a deterministic risk engine protecting your paper account.
        </p>

        <div style={{ display: "flex", gap: 14, marginTop: 36 }}>
          <button className="btn btn--primary btn--lg" onClick={() => navigate("/connect")}>
            Launch Trading Terminal →
          </button>
          <a
            className="btn btn--ghost btn--lg"
            href="https://alpaca.markets/docs/"
            target="_blank"
            rel="noreferrer"
          >
            Alpaca Documentation
          </a>
        </div>

        <div
          style={{
            marginTop: 70,
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))",
            gap: 18,
            maxWidth: 960,
            width: "100%",
          }}
        >
          {[
            ["5", "Quantitative Models", "Supertrend, Mean Reversion, DeX/CeX Arb, Market Making, Funding Basis"],
            ["100%", "Risk Filter Coverage", "Deterministic limits ensure no signal bypasses portfolio safety guardrails"],
            ["Live", "Crypto News Feed", "Keyless real-time headlines and sentiment analysis from cryptocurrency.cv"],
          ].map(([stat, title, desc]) => (
            <div key={title} className="card card--interactive" style={{ padding: "24px 22px", textAlign: "left" }}>
              <div
                className="mono"
                style={{
                  fontSize: 32,
                  fontWeight: 800,
                  color: "var(--accent-strong)",
                  letterSpacing: "-0.03em",
                }}
              >
                {stat}
              </div>
              <div style={{ fontSize: 15, fontWeight: 700, marginTop: 8, color: "var(--text-primary)" }}>{title}</div>
              <div style={{ fontSize: 12.5, color: "var(--text-muted)", marginTop: 6, lineHeight: 1.5 }}>{desc}</div>
            </div>
          ))}
        </div>
      </main>

      <footer
        style={{
          textAlign: "center",
          padding: "24px",
          fontSize: 12,
          color: "var(--text-muted)",
          borderTop: "1px solid var(--hairline)",
          background: "rgba(5, 7, 14, 0.6)",
        }}
      >
        Signal/Terminal — Built for the Alpaca Ecosystem. Paper trading simulation only.
      </footer>
    </div>
  );
}

