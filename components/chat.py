import streamlit as st
from agents.council import AGENTS, PROVIDER_STYLES
from agents.router import route_message, detect_agent_from_message, build_project_context
from db.supabase_client import save_message, log_tokens, get_chat_history
from core.errors import error_boundary


def _model_badge_inline(model_display: str) -> str:
    style = PROVIDER_STYLES.get(model_display, {"bg": "#1e2130", "color": "#94a3b8"})
    return (
        f'<span style="font-family:\'JetBrains Mono\',monospace;font-size:9px;'
        f'font-weight:600;letter-spacing:0.3px;padding:1px 6px;border-radius:3px;'
        f'background:{style["bg"]};color:{style["color"]};margin-left:6px;">'
        f'{model_display}</span>'
    )


@error_boundary
def render_chat(project: dict | None, sb):
    st.markdown("## 💬 Rådslag")

    if project:
        st.markdown(
            f'<div style="font-size:11px;color:#9090a8;margin-bottom:12px;">'
            f'Projekt: <b style="color:#e8e8f0">{project.get("name")}</b> · '
            f'{project.get("client","—")}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="font-size:11px;color:#9090a8;margin-bottom:12px;">Inget aktivt projekt</div>',
            unsafe_allow_html=True,
        )

    project_id = project["id"] if project else None
    history    = get_chat_history(sb, project_id) if project_id else []

    # Chattbubblar
    chat_html = ""
    for msg in history:
        role       = msg["role"]
        content    = msg.get("content", "").replace("<", "&lt;").replace(">", "&gt;")
        agent_name = msg.get("agent") or ("Du" if role == "user" else "Agent")
        model      = msg.get("model", "")
        agent_data = AGENTS.get(agent_name, {})

        if role == "user":
            initials   = "DU"
            bg, fg     = "#7F77DD", "#fff"
            bubble_cls = "user"
            name_line  = ""
        else:
            initials   = agent_data.get("initials", agent_name[:2].upper())
            bg         = agent_data.get("color_bg", "#2a2d3e")
            fg         = agent_data.get("color_text", "#AFA9EC")
            bubble_cls = "diavolo" if agent_name == "Diavolo" else ""
            model_display = agent_data.get("model_display", "Claude")
            model_badge   = _model_badge_inline(model_display)
            name_line     = f'<div class="chat-agent-name">{agent_name}{model_badge}</div>'

        chat_html += f"""
        <div class="chat-message">
          <div class="chat-avatar" style="background:{bg};color:{fg};">{initials}</div>
          <div class="chat-bubble {bubble_cls}">
            {name_line}{content}
          </div>
        </div>
        """

    if chat_html:
        st.markdown(
            f'<div style="max-height:480px;overflow-y:auto;padding-right:4px;">'
            f'{chat_html}</div>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<div style="color:#5a5a72;font-size:13px;padding:20px 0;">'
            'Inga meddelanden ännu.</div>',
            unsafe_allow_html=True,
        )

    st.markdown("---")

    # Agent-väljare + inmatning
    col_input, col_agent = st.columns([4, 1])
    with col_agent:
        agents = list(AGENTS.keys())
        agent_choice = st.selectbox(
            "Agent",
            agents,
            index=agents.index(st.session_state.get("selected_agent", "Architetto")),
            key="chat_agent_select",
            label_visibility="collapsed",
        )
    with col_input:
        user_input = st.chat_input("Skriv till rådet…")

    if user_input:
        target_agent = agent_choice or detect_agent_from_message(user_input)
        agent        = AGENTS.get(target_agent, AGENTS["Architetto"])

        if project_id:
            save_message(sb, project_id, "user", user_input)

        api_messages = [
            {"role": m["role"] if m["role"] == "user" else "assistant", "content": m["content"]}
            for m in history[-10:]
        ] + [{"role": "user", "content": user_input}]

        ctx = build_project_context(project) if project else ""

        with st.spinner(f"{target_agent} tänker…"):
            reply, tokens, cost = route_message(
                agent_name=target_agent,
                messages=api_messages,
                project_context=ctx,
                max_tokens=1024,
            )

        if project_id:
            save_message(
                sb, project_id, "assistant", reply,
                agent=target_agent, model=agent["model"],
                tokens=tokens, cost=cost,
            )
            log_tokens(sb, project_id, target_agent, agent["model"],
                       tokens // 2, tokens - tokens // 2, cost)

        st.rerun()
