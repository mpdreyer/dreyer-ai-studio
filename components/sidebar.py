import streamlit as st
from agents.council import AGENTS, agent_list


VIEWS = {
    "overview":      ("📊", "Översikt"),
    "council":       ("🏛️", "Rådet"),
    "chat":          ("💬", "Rådslag"),
    "tasks":         ("✅", "Uppgifter"),
    "deliverables":  ("📦", "Leveranser"),
    "roi":           ("💰", "ROI-kalkylator"),
    "swarm":         ("🐝", "Testsvärm"),
    "deploy":        ("🔒", "Deployment"),
    "tokens":        ("🪙", "Token-ekonomi"),
    "intelligence":  ("🔭", "Intelligence"),
    "correction":    ("📐", "Correction Delta"),
}


def render_sidebar(project: dict | None) -> str:
    """Renderar sidebar. Returnerar aktiv vy."""

    with st.sidebar:
        # Projektinfo
        st.markdown("**Aktivt projekt**")
        if project:
            st.caption(f"{project.get('name', '—')} · {project.get('client', '—')}")
        else:
            st.caption("Inget projekt valt")

        if st.button("+ Nytt projekt", use_container_width=True):
            st.session_state["show_new_project"] = True

        st.divider()

        # Navigation
        if "active_view" not in st.session_state:
            st.session_state["active_view"] = "overview"

        st.markdown("**Navigation**")
        for view_id, (icon, label) in VIEWS.items():
            active = st.session_state["active_view"] == view_id
            badge = ""
            if view_id == "chat" and project:
                pass
            if st.button(
                f"{icon} {label}{badge}",
                key=f"nav_{view_id}",
                use_container_width=True,
                type="primary" if active else "secondary",
            ):
                st.session_state["active_view"] = view_id
                st.rerun()

        st.divider()

        # Aktiv agent
        st.markdown("**Tala med**")
        agents = agent_list()
        selected = st.selectbox(
            "Agent",
            agents,
            index=0,
            label_visibility="collapsed",
            key="selected_agent",
        )
        agent = AGENTS[selected]
        st.caption(f"{agent['role']}")
        status_dot = "🟢" if agent["status"] == "active" else "🟡" if agent["status"] == "busy" else "⚪"
        st.caption(f"{status_dot} {agent['status'].capitalize()}")

    return st.session_state.get("active_view", "overview")
