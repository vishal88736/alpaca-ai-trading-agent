import { useNavigate } from "react-router-dom";
import { AppShell } from "../components/Layout/AppShell";
import { AssetSelector } from "../components/Assets/AssetSelector";
import { useAutomationSetup } from "../context/AutomationSetupContext";

export function AssetSelection() {
  const { assets, setAssets, strategy } = useAutomationSetup();
  const navigate = useNavigate();

  return (
    <AppShell>
      <div style={{ marginBottom: 24 }}>
        <div className="eyebrow">Step 2 of 3</div>
        <h2 style={{ fontSize: 24, marginTop: 6 }}>Select tradable assets</h2>
        <p style={{ marginTop: 6, fontSize: 13.5 }}>
          The <strong>{strategy || "selected"}</strong> strategy will only ever be allowed to trade the assets you
          select here — this list becomes the risk engine's asset allowlist.
        </p>
      </div>

      <AssetSelector selected={assets} onChange={setAssets} />

      <div style={{ display: "flex", justifyContent: "space-between", marginTop: 24 }}>
        <button className="btn btn--ghost" onClick={() => navigate("/strategy")}>
          Back
        </button>
        <button className="btn btn--primary" disabled={assets.length === 0} onClick={() => navigate("/automation")}>
          Continue to Automation Setup
        </button>
      </div>
    </AppShell>
  );
}
