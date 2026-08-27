# `/model` — Strategy & AI Orchestration Layer

This package contains everything that decides *what* to trade. It never
talks to Alpaca directly — that's the backend's job.

```
model/
├── schemas/          Pydantic contracts shared across the pipeline
│   ├── market_data.py   Bar / Quote / MarketData / AssetInfo
│   ├── trade_signal.py  TradeSignal / NewsSignal / TradeIntent / RiskDecision / OrderRequest
│   └── agent_state.py   AutomationConfig / AutomationStatus / Decision
│
├── strategies/        Five strategy stubs + registry
│   ├── base.py           BaseStrategy interface
│   ├── funding_arbitrage.py
│   ├── cross_exchange_arbitrage.py
│   ├── market_making.py
│   ├── momentum.py
│   ├── mean_reversion.py
│   └── registry.py       STRATEGIES dict, used by backend /api/strategies
│
├── news/
│   └── news_strategy.py  Converts raw articles -> NewsSignal (stub)
│
└── orchestrator/
    └── llm_orchestrator.py  Fuses signal+news+portfolio -> TradeIntent (stub)
```

## Pipeline

```
MarketData ──▶ Strategy.analyze() ──▶ Strategy.generate_signal() ──▶ TradeSignal
                                                                          │
NewsArticles ──▶ NewsStrategy.generate_signal() ──▶ NewsSignal ──────────┤
                                                                          ▼
                                                              LLMOrchestrator
                                                                          │
                                                                          ▼
                                                                    TradeIntent
                                                                          │
                                                        (backend) RiskEngine
                                                                          │
                                                                          ▼
                                                              AlpacaService.submit_order()
```

## Implementing a strategy

Each strategy stub already has:

- a Pydantic `*Config` class describing its tunable parameters (these
  automatically become the fields shown in the Automation Configuration UI)
- `initialize(config)`, `analyze(...)`, `generate_signal(...)` stubbed out
  with `TODO(you)` comments
- docstrings describing expected inputs/outputs

To implement one: open the file, fill in `analyze()` and `generate_signal()`.
Do **not** change the method signatures or the `TradeSignal` schema — the
backend, risk engine, and frontend all depend on that contract staying
stable. As long as you return a valid `TradeSignal` (or `None`), the rest of
the pipeline works unmodified.

## Adding a new strategy

1. Create `model/strategies/your_strategy.py`, subclassing `BaseStrategy`
   (copy the shape of `momentum.py` as a template).
2. Register it in `model/strategies/registry.py`'s `STRATEGIES` dict and add
   an entry to `STRATEGY_METADATA`.
3. The frontend picks it up automatically via `GET /api/strategies` — no
   frontend changes required.

## Funding-rate & cross-exchange arbitrage caveat

Alpaca's API covers spot equities and spot crypto — it does not expose
perpetual futures or funding-rate data, and it is a single execution venue.
`FundingArbitrageStrategy` and `CrossExchangeArbitrageStrategy` are marked
`requires_external_venue: True` in the registry and their `is_available()`
methods reflect that honestly. Implementing them for real requires wiring
in an external data/execution venue — see the module docstrings in each
file for specifics.

## Groq AI Orchestration Service

The AI context fusion layer uses [Groq](https://groq.com) for ultra-low latency inference to synthesize strategy signals with news sentiment and portfolio exposure.

### Configuration
Set the following environment variables in `.env`:
```bash
GROQ_API_KEY=gsk_your_groq_api_key_here
GROQ_MODEL=llama-3.3-70b-versatile  # Or any Groq supported model
```

Supported Groq models:
- `llama-3.3-70b-versatile` (Default, recommended)
- `llama3-70b-8192`
- `llama3-8b-8192`
- `mixtral-8x7b-32768`
- `gemma2-9b-it`

If no `GROQ_API_KEY` is set, the system automatically falls back to deterministic quantitative pass-through signals so testing and automation never block.

## Safety boundary

The LLM orchestrator and every strategy only ever produce structured
Pydantic objects (`TradeSignal`, `TradeIntent`). None of this layer is
permitted to call Alpaca. Only `backend/app/services/alpaca_service.py`
talks to the broker, and only after `backend/app/services/risk_engine.py`
has approved a `TradeIntent`.
