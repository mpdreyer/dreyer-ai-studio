import streamlit as st
from db.supabase_client import get_tasks
from agents.council import agent_list

PHASES = ["Brief", "Data", "Prompts", "Bygg", "Diavolo", "Demo", "Nästa steg"]
STATUS_OPTIONS = ["todo", "in_progress", "done"]
STATUS_ICONS   = {"todo": "⭕", "in_progress": "🔄", "done": "✅"}


def render_tasks(project: dict | None, sb):
    st.subheader("✅ Uppgifter")

    if not project:
        st.info("Inget aktivt projekt.")
        return

    project_id = project["id"]
    tasks = get_tasks(sb, project_id)

    # Ny uppgift
    with st.expander("+ Ny uppgift", expanded=False):
        with st.form("new_task_form"):
            title  = st.text_input("Titel")
            col1, col2, col3 = st.columns(3)
            with col1:
                owner  = st.selectbox("Agent", agent_list())
            with col2:
                phase  = st.selectbox("Fas", list(range(1, 8)), format_func=lambda x: f"{x}. {PHASES[x-1]}")
            with col3:
                blocks = st.checkbox("Blockar leverans")
            submitted = st.form_submit_button("Lägg till")

            if submitted and title:
                sb.table("tasks").insert({
                    "project_id": project_id,
                    "title": title,
                    "owner_agent": owner,
                    "phase": phase,
                    "status": "todo",
                    "blocks_delivery": blocks,
                }).execute()
                st.rerun()

    st.divider()

    # Visa uppgifter grupperade per fas
    for phase_num in range(1, 8):
        phase_tasks = [t for t in tasks if t.get("phase") == phase_num]
        if not phase_tasks:
            continue

        cur = project.get("current_phase", 1)
        phase_label = PHASES[phase_num - 1]
        prefix = "✅" if phase_num < cur else "▶️" if phase_num == cur else "⏳"

        with st.expander(f"{prefix} Fas {phase_num} — {phase_label} ({len(phase_tasks)} uppgifter)", expanded=(phase_num == cur)):
            for task in phase_tasks:
                col1, col2, col3, col4 = st.columns([3, 1, 1, 1])

                with col1:
                    icon = STATUS_ICONS.get(task["status"], "⭕")
                    badge = " 🔴" if task.get("blocks_delivery") else ""
                    st.markdown(f"{icon} **{task['title']}**{badge}")
                    st.caption(f"Agent: {task.get('owner_agent', '—')}")

                with col2:
                    new_status = st.selectbox(
                        "Status",
                        STATUS_OPTIONS,
                        index=STATUS_OPTIONS.index(task.get("status", "todo")),
                        key=f"status_{task['id']}",
                        label_visibility="collapsed",
                    )
                    if new_status != task.get("status"):
                        sb.table("tasks").update({"status": new_status}).eq("id", task["id"]).execute()
                        st.rerun()

                with col3:
                    if task.get("blocks_delivery"):
                        st.error("Blockar")

                with col4:
                    if st.button("🗑️", key=f"del_{task['id']}", help="Ta bort"):
                        sb.table("tasks").delete().eq("id", task["id"]).execute()
                        st.rerun()
