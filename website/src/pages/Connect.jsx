import { useState } from "react";
import { useNavigate } from "react-router-dom";
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
      // Never keep raw credentials in this component's memory longer than needed.
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
        padding: 20,
      }}
    >
      <div className="card" style={{ maxWidth: 440, width: "100%", padding: 32 }}>
        <div className="eyebrow" style={{ marginBottom: 8 }}>
          Step 1 of 1
        </div>
        <h2 style={{ fontSize: 22, marginBottom: 8 }}>Connect your Alpaca account</h2>
        <p style={{ fontSize: 13.5, marginBottom: 20 }}>
          This app is built for Alpaca's <strong style={{ color: "var(--warning)" }}>paper-trading</strong>{" "}
          environment during the hackathon. Your keys are sent directly to the backend over HTTPS and held only in a
          server-side session — never stored in the browser, never logged, never committed anywhere.
        </p>

        <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: 14 }}>
          <Field label="Alpaca API Key" value={apiKey} onChange={setApiKey} required autoComplete="off" />
          <Field
            label="Alpaca Secret Key"
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
              padding: "10px 14px",
              borderRadius: 8,
              background: "var(--warning-soft)",
              border: "1px solid rgba(245,166,35,0.3)",
              fontSize: 12.5,
              color: "var(--warning)",
            }}
          >
            <span>Environment</span>
            <span className="mono">PAPER TRADING</span>
          </div>

          {error && (
            <div
              style={{
                padding: "10px 14px",
                borderRadius: 8,
                background: "var(--sell-soft)",
                border: "1px solid rgba(255,93,118,0.3)",
                fontSize: 12.5,
                color: "var(--sell)",
              }}
            >
              {error}
            </div>
          )}

          <button className="btn btn--primary" type="submit" disabled={submitting} style={{ marginTop: 6 }}>
            {submitting ? "Validating…" : "Connect"}
          </button>
        </form>

        <p style={{ fontSize: 11.5, marginTop: 18, textAlign: "center" }}>
          Don't have a paper account? Create one for free in the{" "}
          <a href="https://app.alpaca.markets/signup" target="_blank" rel="noreferrer" style={{ color: "var(--accent-strong)" }}>
            Alpaca dashboard
          </a>
          .
        </p>
      </div>
    </div>
  );
}

function Field({ label, value, onChange, type = "text", required, autoComplete }) {
  return (
    <label style={{ display: "flex", flexDirection: "column", gap: 6 }}>
      <span style={{ fontSize: 12.5, color: "var(--text-secondary)" }}>{label}</span>
      <input
        type={type}
        value={value}
        required={required}
        autoComplete={autoComplete}
        onChange={(e) => onChange(e.target.value)}
        style={{
          padding: "11px 14px",
          borderRadius: 8,
          border: "1px solid var(--hairline-strong)",
          background: "var(--void)",
          color: "var(--text-primary)",
          fontFamily: "var(--font-mono)",
          fontSize: 13.5,
        }}
      />
    </label>
  );
}
