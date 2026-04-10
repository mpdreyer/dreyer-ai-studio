import streamlit as st
from agents.council import AGENTS
from agents.router import route_message, build_project_context
from db.supabase_client import save_message, log_tokens


def render_council(project: dict | None, sb):
    st.subheader("🏛️ Rådet — 12 agenter")
    st.caption("Klicka på en agent för att tala direkt med den.")

    project_id = project["id"] if project else None
    ctx = build_project_context(project) if project else ""

    # Visa agenter i grid (3 per rad)
    agent_items = list(AGENTS.items())
    for row_start in range(0, len(agent_items), 3):
        cols = st.columns(3)
        for col, (agent_name, agent) in zip(cols, agent_items[row_start:row_start+3]):
            with col:
                # Statusfärg
                status_color = "🟢" if agent["status"] == "active" else "🟡" if agent["status"] == "busy" else "⚪"
                border = "2px solid #E24B4A" if agent_name == "Diavolo" else "1px solid #eee"

                with st.container(border=True):
                    st.markdown(f"**{agent['initials']} · {agent_name}**")
                    st.caption(agent["role"])
                    st.caption(f"{status_color} {agent['status'].capitalize()} · {agent['model'].split('-')[1].upper()}")
                    st.caption(f"~{agent['cost_per_1k']*1000:.3f} USD/1k tok")

                    if st.button(f"Tala med {agent_name}", key=f"btn_{agent_name}", use_container_width=True):
                        st.session_state["selected_agent"] = agent_name
                        st.session_state["active_view"] = "chat"
                        st.rerun()

    st.divider()

    # Snabb-brief till hela rådet
    st.markdown("**Skicka till hela rådet**")
    broadcast = st.text_area("Brief eller fråga till alla agenter...", height=80, key="broadcast_input")

    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("🏛️ Skicka till rådet", use_container_width=True) and broadcast:
            # Architetto svarar på vegnar av rådet
            with st.spinner("Rådet diskuterar..."):
                council_prompt = f"""Mattias har skickat följande till hela rådet:

"{broadcast}"

Svara som Architetto — sammanfatta rådets kollektiva perspektiv och delegera tydligt 
vilken agent som tar ansvar för vad. Nämn specifikt vilka rådsmedlemmar som är relevanta."""

                reply, tokens, cost = route_message(
                    agent_name="Architetto",
                    messages=[{"role": "user", "content": council_prompt}],
                    project_context=ctx,
                    max_tokens=800,
                )

            if project_id:
                save_message(sb, project_id, "user", broadcast, agent="Mattias")
                save_message(sb, project_id, "assistant", reply,
                           agent="Architetto", model=AGENTS["Architetto"]["model"],
                           tokens=tokens, cost=cost)
                log_tokens(sb, project_id, "Architetto", AGENTS["Architetto"]["model"],
                          tokens // 2, tokens // 2, cost)

            st.success(f"**Architetto:** {reply}")
