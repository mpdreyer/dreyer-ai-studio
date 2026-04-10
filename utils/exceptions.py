"""
Centraliserad felhantering för Dreyer AI Studio.

Användning:
    from utils.exceptions import handle_error, AppError

    @handle_error("Kunde inte hämta projekt")
    def my_view_function():
        ...

    raise AppError("Något gick fel", recoverable=True)
"""

from __future__ import annotations

import functools
import logging
import traceback
from typing import Callable, Optional

import streamlit as st

logger = logging.getLogger("dreyer_studio")


class AppError(Exception):
    """Basundantag för applikationsfel med UI-meddelande."""
    def __init__(self, message: str, recoverable: bool = True, detail: str = ""):
        super().__init__(message)
        self.recoverable = recoverable
        self.detail = detail


class ConfigError(AppError):
    """Konfigurationsfel (saknade env-vars, ogiltig setup)."""
    pass


class DatabaseError(AppError):
    """Databasrelaterade fel."""
    pass


class APIError(AppError):
    """Externa API-anrop misslyckades."""
    pass


def handle_error(
    user_message: str = "Ett oväntat fel inträffade",
    show_detail: bool = False,
    fallback=None,
) -> Callable:
    """
    Dekorator som fångar undantag och visar ett snyggt st.error().

    Args:
        user_message: Meddelande som visas för användaren.
        show_detail:  Visa teknisk detalj (bra under utveckling).
        fallback:     Värde att returnera vid fel (None = inget returnvärde).

    Exempel:
        @handle_error("Kunde inte ladda körningar")
        def render_history(controller):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except AppError as e:
                msg = f"{user_message}: {e}" if str(e) else user_message
                if e.recoverable:
                    st.error(msg)
                else:
                    st.error(f"🔴 Kritiskt fel — {msg}")
                if show_detail and e.detail:
                    st.caption(e.detail)
                logger.error("AppError i %s: %s", func.__name__, e, exc_info=True)
                return fallback
            except Exception as e:
                detail = traceback.format_exc() if show_detail else ""
                st.error(f"{user_message}.")
                if show_detail:
                    st.code(detail, language="text")
                logger.error("Oväntat fel i %s: %s", func.__name__, e, exc_info=True)
                return fallback
        return wrapper
    return decorator
