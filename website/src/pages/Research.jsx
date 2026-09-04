import { useEffect, useState } from "react";
import { AppShell } from "../components/Layout/AppShell";
import { api, ApiError } from "../api/client";
import { useToast } from "../hooks/useToast";

function Metric({ label, value }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
      <span className="eyebrow">{label}</span>
      <span className="mono" style={{ fontSize: 16, fontWeight: 700 }}>
        {value}
      </span>
    </div>
  );
}

function VerdictBadge({ verdict }) {
  const cls =
    verdict === "PASS" ? "badge badge--live" : verdict === "REJECT" ? "badge badge--danger" : "badge badge--paper";
  return <span className={cls}>{verdict}</span>;
}

export function Research() {
  const [strategies, setStrategies] = useState([]);
  const [strategy, setStrategy] = useState("momentum");
  const [symbol, setSymbol] = useState("AAPL");
  const [timeframe, setTimeframe] = useState("1D");
  const [running, setRunning] = useState(false);
  const [result, setResult] = useState(null);
  const [history, setHistory] = useState([]);
  const { push } = useToast();

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const [strats, backtests] = await Promise.all([api.getResearchStrategies(), api.listBacktests(10)]);
        if (cancelled) return;
        setStrategies(strats);
        if (strats.length > 0) setStrategy(strats[0].key);
        setHistory(backtests);
      } catch {
        /* offline — page still renders */
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, []);

  const selected = strategies.find((s) => s.key === strategy);
  const isLive = selected?.execution_mode === "live";

  async function handleRun() {
    setRunning(true);
    setResult(null);
    try {
      const res = await api.runResearchCycle(strategy, symbol, timeframe, 250);
      setResult(res);
      push("Research cycle complete. No orders were placed.", "success");
      try {
        setHistory(await api.listBacktests(10));
      } catch {
        /* ignore */
      }
    } catch (err) {
      push(err instanceof ApiError ? err.message : "Research cycle failed", "error");
    } finally {
      setRunning(false);
    }
  }

  const bt = result?.backtest;
  const adv = result?.adversary_report;
  const strat = result?.strategy;

  return (
    <AppShell>
      <div style={{ marginBottom: 24 }}>
        <div className="eyebrow">Discovery → Backtest → Adversary → Edge Score</div>
        <h2 style={{ fontSize: 24, marginTop: 6 }}>Strategy Research Lab</h2>
        <p style={{ marginTop: 6, fontSize: 13.5 }}>
          Research is strictly read-only: it backtests real strategy logic on real historical bars. It never places
          orders and never claims profitability before out-of-sample validation.
        </p>
      </div>

      <div className="card" style={{ padding: 20, marginBottom: 20 }}>
        <div style={{ display: "flex", gap: 12, flexWrap: "wrap", alignItems: "flex-end" }}>
          <label style={{ display: "flex", flexDirection: "column", gap: 6, fontSize: 12.5 }}>
            <span className="eyebrow">Strategy</span>
            <select value={strategy} onChange={(e) => setStrategy(e.target.value)} style={selectStyle}>
              {strategies.map((s) => (
                <option key={s.key} value={s.key}>
                  {s.display_name || s.key} ({s.execution_mode})
                </option>
              ))}
            </select>
          </label>
          <label style={{ display: "flex", flexDirection: "column", gap: 6, fontSize: 12.5 }}>
            <span className="eyebrow">Symbol</span>
            <input value={symbol} onChange={(e) => setSymbol(e.target.value.toUpperCase())} style={selectStyle} />
          </label>
          <label style={{ display: "flex", flexDirection: "column", gap: 6, fontSize: 12.5 }}>
            <span className="eyebrow">Timeframe</span>
            <select value={timeframe} onChange={(e) => setTimeframe(e.target.value)} style={selectStyle}>
              {["1D", "1h", "15m", "5m"].map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </label>
          <button className="btn btn--primary" onClick={handleRun} disabled={running}>
            {running ? "Running…" : "🔬 Run Research Cycle"}
          </button>
          {selected && !isLive && <span className="badge badge--paper">Research-only strategy</span>}
        </div>
      </div>

      {bt && (
        <>
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 20, marginBottom: 20 }}>
            <div className="card" style={{ padding: 20 }}>
              <div className="eyebrow" style={{ marginBottom: 12 }}>
                Hypothesis
              </div>
              <div style={{ fontWeight: 700, marginBottom: 8 }}>{strat?.name}</div>
              <p style={{ fontSize: 13 }}>{strat?.hypothesis}</p>
              <div style={{ marginTop: 12, display: "flex", gap: 8, alignItems: "center" }}>
                <span className="mono" style={{ fontSize: 22, fontWeight: 800 }}>
                  {strat?.edge_score}
                </span>
                <span className="eyebrow">Edge / 100 · {strat?.status}</span>
              </div>
            </div>
            <div className="card" style={{ padding: 20 }}>
              <div className="eyebrow" style={{ marginBottom: 12 }}>
                Out-of-Sample Backtest ({bt.symbol} · {bt.timeframe})
              </div>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
                <Metric label="OOS Sharpe" value={bt.oos.sharpe_ratio} />
                <Metric label="OOS Return" value={`${(bt.oos.total_return * 100).toFixed(2)}%`} />
                <Metric label="OOS Max DD" value={`${(bt.oos.max_drawdown * 100).toFixed(2)}%`} />
                <Metric label="Win Rate" value={`${(bt.oos.win_rate * 100).toFixed(1)}%`} />
                <Metric label="Profit Factor" value={bt.oos.profit_factor} />
                <Metric label="Trades" value={bt.oos.num_trades} />
              </div>
              <div style={{ marginTop: 12 }}>
                <span className={bt.oos_passed ? "badge badge--live" : "badge badge--danger"}>
                  OOS {bt.oos_passed ? "PASSED" : "FAILED"}
                </span>
              </div>
            </div>
            <div className="card" style={{ padding: 20 }}>
              <div className="eyebrow" style={{ marginBottom: 12 }}>
                Adversary Report
              </div>
              <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 10 }}>
                <VerdictBadge verdict={adv?.verdict} />
                <span className="mono" style={{ fontSize: 18, fontWeight: 700 }}>
                  {adv?.robustness_score}/100
                </span>
              </div>
              <p style={{ fontSize: 13 }}>{adv?.recommendation}</p>
            </div>
          </div>
        </>
      )}

      <div className="card" style={{ padding: 20 }}>
        <div className="eyebrow" style={{ marginBottom: 14 }}>
          Recent Backtests
        </div>
        {history.length === 0 ? (
          <p style={{ fontSize: 13 }}>No backtests recorded yet.</p>
        ) : (
          <div className="scroll-x">
            <table>
              <thead>
                <tr>
                  <th>Strategy</th>
                  <th>Symbol</th>
                  <th>OOS Sharpe</th>
                  <th>OOS Return</th>
                  <th>Result</th>
                </tr>
              </thead>
              <tbody>
                {history.map((h) => (
                  <tr key={h.backtest_id}>
                    <td className="mono">{h.strategy_id}</td>
                    <td className="mono">{h.symbol}</td>
                    <td className="mono">{h.result?.oos?.sharpe_ratio ?? "—"}</td>
                    <td className="mono">{h.result?.oos ? `${(h.result.oos.total_return * 100).toFixed(2)}%` : "—"}</td>
                    <td>{h.result?.oos_passed ? "PASSED" : "FAILED"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </AppShell>
  );
}

const selectStyle = {
  padding: "9px 12px",
  borderRadius: "var(--radius-sm)",
  border: "1px solid var(--hairline-strong)",
  background: "var(--surface-raised)",
  color: "var(--text-primary)",
  fontSize: 13,
};
