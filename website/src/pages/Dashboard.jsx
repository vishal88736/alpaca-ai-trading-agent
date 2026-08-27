import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { AppShell } from "../components/Layout/AppShell";
import { AccountSummary, AccountDetailRow } from "../components/Account/AccountSummary";
import { PositionsList } from "../components/Positions/PositionsList";
import { MarketChart } from "../components/Chart/MarketChart";
import { PnlChart } from "../components/Chart/PnlChart";
import { AutomationMonitor } from "../components/Automation/AutomationMonitor";
import { NewsPanel } from "../components/News/NewsPanel";
import { RecentTrades } from "../components/Trades/RecentTrades";
import { useAutomationSetup } from "../context/AutomationSetupContext";
import { api, ApiError } from "../api/client";
import { useToast } from "../hooks/useToast";

const POLL_MS = 8000;

export function Dashboard() {
  const [account, setAccount] = useState(null);
  const [accountError, setAccountError] = useState(false);
  const [positions, setPositions] = useState(null);
  const [positionsError, setPositionsError] = useState(false);
  const [orders, setOrders] = useState(null);
  const [ordersError, setOrdersError] = useState(false);
  const [automationStatus, setAutomationStatus] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedSymbol, setSelectedSymbol] = useState(null);
  const [pnlSeries, setPnlSeries] = useState([]);

  const { assets } = useAutomationSetup();
  const { push } = useToast();

  useEffect(() => {
    let cancelled = false;

    async function load() {
      const results = await Promise.allSettled([
        api.getAccount(),
        api.getPositions(),
        api.getOrders(),
        api.automationStatus(),
      ]);
      if (cancelled) return;

      const [accRes, posRes, ordRes, autoRes] = results;

      if (accRes.status === "fulfilled") {
        setAccount(accRes.value);
        setAccountError(false);
        setPnlSeries((prev) => {
          const next = [...prev, { label: new Date().toLocaleTimeString(), value: accRes.value.portfolio_value }];
          return next.slice(-40);
        });
      } else {
        setAccountError(true);
      }

      if (posRes.status === "fulfilled") {
        setPositions(posRes.value);
        setPositionsError(false);
        if (!selectedSymbol && posRes.value.length > 0) setSelectedSymbol(posRes.value[0].symbol);
      } else {
        setPositionsError(true);
      }

      if (ordRes.status === "fulfilled") {
        setOrders(ordRes.value);
        setOrdersError(false);
      } else {
        setOrdersError(true);
      }

      if (autoRes.status === "fulfilled") {
        setAutomationStatus(autoRes.value);
      }

      setLoading(false);
    }

    load();
    const interval = setInterval(load, POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function handlePause() {
    try {
      setAutomationStatus(await api.pauseAutomation());
    } catch (err) {
      push(err instanceof ApiError ? err.message : "Failed to pause automation", "error");
    }
  }
  async function handleResume() {
    try {
      setAutomationStatus(await api.resumeAutomation());
    } catch (err) {
      push(err instanceof ApiError ? err.message : "Failed to resume automation", "error");
    }
  }
  async function handleStop() {
    try {
      setAutomationStatus(await api.stopAutomation());
      push("Automation stopped.", "info");
    } catch (err) {
      push(err instanceof ApiError ? err.message : "Failed to stop automation", "error");
    }
  }
  async function handleEmergencyStop() {
    try {
      setAutomationStatus(await api.emergencyStop());
      push("Emergency stop engaged. All new orders are blocked.", "error");
    } catch (err) {
      push(err instanceof ApiError ? err.message : "Failed to trigger emergency stop", "error");
    }
  }

  const tickerItems = (positions || []).map((p) => ({
    symbol: p.symbol,
    price: p.current_price,
    changePct: p.unrealized_pl_pct,
  }));

  return (
    <AppShell tickerItems={tickerItems}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: 20 }}>
        <div>
          <div className="eyebrow">Live Overview</div>
          <h2 style={{ fontSize: 24, marginTop: 4 }}>Trading Dashboard</h2>
        </div>
        {!automationStatus || automationStatus.state === "IDLE" ? (
          <Link to="/strategy" className="btn btn--primary">
            Set Up Automation
          </Link>
        ) : null}
      </div>

      <div style={{ marginBottom: 20 }}>
        <AccountSummary account={account} loading={loading} error={accountError} />
      </div>

      <div style={{ marginBottom: 20 }}>
        <MarketChart symbol={selectedSymbol || assets[0]} />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1.3fr 1fr", gap: 20, marginBottom: 20, alignItems: "start" }}>
        <div className="card" style={{ padding: 20 }}>
          <div className="eyebrow" style={{ marginBottom: 14 }}>
            Current Positions
          </div>
          <PositionsList positions={positions} loading={loading} error={positionsError} onSelect={setSelectedSymbol} />
        </div>

        <AutomationMonitor
          status={automationStatus}
          onPause={handlePause}
          onResume={handleResume}
          onStop={handleStop}
          onEmergencyStop={handleEmergencyStop}
        />
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1.3fr 1fr", gap: 20, marginBottom: 20, alignItems: "start" }}>
        <div className="card" style={{ padding: 20 }}>
          <div className="eyebrow" style={{ marginBottom: 14 }}>
            Portfolio Value Over Time
          </div>
          <PnlChart series={pnlSeries} />
        </div>
        <AccountDetailRow account={account} />
      </div>

      <div style={{ marginBottom: 20 }}>
        <NewsPanel symbols={assets} />
      </div>

      <div className="card" style={{ padding: 20 }}>
        <div className="eyebrow" style={{ marginBottom: 14 }}>
          Recent Trades / Orders
        </div>
        <RecentTrades orders={orders} loading={loading} error={ordersError} />
      </div>
    </AppShell>
  );
}
