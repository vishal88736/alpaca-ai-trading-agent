import { createContext, useContext, useState } from "react";

const DEFAULT_RISK = {
  max_position_pct: 10,
  max_portfolio_exposure_pct: 50,
  max_order_size_usd: 1000,
  max_daily_loss_pct: 2,
  max_trades_per_day: 20,
  stop_loss_pct: 2,
  take_profit_pct: 4,
};

const AutomationSetupContext = createContext(null);

export function AutomationSetupProvider({ children }) {
  const [strategy, setStrategy] = useState(null);
  const [strategyConfig, setStrategyConfig] = useState({});
  const [assets, setAssets] = useState([]);
  const [timeframe, setTimeframe] = useState("15m");
  const [risk, setRisk] = useState(DEFAULT_RISK);

  const value = {
    strategy,
    setStrategy,
    strategyConfig,
    setStrategyConfig,
    assets,
    setAssets,
    timeframe,
    setTimeframe,
    risk,
    setRisk,
  };

  return <AutomationSetupContext.Provider value={value}>{children}</AutomationSetupContext.Provider>;
}

export function useAutomationSetup() {
  const ctx = useContext(AutomationSetupContext);
  if (!ctx) throw new Error("useAutomationSetup must be used within AutomationSetupProvider");
  return ctx;
}
