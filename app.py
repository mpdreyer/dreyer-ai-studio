"""
Dreyer AI Studio
Modulär Streamlit-app · Fas 1 · Claude only
"""

import pathlib
import streamlit as st

st.set_page_config(
    page_title="Dreyer AI Studio",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Ladda global CSS
css_file = pathlib.Path(__file__).parent / "assets" / "style.css"
if css_file.exists():
    st.markdown(f"<style>{css_file.read_text()}</style>", unsafe_allow_html=True)

from db.supabase_client import get_supabase, get_active_project
from db.portfolio_client import get_all_apps, get_active_projects_all
from components.topbar import render_topbar
from components.sidebar import render_sidebar
from components.new_project_modal import render_new_project_modal

# Init
sb = get_supabase()
project = get_active_project(sb)

# Nytt projekt-modal
if st.session_state.get("show_new_project"):
    render_new_project_modal(sb)
    st.stop()

# Om inget projekt valt → defaulta till portfolio
if project is None and "ss_active_view" not in st.session_state:
    st.session_state["ss_active_view"] = "portfolio"

# Topbar — räkna appar och projekt för no-project-läget
_app_count  = len(get_all_apps(sb))
_proj_count = len(get_active_projects_all(sb))
render_topbar(project, app_count=_app_count, active_project_count=_proj_count)

# Sidebar + aktiv vy
active_view = render_sidebar(project, sb=sb)

# Rendera aktiv vy via registry
from core.registry import render_view
render_view(active_view, project, sb)
