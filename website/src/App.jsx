import { Navigate, Route, Routes } from "react-router-dom";
import { SessionProvider, useSession } from "./context/SessionContext";
import { AutomationSetupProvider } from "./context/AutomationSetupContext";
import { ThemeProvider } from "./context/ThemeContext";
import { ToastProvider } from "./hooks/useToast";
import { Landing } from "./pages/Landing";
import { Connect } from "./pages/Connect";
import { Dashboard } from "./pages/Dashboard";
import { StrategySelection } from "./pages/StrategySelection";
import { AssetSelection } from "./pages/AssetSelection";
import { AutomationSetup } from "./pages/AutomationSetup";
import { DecisionLogPage } from "./pages/DecisionLogPage";
import { Research } from "./pages/Research";
import { Agents } from "./pages/Agents";

function RequireConnection({ children }) {
  const { connected, checking } = useSession();

  if (checking) {
    return (
      <div style={{ minHeight: "100vh", display: "flex", alignItems: "center", justifyContent: "center" }}>
        <span className="mono muted">Checking connection…</span>
      </div>
    );
  }

  if (!connected) return <Navigate to="/connect" replace />;
  return children;
}

function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/connect" element={<Connect />} />
      <Route
        path="/dashboard"
        element={
          <RequireConnection>
            <Dashboard />
          </RequireConnection>
        }
      />
      <Route
        path="/strategy"
        element={
          <RequireConnection>
            <StrategySelection />
          </RequireConnection>
        }
      />
      <Route
        path="/assets"
        element={
          <RequireConnection>
            <AssetSelection />
          </RequireConnection>
        }
      />
      <Route
        path="/automation"
        element={
          <RequireConnection>
            <AutomationSetup />
          </RequireConnection>
        }
      />
      <Route
        path="/decisions"
        element={
          <RequireConnection>
            <DecisionLogPage />
          </RequireConnection>
        }
      />
      <Route
        path="/research"
        element={
          <RequireConnection>
            <Research />
          </RequireConnection>
        }
      />
      <Route
        path="/agents"
        element={
          <RequireConnection>
            <Agents />
          </RequireConnection>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}

export default function App() {
  return (
    <ThemeProvider>
      <SessionProvider>
        <ToastProvider>
          <AutomationSetupProvider>
            <AppRoutes />
          </AutomationSetupProvider>
        </ToastProvider>
      </SessionProvider>
    </ThemeProvider>
  );
}
