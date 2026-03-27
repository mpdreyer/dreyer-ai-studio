import streamlit as st
from agents.council import AGENTS, PHASES
from agents.router import route_message, build_project_context
from db.supabase_client import save_message, log_tokens, get_chat_history


def render_council(project: dict | None, sb):
    st.subheader("🏛️ Rådet")
    if not project:
        st.info("Skapa ett projekt för att starta råd-sessionen.")
        return
    st.caption(f"Projekt: **{project['name']}** · {len(AGENTS)} aktiva agenter")

    # Fas-selector
    phase = st.selectbox("Fas", PHASES, key="council_phase")

    # Chatthistorik
    history = get_chat_history(sb, project["id"], session_type="council")
    for msg in history:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Inmatning
    prompt = st.chat_input("Skriv till rådet…")
    if prompt:
        with st.chat_message("user"):
            st.markdown(prompt)
        ctx = build_project_context(project)
        agent_key = st.session_state.get("active_agent", "Architetto")
        result = route_message(prompt, agent_key, history, ctx)
        with st.chat_message("assistant"):
            st.markdown(result["content"])
        save_message(sb, project["id"], "user", prompt, session_type="council")
        save_message(sb, project["id"], "assistant", result["content"],
                     agent=agent_key, session_type="council")
        log_tokens(sb, project["id"], agent_key, result.get("input_tokens", 0),
                   result.get("output_tokens", 0))
        st.rerun()
