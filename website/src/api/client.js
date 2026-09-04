const BASE = "/api";

class ApiError extends Error {
  constructor(message, status) {
    super(message);
    this.status = status;
  }
}

async function request(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    credentials: "include",
    headers: { "Content-Type": "application/json", ...options.headers },
    ...options,
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      detail = body.detail || detail;
    } catch {
      /* no json body */
    }
    throw new ApiError(detail, res.status);
  }

  if (res.status === 204) return null;
  return res.json();
}

export const api = {
  // Alpaca connection
  connect: (apiKey, secretKey, paper) =>
    request("/alpaca/connect", { method: "POST", body: JSON.stringify({ api_key: apiKey, secret_key: secretKey, paper }) }),
  disconnect: () => request("/alpaca/disconnect", { method: "POST" }),
  connectionStatus: () => request("/alpaca/status"),

  // Account
  getAccount: () => request("/account"),
  getPositions: () => request("/positions"),
  getOrders: () => request("/orders"),

  // Market
  getAssets: (search) => request(`/assets${search ? `?search=${encodeURIComponent(search)}` : ""}`),
  getLiveTickers: () => request("/market/live-tickers"),
  getMarketData: (symbol, timeframe = "15m") =>
    request(`/market/${encodeURIComponent(symbol)}?timeframe=${timeframe}`),

  // News
  getNews: (symbols) => request(`/news${symbols?.length ? `?symbols=${symbols.join(",")}` : ""}`),

  // Strategies
  getStrategies: () => request("/strategies"),

  // Automation
  startAutomation: (config) =>
    request("/automation/start", { method: "POST", body: JSON.stringify({ config, confirmed: true }) }),
  pauseAutomation: () => request("/automation/pause", { method: "POST" }),
  resumeAutomation: () => request("/automation/resume", { method: "POST" }),
  stopAutomation: () => request("/automation/stop", { method: "POST" }),
  emergencyStop: () => request("/automation/emergency-stop", { method: "POST" }),
  automationStatus: () => request("/automation/status"),
  executeTestTrade: (symbol = "BTC/USD") =>
    request(`/automation/test-trade?symbol=${encodeURIComponent(symbol)}`, { method: "POST" }),

  // Decisions / trades
  getDecisions: () => request("/decisions"),
  getTrades: () => request("/trades"),

  // Research & market intelligence (read-only; never places orders)
  getMarketRegime: () => request("/market-regime"),
  runDiscovery: () => request("/research/discover", { method: "POST" }),
  runBacktest: (strategy, symbol = "AAPL", timeframe = "1D", limit = 250) =>
    request(`/research/backtest?strategy=${encodeURIComponent(strategy)}&symbol=${encodeURIComponent(symbol)}&timeframe=${encodeURIComponent(timeframe)}&limit=${limit}`, { method: "POST" }),
  runResearchCycle: (strategy, symbol = "AAPL", timeframe = "1D", limit = 250) =>
    request(`/research/run?strategy=${encodeURIComponent(strategy)}&symbol=${encodeURIComponent(symbol)}&timeframe=${encodeURIComponent(timeframe)}&limit=${limit}`, { method: "POST" }),
  listBacktests: (limit = 20) => request(`/research/backtests?limit=${limit}`),

  // Agent activity
  getAgentEvents: (limit = 100) => request(`/agents/events?limit=${limit}`),
  getResearchStrategies: () => request("/research/strategies"),
};

export { ApiError };
