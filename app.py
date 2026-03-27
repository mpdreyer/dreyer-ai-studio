"""
Dreyer AI Studio
Modulär Streamlit-app · Fas 1 · Claude only
"""

import streamlit as st

st.set_page_config(
    page_title="Dreyer AI Studio",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Dölj Streamlit-brandning
st.markdown("""
<style>
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
.block-container {padding-top: 1rem; padding-bottom: 1rem;}
.stButton > button {border-radius: 8px;}
</style>
""", unsafe_allow_html=True)

from db.supabase_client import get_supabase, get_active_project
from components.topbar import render_topbar
from components.sidebar import render_sidebar

# Init
sb = get_supabase()
project = get_active_project(sb)

# Nytt projekt-modal
if st.session_state.get("show_new_project"):
    with st.form("new_project_form"):
        st.subheader("+ Nytt projekt")
        col1, col2 = st.columns(2)
        with col1:
            name   = st.text_input("Projektnamn", placeholder="AI POC")
            client = st.text_input("Kund", placeholder="Kund X")
        with col2:
            budget   = st.number_input("Token-budget (USD)", value=20.0, min_value=1.0, step=5.0)
            deadline = st.date_input("Deadline")
            deploy   = st.selectbox("Deployment", ["cloud", "hybrid", "airgap"])

        c1, c2 = st.columns(2)
        if c1.form_submit_button("Skapa projekt", type="primary"):
            sb.table("projects").insert({
                "name":            name,
                "client":          client,
                "token_budget":    budget,
                "deadline":        str(deadline),
                "deployment_mode": deploy,
                "status":          "active",
            }).execute()
            st.session_state.pop("show_new_project", None)
            st.session_state.pop("active_project_id", None)
            st.rerun()
        if c2.form_submit_button("Avbryt"):
            st.session_state.pop("show_new_project", None)
            st.rerun()
    st.stop()

# Topbar
render_topbar(project)

# Sidebar + aktiv vy
active_view = render_sidebar(project)

# Importera och rendera aktiv vy
if active_view == "overview":
    from views.overview import render_overview
    render_overview(project, sb)

elif active_view == "council":
    from views.council import render_council
    render_council(project, sb)

elif active_view == "chat":
    from components.chat import render_chat
    render_chat(project, sb)

elif active_view == "tasks":
    from views.tasks import render_tasks
    render_tasks(project, sb)

elif active_view == "deliverables":
    from views.deliverables import render_deliverables
    render_deliverables(project, sb)

elif active_view == "roi":
    from views.roi import render_roi
    render_roi(project, sb)

elif active_view == "swarm":
    from views.swarm import render_swarm
    render_swarm(project, sb)

elif active_view == "deploy":
    from views.deploy import render_deploy
    render_deploy(project, sb)

elif active_view == "tokens":
    from views.tokens import render_tokens
    render_tokens(project, sb)

elif active_view == "intelligence":
    from views.intelligence import render_intelligence
    render_intelligence(project, sb)

elif active_view == "correction":
    from views.correction import render_correction
    render_correction(project, sb)
