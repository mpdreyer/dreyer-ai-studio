import streamlit as st


def render_topbar(project: dict | None):
    """Renderar topbar med projektinfo, Health Score och token-meter."""

    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])

    with col1:
        st.markdown("### 🏛️ Dreyer AI Studio")

    with col2:
        if project:
            health = project.get("health_score", 0)
            if health >= 75:
                color, label = "🟢", "Stabil"
            elif health >= 50:
                color, label = "🟡", "Marginell"
            else:
                color, label = "🔴", "Kritisk"
            st.metric(f"{color} Health", f"{health}/100", label)
        else:
            st.metric("Health", "—")

    with col3:
        if project:
            used  = project.get("token_used", 0)
            budget = project.get("token_budget", 20)
            pct   = used / budget * 100 if budget > 0 else 0
            st.metric("Token-kostnad", f"{used:.2f} USD", f"{pct:.0f}% av {budget:.0f} USD")
        else:
            st.metric("Tokens", "—")

    with col4:
        if project:
            phases = ["Brief", "Data", "Prompts", "Bygg", "Diavolo", "Demo", "Nästa steg"]
            cur = project.get("current_phase", 1)
            pname = phases[cur - 1] if 0 < cur <= len(phases) else "—"
            st.metric("Fas", f"{cur}/7", pname)
        else:
            st.metric("Fas", "—")

    st.divider()
