"""
TokenBudgetManager — spårar token-förbrukning per session med auto-stopp.

Användning i Streamlit:
    from utils.token_budget import TokenBudgetManager

    budget = TokenBudgetManager(limit_usd=1.0)
    budget.add(tokens_in=500, tokens_out=200, model="claude-haiku-4-5-20251001")

    if budget.should_stop():
        st.warning(budget.warning_message())
"""

from __future__ import annotations

import streamlit as st

# Ungefärliga kostnader USD per 1M tokens (input / output)
_MODEL_PRICES: dict[str, tuple[float, float]] = {
    "claude-haiku-4-5-20251001":  (0.80,  4.00),
    "claude-sonnet-4-6":          (3.00, 15.00),
    "claude-opus-4-6":           (15.00, 75.00),
}
_DEFAULT_PRICE = (3.00, 15.00)

_STATE_KEY = "token_budget"


def _state() -> dict:
    if _STATE_KEY not in st.session_state:
        st.session_state[_STATE_KEY] = {"tokens_in": 0, "tokens_out": 0, "cost_usd": 0.0}
    return st.session_state[_STATE_KEY]


class TokenBudgetManager:
    """
    Enkel sessionsbaserad budgetstyrning.

    Args:
        limit_usd:    Maxkostnad i USD innan varning/stopp.
        warn_at:      Andel av limit vid vilken varning visas (default 0.8 = 80%).
    """

    def __init__(self, limit_usd: float = 1.0, warn_at: float = 0.8):
        self._limit = limit_usd
        self._warn_at = warn_at

    # ── Datainmatning ──────────────────────────────────────────────────────────

    def add(self, tokens_in: int, tokens_out: int, model: str = "claude-sonnet-4-6") -> None:
        """Lägg till tokens och uppdatera kostnad."""
        price_in, price_out = _MODEL_PRICES.get(model, _DEFAULT_PRICE)
        cost = (tokens_in * price_in + tokens_out * price_out) / 1_000_000
        s = _state()
        s["tokens_in"]  += tokens_in
        s["tokens_out"] += tokens_out
        s["cost_usd"]   += cost

    # ── Status ─────────────────────────────────────────────────────────────────

    @property
    def cost_usd(self) -> float:
        return _state()["cost_usd"]

    @property
    def tokens_total(self) -> int:
        s = _state()
        return s["tokens_in"] + s["tokens_out"]

    def utilization(self) -> float:
        """Andel av budgeten som förbrukats (0.0–1.0+)."""
        return self.cost_usd / self._limit if self._limit > 0 else 0.0

    def should_warn(self) -> bool:
        return self.utilization() >= self._warn_at

    def should_stop(self) -> bool:
        return self.utilization() >= 1.0

    def warning_message(self) -> str:
        pct = self.utilization() * 100
        return (
            f"⚠️ Budgetvarning: {pct:.0f}% av ${self._limit:.2f} förbrukat "
            f"(${self.cost_usd:.4f} / {self.tokens_total:,} tokens)"
        )

    def stop_message(self) -> str:
        return (
            f"🛑 Budgetgräns nådd: ${self.cost_usd:.4f} ≥ ${self._limit:.2f}. "
            "Ny körning blockerad."
        )

    # ── Streamlit-widget ───────────────────────────────────────────────────────

    def render_status(self) -> None:
        """Visar en kompakt budgetstatus-rad i Streamlit."""
        util = self.utilization()
        color = "🔴" if util >= 1.0 else "🟡" if util >= self._warn_at else "🟢"
        st.caption(
            f"{color} Budget: ${self.cost_usd:.4f} / ${self._limit:.2f} "
            f"({util * 100:.0f}%) · {self.tokens_total:,} tokens"
        )
        if self.should_warn():
            st.warning(self.warning_message() if not self.should_stop() else self.stop_message())

    def reset(self) -> None:
        """Nollställ sessionsräknarna (t.ex. vid nytt projekt)."""
        st.session_state[_STATE_KEY] = {"tokens_in": 0, "tokens_out": 0, "cost_usd": 0.0}
