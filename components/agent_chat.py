"""
Global Agent Chat Panel — Dreyer AI Studio
Kollapsbar sidebar-komponent tillgänglig från alla vyer.
"""

import streamlit as st
from datetime import datetime

from agents.council import AGENTS
from agents.router import route_message
from db.supabase_client import get_supabase, save_message, log_tokens

PHASES = ["Brief", "Data", "Prompts", "Bygg", "Diavolo", "Demo", "Nästa steg"]


def _build_rich_context(project_id: str, project: dict, sb) -> str:
    """Bygger en detaljerad systemkontext med deliverables, issues och chatthistorik."""
    cur   = project.get("current_phase", 1)
    pname = PHASES[cur - 1] if 0 < cur <= len(PHASES) else "—"

    # Deliverables
    try:
        deliv_rows = (
            sb.table("deliverables")
            .select("title,status")
            .eq("project_id", project_id)
            .limit(5)
            .execute()
            .data or []
        )
        deliv_str = ", ".join(
            f"{d['title']} ({d['status']})" for d in deliv_rows
        ) or "—"
    except Exception:
        deliv_str = "—"

    # Öppna issues
    try:
        issue_rows = (
            sb.table("issues")
            .select("title,priority")
            .eq("project_id", project_id)
            .eq("status", "open")
            .limit(5)
            .execute()
            .data or []
        )
        issues_str = ", ".join(
            f"{i['title']} [{i['priority']}]" for i in issue_rows
        ) or "—"
    except Exception:
        issues_str = "—"

    # Senaste 10 chattmeddelanden
    try:
        recent = (
            sb.table("chat_messages")
            .select("role,content,agent")
            .eq("project_id", project_id)
            .order("created_at", desc=True)
            .limit(10)
            .execute()
            .data or []
        )
        recent = list(reversed(recent))
        chat_str = "\n".join(
            f"{m['role'].upper()} ({m.get('agent') or '?'}): {m['content'][:120]}"
            for m in recent
        ) or "—"
    except Exception:
        chat_str = "—"

    return (
        f"AKTIVT PROJEKT: {project.get('name', '—')}\n"
        f"KUND: {project.get('client', '—')}\n"
        f"BESKRIVNING: {project.get('description', '—')}\n"
        f"AKTUELL FAS: {cur}/7 — {pname}\n"
        f"HEALTH: {project.get('health_score', 0)}/100\n"
        f"TOKEN-BUDGET: {project.get('token_used', 0):.2f}/{project.get('token_budget', 20):.0f} USD\n"
        f"DEPLOYMENT: {project.get('deployment_mode', 'cloud')}\n\n"
        f"DELIVERABLES: {deliv_str}\n"
        f"ÖPPNA ISSUES: {issues_str}\n\n"
        f"SENASTE KONVERSATION:\n{chat_str}"
    )


def render_agent_chat():
    """Global agent chat — anropas från sidebar.py inuti with st.sidebar."""
    st.markdown("---")
    st.markdown(
        '<div style="font-size:10px;font-family:monospace;color:#5a5a72;'
        'letter-spacing:1px;margin-bottom:6px;">AGENT CHAT</div>',
        unsafe_allow_html=True,
    )

    agent_names = list(AGENTS.keys())
    selected = st.selectbox(
        "Agent",
        agent_names,
        format_func=lambda x: f"{AGENTS[x]['initials']}  {x} — {AGENTS[x]['role']}",
        key="sidebar_chat_agent",
        label_visibility="collapsed",
    )

    agent = AGENTS[selected]
    st.caption(f"`{agent['model_display']}` · {agent['model']}")

    history_key = f"agent_chat_{selected}"

    with st.expander(
        "💬 Öppna chat",
        expanded=st.session_state.get("ss_chat_open", False),
    ):
        history: list[dict] = st.session_state.get(history_key, [])

        # Visa senaste 6 meddelanden
        if history:
            for msg in history[-6:]:
                if msg["role"] == "user":
                    st.markdown(
                        f'<div style="font-size:12px;color:#9090a8;'
                        f'margin-bottom:4px;">👤 {msg["content"]}</div>',
                        unsafe_allow_html=True,
                    )
                else:
                    st.markdown(
                        f'<div style="font-size:12px;color:#e8e8f0;'
                        f'background:rgba(99,102,241,0.08);border-radius:6px;'
                        f'padding:6px 8px;margin-bottom:4px;">'
                        f'{agent["initials"]} {msg["content"]}</div>',
                        unsafe_allow_html=True,
                    )
        else:
            st.caption("Ingen historik ännu.")

        user_input = st.text_input(
            "Din fråga...",
            key=f"chat_input_{selected}",
            label_visibility="collapsed",
            placeholder="Skriv din fråga...",
        )

        col1, col2 = st.columns([3, 1])
        with col1:
            send = st.button("Skicka", key=f"send_{selected}",
                             use_container_width=True, type="primary")
        with col2:
            clear = st.button("🗑️", key=f"clear_{selected}",
                              use_container_width=True)

        if clear:
            st.session_state[history_key] = []
            st.rerun()

        if send and user_input:
            project_id = st.session_state.get("ss_active_project_id")
            if not project_id:
                st.warning("Välj ett projekt först.")
            else:
                sb = get_supabase()

                # Hämta projekt för kontext
                try:
                    proj_res = (
                        sb.table("projects")
                        .select("*")
                        .eq("id", project_id)
                        .single()
                        .execute()
                    )
                    project = proj_res.data or {}
                except Exception:
                    project = {}

                context = _build_rich_context(project_id, project, sb)
                messages = history + [{"role": "user", "content": user_input}]

                with st.spinner(f"{selected} tänker..."):
                    reply, tokens, cost = route_message(
                        selected,
                        messages,
                        project_context=context,
                        max_tokens=800,
                    )

                # Uppdatera session state
                if history_key not in st.session_state:
                    st.session_state[history_key] = []
                st.session_state[history_key].append(
                    {"role": "user", "content": user_input})
                st.session_state[history_key].append(
                    {"role": "assistant", "content": reply})
                st.session_state["ss_chat_open"] = True

                # Spara i Supabase
                save_message(sb, project_id, "user", user_input,
                             agent=selected, model=agent["model"])
                save_message(sb, project_id, "assistant", reply,
                             agent=selected, model=agent["model"],
                             tokens=tokens, cost=cost)
                try:
                    log_tokens(sb, project_id, selected, agent["model"],
                               tokens // 2, tokens - tokens // 2, cost)
                except Exception:
                    pass

                st.rerun()
