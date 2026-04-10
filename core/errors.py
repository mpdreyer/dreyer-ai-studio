import streamlit as st
import traceback
import functools
import logging

logging.basicConfig(
    filename="dreyer_studio.log",
    level=logging.ERROR,
    format="%(asctime)s — %(name)s — %(levelname)s — %(message)s",
)
logger = logging.getLogger("dreyer_studio")


def error_boundary(func):
    """Dekorator som fångar fel och visar dem snyggt."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            tb = traceback.format_exc()
            logger.error(f"{func.__name__}: {e}\n{tb}")
            st.error(f"**Något gick fel i {func.__name__}**")
            with st.expander("Visa detaljer"):
                st.code(tb)
            st.info("Försök igen eller kontakta Architetto via Rådslag för hjälp.")
            return None
    return wrapper


def safe_supabase_call(func):
    """Dekorator för Supabase-anrop med återförsök."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Supabase-fel i {func.__name__}: {e}")
            st.warning("Databasanslutning misslyckades. Försöker igen...")
            try:
                return func(*args, **kwargs)
            except Exception as e2:
                logger.error(f"Supabase retry failed: {e2}")
                return None
    return wrapper
