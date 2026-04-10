"""
StateManager — centraliserad hantering av st.session_state.

Förhindrar typo-buggar och race conditions vid snabba UI-klick
genom att samla alla state-nycklar på ett ställe.

Användning:
    from core.state_manager import state

    state.set_active_project("proj-123")
    pid = state.active_project_id()
    state.clear_swarm()
"""

from __future__ import annotations

from typing import Optional, TYPE_CHECKING

import streamlit as st

if TYPE_CHECKING:
    from agents.swarm_controller import SwarmConfig

# ── Nyckelkonstanter (ändra här, ändras överallt) ──────────────────────────────

_KEY_ACTIVE_PROJECT   = "active_project_id"
_KEY_ACTIVE_SWARM     = "active_swarm_config"
_KEY_SIDEBAR_OPEN     = "sidebar_open"
_KEY_CURRENT_VIEW     = "current_view"


class _StateManager:
    """
    Tunn wrapper runt st.session_state med explicita accessorer.
    Singleton — använd den exporterade `state`-instansen.
    """

    # ── Projekt ────────────────────────────────────────────────────────────────

    def active_project_id(self) -> Optional[str]:
        return st.session_state.get(_KEY_ACTIVE_PROJECT)

    def set_active_project(self, project_id: str) -> None:
        st.session_state[_KEY_ACTIVE_PROJECT] = project_id

    def clear_active_project(self) -> None:
        st.session_state.pop(_KEY_ACTIVE_PROJECT, None)

    # ── Svärm ──────────────────────────────────────────────────────────────────

    def active_swarm_config(self) -> Optional["SwarmConfig"]:
        return st.session_state.get(_KEY_ACTIVE_SWARM)

    def set_active_swarm(self, config: "SwarmConfig") -> None:
        st.session_state[_KEY_ACTIVE_SWARM] = config

    def clear_swarm(self) -> None:
        st.session_state.pop(_KEY_ACTIVE_SWARM, None)

    # ── Navigation ─────────────────────────────────────────────────────────────

    def current_view(self) -> Optional[str]:
        return st.session_state.get(_KEY_CURRENT_VIEW)

    def set_current_view(self, view: str) -> None:
        st.session_state[_KEY_CURRENT_VIEW] = view

    # ── Generellt ──────────────────────────────────────────────────────────────

    def get(self, key: str, default=None):
        return st.session_state.get(key, default)

    def set(self, key: str, value) -> None:
        st.session_state[key] = value

    def clear_all(self) -> None:
        """Nollställ all session-state (t.ex. vid utloggning)."""
        st.session_state.clear()


# Exporterad singleton
state = _StateManager()
