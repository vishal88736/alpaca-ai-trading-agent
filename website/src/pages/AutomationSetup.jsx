import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { AppShell } from "../components/Layout/AppShell";
import { AutomationConfigPanel } from "../components/Automation/AutomationConfigPanel";
import { AutomationSummary } from "../components/Automation/AutomationMonitor";
import { ConfirmDialog } from "../components/Common/ConfirmDialog";
import { useAutomationSetup } from "../context/AutomationSetupContext";
import { useToast } from "../hooks/useToast";
import { api } from "../api/client";

export function AutomationSetup() {
  const { strategy, strategyConfig, assets, timeframe, setTimeframe, risk, setRisk } = useAutomationSetup();
  const [confirmOpen, setConfirmOpen] = useState(false);
  const [starting, setStarting] = useState(false);
  const { push } = useToast();
  const navigate = useNavigate();

  const ready = !!strategy && assets.length > 0;

  async function handleStart() {
    setStarting(true);
    try {
      await api.startAutomation({
        strategy,
        assets,
        timeframe,
        risk,
        paper_trading: true,
      });
      push("Automation started.", "success");
      navigate("/dashboard");
    } catch (err) {
      push(err.message || "Failed to start automation.", "error");
    } finally {
      setStarting(false);
      setConfirmOpen(false);
    }
  }

  if (!ready) {
    return (
      <AppShell>
        <div className="card" style={{ padding: 32, textAlign: "center" }}>
          <h3 style={{ marginBottom: 8 }}>Setup incomplete</h3>
          <p style={{ marginBottom: 16 }}>Select a strategy and at least one asset before configuring automation.</p>
          <button className="btn btn--primary" onClick={() => navigate("/strategy")}>
            Go to Strategy Selection
          </button>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div style={{ marginBottom: 24 }}>
        <div className="eyebrow">Step 3 of 3</div>
        <h2 style={{ fontSize: 24, marginTop: 6 }}>Configure & review automation</h2>
        <p style={{ marginTop: 6, fontSize: 13.5 }}>
          These limits are enforced by the deterministic risk engine on every trade — the AI orchestrator cannot
          bypass them.
        </p>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1.6fr 1fr", gap: 20, alignItems: "start" }}>
        <AutomationConfigPanel risk={risk} timeframe={timeframe} onRiskChange={setRisk} onTimeframeChange={setTimeframe} />
        <AutomationSummary strategyName={strategy} assets={assets} risk={risk} timeframe={timeframe} />
      </div>

      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 24 }}>
        <button className="btn btn--ghost" onClick={() => navigate("/assets")}>
          Back
        </button>
        <button className="btn btn--primary" onClick={() => setConfirmOpen(true)}>
          Start Automation
        </button>
      </div>

      <ConfirmDialog
        open={confirmOpen}
        title="Start automated paper trading?"
        description={`This will begin autonomous trading with the ${strategy} strategy on ${assets.length} asset(s) in Alpaca's PAPER TRADING environment. Every trade still passes through the risk engine before execution. You can pause, resume, or emergency-stop at any time from the dashboard.`}
        confirmLabel={starting ? "Starting…" : "Start Automation"}
        onConfirm={handleStart}
        onCancel={() => setConfirmOpen(false)}
      />
    </AppShell>
  );
}
