# Architecture Comparison — Alpaca AI Trading Agent vs. Reference (Alpha Hunter)

> Generated during the reference-driven upgrade. Documents what each system actually
> does (verified from source, not READMEs) and what was kept, imported, reworked, or
> rejected.

---

## A. Current architecture (my project)

My project is a **session-scoped, paper-trading scaffold** with a clean three-layer split:

```
website/    React + Vite terminal (never talks to Alpaca)
model/      Strategy library + schemas + LLM orchestrator + news (never talks to Alpaca)
backend/    FastAPI + Alpaca service + deterministic risk engine + automation engine
```

Design invariants already present (all preserved in the upgrade):

1. **Session-scoped server-side credentials.** The Connect screen POSTs `api_key`/`secret_key`
   once; the backend validates them against Alpaca and holds them only in an in-memory
   `session_store` keyed by an httpOnly `session_id` cookie. Never echoed, logged, or written to disk.
2. **The LLM can never reach Alpaca.** `model/` only produces Pydantic objects
   (`TradeSignal` → `TradeIntent`). The deterministic `RiskEngine` is the sole gate; only
   `backend/app/services/alpaca_service.py` calls the broker.
3. **Deterministic risk engine** — fully implemented (kill switch, asset allowlist, duplicate
   order, max order size, max position %, max exposure %, buying power, daily loss, trades/day).
4. **Six strategies** with real signal logic (momentum computes Supertrend/ROC; mean reversion
   computes z-scores; market making computes inventory skew; options alpha computes historical
   vol). Funding/cross-exchange arbitrage honestly marked `requires_external_venue`.
5. **Real news service** (cryptocurrency.cv + CoinTelegraph RSS) feeding a real word-frequency
   sentiment `NewsStrategy`.
6. **Groq LLM orchestrator** with deterministic pass-through fallback when no key is set.

### Verified weaknesses in my project (found during inspection)

| # | Issue | Evidence |
|---|-------|----------|
| 1 | `alpaca_service.py` references undefined names (`AlpacaAssetClass`, `datetime`, `timezone`, `AssetClass`, `Timeframe`) — `get_assets(asset_class=...)` and the crypto fallback crash. | lines 133/135, 200, 212 |
| 2 | No `run.py`; README's `cd backend && uvicorn app.main:app` fails (`model` not importable). | verified locally |
| 3 | Automation loop generates signals but execution status is only in-memory `Decision.execution_result` strings; nothing persisted, order status never re-synced from Alpaca. | `automation_engine.py` |
| 4 | No backtesting, market-regime, discovery, adversarial testing, portfolio allocation, performance monitoring, or explainability. | absent |
| 5 | `market_making`, `funding_arbitrage`, `cross_exchange_arbitrage` either read an unavailable `latest_quote` or fabricate basis/spread (e.g. hardcoded `estimated_basis = 0.0008`). | strategy files |
| 6 | `test-trade` endpoint submits a hardcoded micro order with a hardcoded "FILLED" label. | `execute_test_trade` |

---

## B. Reference architecture (Alpha Hunter)

A **demo/mock multi-agent research system** (not truly autonomous or production-safe):

```
market_intel → discovery → backtest → adversary → evolution (edge score)
    → portfolio_mgr → risk_agent → alpaca.trading → performance_monitor → explainability
```

Strong ideas worth importing:

1. Six-agent research pipeline with clear responsibility separation.
2. Backtest with chronological train/OOS walk-forward split (70/30) and metrics
   (Sharpe, Sortino, win rate, profit factor, max drawdown).
3. Adversary agent producing robustness score + PASS/WATCH/REJECT.
4. Edge score / strategy Darwinism + lifecycle states (ALIVE/WATCH/KILLED/REJECTED).
5. Portfolio manager with mandatory cash buffer and edge-based allocation.
6. Performance monitor that degrades allocation or kills underperformers.
7. Explainability ("why this trade / why killed").
8. SQLite + SQLAlchemy persistence (regimes, strategies, backtests, adversary reports,
   orders, trades, agent events, audit logs).
9. Alpaca source-of-truth reconciliation (incl. stop/take-profit protection map).

Serious problems NOT imported (deliberately):

| # | Problem | Why rejected |
|---|---------|--------------|
| 1 | `trading.submit_order` silently fabricates a `"filled"` order with a fake id when Alpaca is unavailable/errors. | Violates "no fake order responses". |
| 2 | `backtest._simulate_period` uses `np.random.normal` returns — backtests are **fake**. | Violates "no fabricated performance". |
| 3 | `market_data` synth fallback invents random prices/volumes for any symbol. | Fabricated market data. |
| 4 | Hardcoded demo strategies/trades/P&L ("Regime Momentum v3" edge 91, NVDA 250 @ $122.40…). | Fake seed data. |
| 5 | Autonomous loop auto-executes on a **random** symbol whenever seeded edge ≥ 80. | Unsafe + fake edge signal. |
| 6 | Risk `daily_loss_pct <= -MAX` comparison is effectively a no-op for the values passed. | Bug. |
| 7 | `backtest.py` uses `np` without importing it. | Bug. |
| 8 | Global singletons; no per-user session isolation. | Unsafe for multi-user. |

---

## C. Feature-by-feature comparison

```
Feature                  My Project                  Reference                   Best Implementation
----------------------------------------------------------------------------------------------------------------
Market Intelligence      absent                      regime (real data+failback)   Import: deterministic regime agent on real bars
Strategy Registry        registry+metadata           hardcoded list               Keep mine (+ execution_mode)
Strategy Discovery       absent                      hypothesis templates         Import: deterministic templates (no fake "profit")
Backtesting              absent                      real split, fake returns     Import structure, implement REAL vectorized engine
Adversarial Testing      absent                      stress tests (some fake)     Import: deterministic stress tests
Portfolio Management     absent                      edge-based allocation        Import: edge-based w/ cash buffer
Risk Management          full deterministic          deterministic (buggy)        Keep mine, EXTEND (symbol/qty/hours/drawdown/open-pos)
Execution                real submit (no mock)       real + fake fallback         Keep mine (no mock), ADD order-sync + persistence
Performance Monitoring   absent                      edge deterioration           Import: stateless, live-P&L-driven
Agent State              AutomationStatus            in-memory events             Keep mine + persistent audit/events
Orchestrator             Groq + fallback             event router                 Keep mine (safety boundary)
Frontend                 React terminal              React/TS dashboard           Keep mine, distinct visuals; add panels
Testing                  none in my project          pytest (risk/lifecycle)      Import tests + write mine
```

---

## D. Strategy comparison

```
Strategy                     My Version                        Reference                     Best Version
---------------------------------------------------------------------------------------------------------------------
Momentum                     Real Supertrend+ROC logic         ~ only as "Regime Momentum" template   Keep MINE (executable)
Mean Reversion               Real z-score logic                ~ RSI-MACD template                     Keep MINE (executable)
Market Making                inventory skew (no live quotes)   absent                                 Keep mine, mark research
Cross-Exchange Arbitrage     spread calc (broken)              absent                                 Fix mine, mark backtest-only (external venue)
Funding Arbitrage            fabricated basis (0.0008)         absent                                 Rewrite honestly, mark research/external
Options Alpha Income         real HV/delta est (equity wheel)  absent                                 Keep mine, clarify equity approximation
News Strategy                real word-sentiment               absent                                 Keep MINE (real data)
```

---

## E. Recommended architecture

Keep the three-layer split and safety invariants. Add, under `backend/`:

1. A `db/` package (SQLAlchemy + SQLite) for orders, positions snapshot, decisions, trades,
   strategies, backtests, adversary reports, agent events, audit.
2. A stateless `agents/` package (market intelligence/regime, discovery, backtest, adversary,
   evolution/edge-score, portfolio manager, performance monitor, explainability). Stateless by
   design so they remain per-session safe.
3. Extend `services/` with: fixed `alpaca_service` (+ order status sync, clock/market hours),
   extended `risk_engine`, a repository bridging the automation engine to SQLite, and a broker
   interface so tests can inject a clearly-labelled test double.
4. `run.py` at repo root that fixes `sys.path` so `model` and `backend/app` are importable
   regardless of working directory.

Flow becomes:

```
Market data (Alpaca / real fallback) → Market Intelligence (regime)
  → Strategy (analyze → structured TradeSignal) → News (real sentiment)
  → LLM Orchestrator (TradeIntent, LLM can only propose)
  → Deterministic RiskEngine (hard gates) → Position sizing (portfolio manager)
  → Order manager → Alpaca.submit_order → real order id/status persisted
  → sync positions/orders from Alpaca → performance monitor updates edge/alloc
  → audit + agent events persisted → UI reads real state
```

---

## F. Features imported from the reference

1. Market-intelligence/regime analysis (deterministic, real bars).
2. Strategy discovery templates (deterministic; no fabricated "profit" claims).
3. Real chronological train/OOS backtest engine (vectorized, with costs/slippage).
4. Adversarial stress test (parameter perturbation, concentration, OOS collapse).
5. Edge score + lifecycle (ALIVE/WATCH/KILLED/REJECTED).
6. Portfolio capital allocation with mandatory cash buffer.
7. Performance monitor (edge deterioration → reduce/kill).
8. Explainability ("why this trade / why killed").
9. SQLite persistence + audit trail + agent-event feed.
10. Protection-map reconciliation of open stop/take-profit orders.

## G. Features preserved from my project

1. Session-scoped, server-side Alpaca connection flow (Connect screen + httpOnly cookie).
2. Deterministic RiskEngine (extended, never replaced).
3. Broker-agnostic strategy base + registry + `TradeSignal`/`TradeIntent`/`RiskDecision`/`OrderRequest` schemas.
4. All six strategies (upgraded/classified, none removed).
5. Real news service + real sentiment strategy.
6. Groq orchestrator with deterministic fallback.
7. No mock/fake fallback in the live execution path — an order is only reported executed when
   Alpaca returns a real order id/status.
8. React trading-terminal UI (visually distinct from the reference).