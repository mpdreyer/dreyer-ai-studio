import streamlit as st
from agents.council import AGENTS, agent_list
from db.portfolio_client import get_active_projects_all
from core.state import get_active_view, set_active_view


VIEWS = {
    "portfolio":    ("🏢", "DTSM Portfolio"),
    "overview":     ("📊", "Översikt"),
    "analyze":        ("🔍", "Analysera"),
    "code_analyzer":  ("🔬", "Kodanalys"),
    "council":        ("🏛️", "Rådet"),
    "chat":         ("💬", "Rådslag"),
    "tasks":        ("✅", "Uppgifter"),
    "deliverables": ("📦", "Leveranser"),
    "roi":          ("💰", "ROI-kalkylator"),
    "swarm":        ("🐝", "Testsvärm"),
    "deploy":       ("🔒", "Deployment"),
    "tokens":       ("🪙", "Token-ekonomi"),
    "intelligence": ("🔭", "Intelligence"),
    "correction":   ("📐", "Correction Delta"),
    "app_factory":  ("⚡", "App Factory"),
    "notebooklm":   ("📚", "NotebookLM"),
    "user_manual":  ("📖", "Användarmanual"),
    "issues":       ("🐛", "Buggar & Förbättringar"),
}

_STATUS_DOT = {
    "active": '<span class="status-dot active"></span>',
    "busy":   '<span class="status-dot busy"></span>',
    "idle":   '<span class="status-dot idle"></span>',
}


def render_sidebar(project: dict | None, sb=None) -> str:
    with st.sidebar:
        # DTSM logotyp
        st.markdown(
            '<div style="font-family:\'JetBrains Mono\',monospace;font-size:16px;'
            'font-weight:700;color:#6366f1;letter-spacing:2px;margin-bottom:2px;">DTSM</div>'
            '<div style="font-size:10px;color:#5a5a72;margin-bottom:12px;">'
            'Dreyer Technology & Strategy Management</div>',
            unsafe_allow_html=True,
        )

        # Projektväxlare
        if sb is not None:
            all_projects = get_active_projects_all(sb)
        else:
            all_projects = []

        if all_projects:
            project_names = ["— Välj projekt —"] + [p["name"] for p in all_projects]
            project_ids   = [None] + [p["id"] for p in all_projects]
            current_id    = st.session_state.get("ss_active_project_id")
            try:
                current_idx = project_ids.index(current_id)
            except ValueError:
                current_idx = 0  # "— Välj projekt —"

            chosen_idx = st.selectbox(
                "Aktivt projekt",
                range(len(project_names)),
                format_func=lambda i: project_names[i],
                index=current_idx,
                key="project_switcher",
                label_visibility="collapsed",
            )
            chosen_id = project_ids[chosen_idx]
            if chosen_id and chosen_id != st.session_state.get("ss_active_project_id"):
                st.session_state["ss_active_project_id"] = chosen_id
                st.rerun()

            if chosen_id:
                proj   = all_projects[chosen_idx - 1]  # -1 för "— Välj —"-offset
                cur    = proj.get("current_phase", 1)
                phases = ["Brief","Data","Prompts","Bygg","Diavolo","Demo","Nästa steg"]
                pname  = phases[cur - 1] if 0 < cur <= len(phases) else "—"
                st.markdown(
                    f'<div style="font-size:10px;color:#9090a8;margin-top:2px;">'
                    f'{proj.get("client","—")} · Fas {cur}/7 · {pname}</div>',
                    unsafe_allow_html=True,
                )
        else:
            st.markdown(
                '<div style="font-size:11px;color:#9090a8;margin-bottom:4px;">Inga aktiva projekt</div>',
                unsafe_allow_html=True,
            )

        if st.button("＋ Nytt projekt", use_container_width=True, type="primary"):
            st.session_state["show_new_project"] = True
            st.rerun()

        st.divider()

        # Navigation
        if "ss_active_view" not in st.session_state:
            set_active_view("overview")

        st.markdown(
            '<div style="font-size:10px;font-family:monospace;color:#5a5a72;'
            'letter-spacing:1px;margin-bottom:6px;">NAVIGATION</div>',
            unsafe_allow_html=True,
        )
        for view_id, (icon, label) in VIEWS.items():
            active = get_active_view() == view_id
            if st.button(
                f"{icon}  {label}",
                key=f"nav_{view_id}",
                use_container_width=True,
                type="primary" if active else "secondary",
            ):
                set_active_view(view_id)
                st.rerun()

        st.divider()

        # Agent-selector
        st.markdown(
            '<div style="font-size:10px;font-family:monospace;color:#5a5a72;'
            'letter-spacing:1px;margin-bottom:6px;">TALA MED</div>',
            unsafe_allow_html=True,
        )
        agents = agent_list()
        selected = st.selectbox(
            "Agent",
            agents,
            index=0,
            label_visibility="collapsed",
            key="selected_agent",
        )
        st.session_state["active_agent"] = selected

        agent  = AGENTS[selected]
        dot    = _STATUS_DOT.get(agent.get("status", "idle"), _STATUS_DOT["idle"])
        model  = agent.get("model", "—")
        role   = agent.get("role", "—")
        initials = agent.get("initials", selected[:2].upper())
        bg     = agent.get("color_bg", "#1e2130")
        fg     = agent.get("color_text", "#AFA9EC")

        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:10px;margin-top:6px;
                    background:#1e2130;border:1px solid rgba(127,119,221,0.2);
                    border-radius:8px;padding:10px 12px;">
          <div style="width:32px;height:32px;border-radius:50%;background:{bg};
                      color:{fg};display:flex;align-items:center;justify-content:center;
                      font-family:monospace;font-weight:700;font-size:12px;flex-shrink:0;">
            {initials}
          </div>
          <div>
            <div style="font-size:12px;font-weight:600;color:#e8e8f0;">{selected}</div>
            <div style="font-size:10px;color:#9090a8;">{role}</div>
            <div style="font-size:10px;margin-top:2px;">{dot}
              <span style="color:#9090a8;font-family:monospace;">{model}</span>
            </div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        from components.agent_chat import render_agent_chat
        render_agent_chat()

    return get_active_view()
