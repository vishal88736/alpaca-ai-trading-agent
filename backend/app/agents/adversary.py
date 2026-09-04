"""
Adversary Agent (deterministic).

Stress-tests a backtest result by checking:
  1. Out-of-sample stability  (OOS Sharpe/return vs train)
  2. Sample size              (too few trades → fragile)
  3. Trade concentration      (few outliers driving returns)
  4. Drawdown severity

Outputs a ROBUSTNESS SCORE (0-100) and a verdict (PASS / WATCH / REJECT).
No LLM, no random numbers.
"""

from __future__ import annotations

import uuid
from typing import Any


class AdversaryAgent:
    def stress_test_strategy(self, strategy: dict[str, Any], backtest: dict[str, Any]) -> dict[str, Any]:
        train = backtest.get("train", {})
        oos = backtest.get("oos", {})

        train_sharpe = float(train.get("sharpe_ratio", 0.0))
        oos_sharpe = float(oos.get("sharpe_ratio", 0.0))
        train_return = float(train.get("total_return", 0.0))
        oos_return = float(oos.get("total_return", 0.0))
        oos_dd = float(oos.get("max_drawdown", 0.0))
        num_trades = int(oos.get("num_trades", 0) or 0) + int(train.get("num_trades", 0) or 0)
        win_rate = float(oos.get("win_rate", 0.0))

        trade_pnls = list(backtest.get("train", {}).get("trade_pnls", [])) + list(backtest.get("oos", {}).get("trade_pnls", []))

        weaknesses: list[str] = []
        evidence: list[str] = []
        failure_scenarios: list[str] = []

        # 1. OOS stability
        sharpe_degradation = (train_sharpe - oos_sharpe) / max(abs(train_sharpe), 1e-6)
        if train_sharpe > 0 and oos_sharpe < 0:
            weaknesses.append("Strategy loses money out-of-sample (OOS Sharpe negative).")
            failure_scenarios.append("Live performance collapses relative to training period.")
            evidence.append(f"OOS Sharpe {oos_sharpe:.2f} vs train {train_sharpe:.2f}")
        elif sharpe_degradation > 1.0:
            weaknesses.append(f"Large OOS degradation (Sharpe dropped {sharpe_degradation:.0%} from train).")
            evidence.append(f"Train Sharpe {train_sharpe:.2f} -> OOS {oos_sharpe:.2f}")
        else:
            evidence.append(f"OOS Sharpe {oos_sharpe:.2f} (train {train_sharpe:.2f}: stable degradation).")

        oos_return_negative = oos_return <= 0
        if oos_return_negative:
            weaknesses.append("Out-of-sample total return is non-positive.")
            evidence.append(f"OOS return {oos_return:+.2%}")

        # 2. Sample size
        if num_trades < 20:
            weaknesses.append(f"Small trade sample ({num_trades} trades) — statistically fragile.")
            failure_scenarios.append("Few dependent trades; edge not statistically significant.")
            evidence.append(f"Total trades: {num_trades}")
        else:
            evidence.append(f"Total trades: {num_trades}")

        # 3. Trade concentration (top trade share of gross profit)
        concentration = _concentration(trade_pnls)
        if concentration > 0.60:
            weaknesses.append(f"Return concentration {concentration:.0%} — too few trades drive performance.")
            failure_scenarios.append("A single outlier trade dominates results.")
            evidence.append(f"Concentration index: {concentration:.2f}")
        else:
            evidence.append(f"Concentration index: {concentration:.2f}")

        # 4. Drawdown severity
        if oos_dd > 0.25:
            weaknesses.append(f"Severe OOS drawdown ({oos_dd:.1%}).")
            failure_scenarios.append("Deep drawdowns breach risk tolerance in live trading.")
            evidence.append(f"OOS max drawdown {oos_dd:.1%}")
        else:
            evidence.append(f"OOS max drawdown {oos_dd:.1%}")

        score = _robustness_score(oos_sharpe, oos_return, concentration, win_rate, oos_dd, num_trades)

        if score >= 70.0:
            verdict = "PASS"
            recommendation = "Structurally robust; eligible for capital allocation (still subject to the deterministic risk engine)."
        elif score >= 45.0:
            verdict = "WATCH"
            recommendation = "Modest edge; permit a small paper allocation and monitor rolling performance."
        else:
            verdict = "REJECT"
            recommendation = "Reject — edge is not robust enough to warrant capital."

        report_id = f"ADV-{uuid.uuid4().hex[:8]}"
        return {
            "report_id": report_id,
            "strategy_id": strategy.get("strategy_id", "UNKNOWN"),
            "robustness_score": round(score, 1),
            "verdict": verdict,
            "weaknesses": weaknesses,
            "evidence": evidence,
            "failure_scenarios": failure_scenarios,
            "recommendation": recommendation,
        }


def _concentration(pnls: list[float]) -> float:
    if not pnls:
        return 0.0
    gross_profit = sum(p for p in pnls if p > 0)
    if gross_profit <= 0:
        return 0.0
    top = sorted((p for p in pnls if p > 0), reverse=True)[: max(1, len(pnls) // 5)]
    return sum(top) / gross_profit


def _robustness_score(oos_sharpe: float, oos_return: float, concentration: float, win_rate: float, oos_dd: float, num_trades: int) -> float:
    sharpe_score = min(1.0, max(0.0, oos_sharpe / 2.0))
    return_score = min(1.0, max(0.0, oos_return / 0.30))
    concentration_penalty = concentration if concentration > 0.5 else 0.0
    drawdown_penalty = min(1.0, oos_dd / 0.30)
    sample_penalty = 0.4 if num_trades < 20 else 0.0

    score = 100.0 * (
        0.40 * sharpe_score
        + 0.25 * return_score
        + 0.15 * win_rate
        - 0.12 * concentration_penalty
        - 0.10 * drawdown_penalty
        - 0.08 * sample_penalty
    )
    return max(0.0, min(100.0, score))


adversary_agent = AdversaryAgent()