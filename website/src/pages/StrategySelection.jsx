import { useNavigate } from "react-router-dom";
import { AppShell } from "../components/Layout/AppShell";
import { StrategySelector } from "../components/Strategy/StrategySelector";
import { StrategyConfigForm } from "../components/Strategy/StrategyConfigForm";
import { useAutomationSetup } from "../context/AutomationSetupContext";

export function StrategySelection() {
  const { strategy, setStrategy, strategyConfig, setStrategyConfig } = useAutomationSetup();
  const navigate = useNavigate();

  return (
    <AppShell>
      <div style={{ marginBottom: 24 }}>
        <div className="eyebrow">Step 1 of 3</div>
        <h2 style={{ fontSize: 24, marginTop: 6 }}>Select a strategy</h2>
        <p style={{ marginTop: 6, fontSize: 13.5 }}>
          Choose the strategy the automation engine will run. Configuration fields below map directly to the
          strategy's stub in <code className="mono">model/strategies/</code>.
        </p>
      </div>

      <StrategySelector selected={strategy} onSelect={setStrategy} />

      {strategy && (
        <div style={{ marginTop: 20 }}>
          <StrategyConfigForm strategyKey={strategy} values={strategyConfig} onChange={setStrategyConfig} />
        </div>
      )}

      <div style={{ display: "flex", justifyContent: "flex-end", marginTop: 24 }}>
        <button className="btn btn--primary" disabled={!strategy} onClick={() => navigate("/assets")}>
          Continue to Asset Selection
        </button>
      </div>
    </AppShell>
  );
}
