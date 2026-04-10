from typing import Callable
import streamlit as st

VIEW_REGISTRY: dict[str, tuple[str, str]] = {
    "overview":      ("views.overview",       "render_overview"),
    "council":       ("views.council",        "render_council"),
    "chat":          ("components.chat",      "render_chat"),
    "tasks":         ("views.tasks",          "render_tasks"),
    "deliverables":  ("views.deliverables",   "render_deliverables"),
    "roi":           ("views.roi",            "render_roi"),
    "swarm":         ("views.swarm",          "render_swarm"),
    "deploy":        ("views.deploy",         "render_deploy"),
    "tokens":        ("views.tokens",         "render_tokens"),
    "intelligence":  ("views.intelligence",   "render_intelligence"),
    "correction":    ("views.correction",     "render_correction"),
    "analyze":       ("views.analyze",        "render_analyze"),
    "code_analyzer": ("views.code_analyzer",  "render_code_analyzer"),
    "portfolio":     ("views.portfolio",      "render_portfolio"),
    "app_factory":   ("views.app_factory",    "render_app_factory"),
    "notebooklm":    ("views.notebooklm_view","render_notebooklm"),
    "user_manual":   ("views.user_manual",    "render_user_manual"),
    "issues":        ("views.issues",         "render_issues"),
}


def render_view(view_id: str, project, sb) -> None:
    entry = VIEW_REGISTRY.get(view_id)
    if not entry:
        st.error(f"Okänd vy: {view_id}")
        return
    module_path, func_name = entry
    try:
        import importlib
        module = importlib.import_module(module_path)
        func: Callable = getattr(module, func_name)
        if view_id == "portfolio":
            func(sb)
        else:
            func(project, sb)
    except ImportError as e:
        st.warning(f"Vyn '{view_id}' är inte implementerad än. ({e})")
    except Exception as e:
        st.error(f"Fel i vy '{view_id}': {e}")
        import traceback
        with st.expander("Detaljer"):
            st.code(traceback.format_exc())
