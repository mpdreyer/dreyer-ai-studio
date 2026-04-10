import streamlit as st
from agents.council import AGENTS
from agents.router import route_message, detect_agent_from_message, build_project_context
from db.supabase_client import save_message, log_tokens, get_chat_history


def render_chat(project: dict | None, sb):
    """Fullständig rådslag-komponent med historik och streaming."""

    st.subheader("💬 Rådslag")
    if project:
        st.caption(f"Projekt: {project.get('name')} · {project.get('client')}")
    else:
        st.caption("Inget aktivt projekt")

    # Hämta historik
    project_id = project["id"] if project else None
    history = get_chat_history(sb, project_id) if project_id else []

    # Visa historik
    chat_container = st.container(height=400)
    with chat_container:
        for msg in history:
            role = msg["role"]
            agent_name = msg.get("agent", "Mattias")
            content = msg.get("content", "")
            model = msg.get("model", "")

            if role == "user":
                with st.chat_message("user"):
                    st.markdown(content)
            else:
                agent = AGENTS.get(agent_name, {})
                display = f"**{agent_name}** · *{model}*" if model else f"**{agent_name}**"
                with st.chat_message("assistant"):
                    st.caption(display)
                    st.markdown(content)

    # Inmatning
    st.markdown("---")
    col1, col2 = st.columns([4, 1])

    with col2:
        agents = list(AGENTS.keys())
        if "selected_agent" not in st.session_state:
            st.session_state["selected_agent"] = "Architetto"
        agent_choice = st.selectbox(
            "Agent",
            agents,
            index=agents.index(st.session_state.get("selected_agent", "Architetto")),
            key="chat_agent_select",
        )

    with col1:
        user_input = st.chat_input("Skriv till rådet...")

    if user_input:
        # Spara användarmeddelande
        if project_id:
            save_message(sb, project_id, "user", user_input, agent="Mattias")

        # Auto-detect agent om ingen specifik vald
        target_agent = agent_choice or detect_agent_from_message(user_input)

        # Bygg meddelandehistorik för API
        api_messages = []
        for msg in history[-10:]:  # Skicka max 10 historikmeddelanden
            api_messages.append({
                "role":    msg["role"] if msg["role"] == "user" else "assistant",
                "content": msg["content"],
            })
        api_messages.append({"role": "user", "content": user_input})

        # Anropa agent
        ctx = build_project_context(project) if project else ""

        with st.spinner(f"{target_agent} tänker..."):
            reply, tokens, cost = route_message(
                agent_name=target_agent,
                messages=api_messages,
                project_context=ctx,
                max_tokens=1024,
            )

        # Spara agentsvar
        if project_id:
            agent_model = AGENTS[target_agent]["model"]
            save_message(sb, project_id, "assistant", reply,
                        agent=target_agent, model=agent_model,
                        tokens=tokens, cost=cost)
            log_tokens(sb, project_id, target_agent, agent_model,
                      tokens // 2, tokens // 2, cost)

        st.rerun()
