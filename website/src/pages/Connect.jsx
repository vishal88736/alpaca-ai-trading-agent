import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { useSession } from "../context/SessionContext";
import { useToast } from "../hooks/useToast";

export function Connect() {
  const [apiKey, setApiKey] = useState("");
  const [secretKey, setSecretKey] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);
  const { connect } = useSession();
  const { push } = useToast();
  const navigate = useNavigate();

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await connect(apiKey, secretKey, true);
      push("Connected to Alpaca paper trading.", "success");
      navigate("/dashboard");
    } catch (err) {
      setError(err.message || "Failed to connect. Check your API key and secret.");
    } finally {
      setSubmitting(false);
      setSecretKey("");
    }
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: 24,
        position: "relative",
      }}
    >
      <div
        className="card"
        style={{
          maxWidth: 480,
          width: "100%",
          padding: "36px 32px",
          position: "relative",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
          <Link to="/" style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 13, color: "var(--text-muted)" }}>
            ← Back to Home
          </Link>
          <span className="badge badge--paper">
            <span className="dot dot--pulse" />
            Paper Environment
          </span>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 12, marginBottom: 12 }}>
          <div
            style={{
              width: 32,
              height: 32,
              borderRadius: 10,
              background: "linear-gradient(135deg, #6366f1 0%, #06b6d4 100%)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              boxShadow: "0 0 16px rgba(99, 102, 241, 0.4)",
            }}
          >
            <span style={{ fontSize: 16 }}>🔑</span>
          </div>
          <h2 style={{ fontSize: 22, letterSpacing: "-0.02em" }}>Alpaca Authentication</h2>
        </div>

        <p style={{ fontSize: 13.5, color: "var(--text-secondary)", marginBottom: 24, lineHeight: 1.55 }}>
          Enter your Alpaca paper API credentials to authorize trading automation. Keys are encrypted in session memory and never persisted to local storage.
        </p>

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 18 }}>
          <Field
            label="Alpaca Paper API Key"
            placeholder="PK..."
            value={apiKey}
            onChange={setApiKey}
            required
            autoComplete="off"
          />
          <Field
            label="Alpaca Paper Secret Key"
            placeholder="••••••••••••••••••••"
            value={secretKey}
            onChange={setSecretKey}
            type="password"
            required
            autoComplete="off"
          />

          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              padding: "12px 16px",
              borderRadius: "var(--radius-sm)",
              background: "var(--warning-soft)",
              border: "1px solid rgba(245, 158, 11, 0.25)",
              fontSize: 12.5,
              color: "var(--warning-strong)",
            }}
          >
            <span style={{ fontWeight: 600 }}>Target Environment</span>
            <span className="mono" style={{ fontWeight: 700 }}>
              PAPER TRADING (SAFE)
            </span>
          </div>

          {error && (
            <div
              style={{
                padding: "12px 16px",
                borderRadius: "var(--radius-sm)",
                background: "var(--sell-soft)",
                border: "1px solid rgba(244, 63, 94, 0.3)",
                fontSize: 12.5,
                color: "var(--sell-strong)",
              }}
            >
              {error}
            </div>
          )}

          <button className="btn btn--primary btn--lg" type="submit" disabled={submitting} style={{ marginTop: 8 }}>
            {submitting ? "Verifying Credentials…" : "Authenticate & Open Terminal →"}
          </button>
        </form>

        <p style={{ fontSize: 12, marginTop: 22, textAlign: "center", color: "var(--text-muted)" }}>
          Need API keys? Generate paper credentials instantly in the{" "}
          <a
            href="https://app.alpaca.markets/signup"
            target="_blank"
            rel="noreferrer"
            style={{ color: "var(--accent-strong)", fontWeight: 600 }}
          >
            Alpaca Developer Console ↗
          </a>
        </p>
      </div>
    </div>
  );
}

function Field({ label, placeholder, value, onChange, type = "text", required, autoComplete }) {
  return (
    <label style={{ display: "flex", flexDirection: "column", gap: 7 }}>
      <span style={{ fontSize: 12.5, fontWeight: 600, color: "var(--text-secondary)" }}>{label}</span>
      <input
        type={type}
        value={value}
        placeholder={placeholder}
        required={required}
        autoComplete={autoComplete}
        onChange={(e) => onChange(e.target.value)}
        style={{
          padding: "12px 14px",
          borderRadius: "var(--radius-sm)",
          border: "1px solid var(--hairline-strong)",
          background: "rgba(5, 7, 14, 0.8)",
          color: "var(--text-primary)",
          fontFamily: "var(--font-mono)",
          fontSize: 13.5,
          transition: "border-color 0.15s ease",
        }}
      />
    </label>
  );
}

