import { useEffect, useState } from "react";
import { AppShell } from "../components/Layout/AppShell";
import { DecisionLog } from "../components/Decisions/DecisionLog";
import { api } from "../api/client";

export function DecisionLogPage() {
  const [decisions, setDecisions] = useState(null);
  const [error, setError] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        const data = await api.getDecisions();
        if (!cancelled) {
          setDecisions(data);
          setError(false);
        }
      } catch {
        if (!cancelled) setError(true);
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    const interval = setInterval(load, 8000);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  return (
    <AppShell>
      <div style={{ marginBottom: 24 }}>
        <div className="eyebrow">Full History</div>
        <h2 style={{ fontSize: 24, marginTop: 6 }}>AI Decision Log</h2>
        <p style={{ marginTop: 6, fontSize: 13.5 }}>
          Every decision the pipeline produced, approved or rejected. Reasoning shown here is a concise, user-facing
          explanation — not raw model chain-of-thought.
        </p>
      </div>

      <DecisionLog decisions={decisions} loading={loading} error={error} />
    </AppShell>
  );
}
