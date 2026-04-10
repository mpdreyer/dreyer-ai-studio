import streamlit as st
from agents.council import AGENTS, PHASES, PROVIDER_STYLES
from agents.router import route_message, build_project_context, AGENT_MODEL_MAP
from db.supabase_client import save_message, log_tokens, get_chat_history
from core.errors import error_boundary


def _model_badge_html(model_display: str) -> str:
    style = PROVIDER_STYLES.get(model_display, {"bg": "#1e2130", "color": "#94a3b8"})
    return (
        f'<span style="font-family:\'JetBrains Mono\',monospace;font-size:9px;'
        f'font-weight:600;letter-spacing:0.3px;padding:1px 6px;border-radius:3px;'
        f'background:{style["bg"]};color:{style["color"]};">{model_display}</span>'
    )


def _agent_card_html(name: str, agent: dict, active: bool = False) -> str:
    initials      = agent.get("initials", name[:2].upper())
    role          = agent.get("role", "—")
    model_display = agent.get("model_display", "Claude")
    bg            = agent.get("color_bg", "#1e2130")
    fg            = agent.get("color_text", "#AFA9EC")
    status        = agent.get("status", "idle")
    extra_cls     = "active" if active else ("diavolo" if name == "Diavolo" else "")
    dot_cls       = "red" if name == "Diavolo" else status
    badge         = _model_badge_html(model_display)

    return f"""
    <div class="agent-card {extra_cls}">
      <div class="agent-initials" style="background:{bg};color:{fg};">{initials}</div>
      <div class="agent-name">{name}</div>
      <div class="agent-role">{role}</div>
      <div style="display:flex;align-items:center;gap:6px;flex-wrap:wrap;">
        <span class="status-dot {dot_cls}"></span>
        {badge}
      </div>
    </div>
    """


@error_boundary
def render_council(project: dict | None, sb):
    st.markdown("## 🏛️ Rådet")

    if not project:
        st.info("Skapa ett projekt för att starta råd-sessionen.")
        return

    active_agent = st.session_state.get("active_agent", "Architetto")

    # Agent-grid (3 kolumner × 4 rader)
    agent_names = list(AGENTS.keys())
    cols_per_row = 4
    rows = [agent_names[i:i + cols_per_row] for i in range(0, len(agent_names), cols_per_row)]

    for row in rows:
        cols = st.columns(len(row))
        for col, name in zip(cols, row):
            with col:
                is_active = name == active_agent
                st.markdown(_agent_card_html(name, AGENTS[name], is_active), unsafe_allow_html=True)
                if st.button(
                    "Välj" if not is_active else "✓ Aktiv",
                    key=f"select_agent_{name}",
                    type="primary" if is_active else "secondary",
                    use_container_width=True,
                ):
                    st.session_state["active_agent"] = name
                    st.rerun()

    st.divider()

    # Fas + projekt-info
    col_fas, col_info = st.columns([2, 3])
    with col_fas:
        phase = st.selectbox("Fas", PHASES, index=project.get("current_phase", 1) - 1, key="council_phase")
    with col_info:
        st.markdown(
            f'<div style="font-size:11px;color:#9090a8;padding-top:28px;">'
            f'Projekt: <b style="color:#e8e8f0">{project["name"]}</b> · '
            f'{project.get("client","—")} · '
            f'{len(AGENTS)} agenter aktiva</div>',
            unsafe_allow_html=True,
        )

    # Chatthistorik
    history = get_chat_history(sb, project["id"])

    chat_html = ""
    for msg in history:
        role       = msg["role"]
        content    = msg.get("content", "").replace("<", "&lt;").replace(">", "&gt;")
        agent_name = msg.get("agent") or ("Du" if role == "user" else "Agent")
        agent_data = AGENTS.get(agent_name, {})
        initials   = agent_data.get("initials", agent_name[:2].upper()) if role != "user" else "DU"
        bg         = agent_data.get("color_bg", "#2a2d3e") if role != "user" else "#7F77DD"
        fg         = agent_data.get("color_text", "#AFA9EC") if role != "user" else "#fff"
        bubble_cls = "user" if role == "user" else ("diavolo" if agent_name == "Diavolo" else "")
        name_line  = "" if role == "user" else f'<div class="chat-agent-name">{agent_name}</div>'

        chat_html += f"""
        <div class="chat-message">
          <div class="chat-avatar" style="background:{bg};color:{fg};">{initials}</div>
          <div class="chat-bubble {bubble_cls}">
            {name_line}
            {content}
          </div>
        </div>
        """

    if chat_html:
        st.markdown(chat_html, unsafe_allow_html=True)
    else:
        st.markdown(
            '<div style="color:#5a5a72;font-size:13px;padding:16px 0;">'
            'Inga meddelanden ännu. Välj en agent och skriv en fråga.</div>',
            unsafe_allow_html=True,
        )

    # Inmatning
    prompt = st.chat_input(f"Skriv till {active_agent}…")
    if prompt:
        agent      = AGENTS.get(active_agent, AGENTS["Architetto"])
        ctx        = build_project_context(project)
        messages   = [{"role": m["role"], "content": m["content"]} for m in history]
        messages  += [{"role": "user", "content": prompt}]

        with st.spinner(f"{active_agent} tänker…"):
            content, total_tokens, cost = route_message(active_agent, messages, ctx)

        save_message(sb, project["id"], "user", prompt)
        save_message(
            sb, project["id"], "assistant", content,
            agent=active_agent, model=agent["model"],
            tokens=total_tokens, cost=cost,
        )
        log_tokens(
            sb, project["id"], active_agent, agent["model"],
            tokens_in=total_tokens // 2,
            tokens_out=total_tokens - total_tokens // 2,
            cost=cost,
        )
        st.rerun()
