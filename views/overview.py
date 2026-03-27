import streamlit as st
from db.supabase_client import get_tasks, get_deliverables, get_token_summary

PHASES = ["Brief", "Data", "Prompts", "Bygg", "Diavolo", "Demo", "Nästa steg"]


def render_overview(project: dict | None, sb):
    st.subheader("📊 Projektöversikt")

    if not project:
        st.info("Inget aktivt projekt. Skapa ett nytt projekt för att börja.")
        return

    project_id = project["id"]

    # Metriker
    col1, col2, col3, col4 = st.columns(4)
    tasks = get_tasks(sb, project_id)
    done  = sum(1 for t in tasks if t["status"] == "done")
    used  = project.get("token_used", 0)
    budget = project.get("token_budget", 20)
    cur   = project.get("current_phase", 1)

    col1.metric("Fas", f"{cur}/7", PHASES[cur-1] if 0 < cur <= 7 else "—")
    col2.metric("Uppgifter klara", f"{done}/{len(tasks)}", f"{done/max(len(tasks),1)*100:.0f}%")
    col3.metric("Token-kostnad", f"{used:.2f} USD", f"av {budget:.0f} USD budget")
    col4.metric("Health Score", f"{project.get('health_score',0)}/100")

    # Fasindikator
    st.markdown("**Projektfaser**")
    phase_cols = st.columns(7)
    for i, (col, phase) in enumerate(zip(phase_cols, PHASES), 1):
        if i < cur:
            col.success(phase)
        elif i == cur:
            col.info(f"**{phase}**")
        else:
            col.markdown(f"<div style='text-align:center;color:gray;font-size:12px'>{phase}</div>", unsafe_allow_html=True)

    st.divider()

    # Agentaktivitet och senaste uppgifter
    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown("**Senaste uppgifter**")
        recent_tasks = sorted(tasks, key=lambda x: x["created_at"], reverse=True)[:5]
        if not recent_tasks:
            st.caption("Inga uppgifter ännu.")
        for task in recent_tasks:
            status = task.get("status", "todo")
            icon = "✅" if status == "done" else "🔴" if task.get("blocks_delivery") else "🔄" if status == "in_progress" else "⭕"
            st.markdown(f"{icon} **{task['title']}** · {task.get('owner_agent','—')}")

    with col_b:
        st.markdown("**Token-förbrukning per agent**")
        token_summary = get_token_summary(sb, project_id)
        if not token_summary:
            st.caption("Ingen tokenanvändning ännu.")
        for row in token_summary[:6]:
            pct = min(row["cost"] / max(used, 0.001) * 100, 100)
            st.progress(int(pct), text=f"{row['agent']} — {row['tokens']:,} tok · {row['cost']:.4f} USD")
