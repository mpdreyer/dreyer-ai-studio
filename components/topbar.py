import streamlit as st
from core.state import set_active_view


def render_topbar(project: dict | None, app_count: int = 6, active_project_count: int = 0):
    """Topbar med inline-stilar — oberoende av CSS-klasser."""

    # Gemensam badge-stil (JetBrains Mono, uppercase, square-ish)
    badge_base = (
        "display:inline-block;"
        "font-family:'JetBrains Mono',monospace;"
        "font-size:10px;"
        "font-weight:500;"
        "letter-spacing:0.5px;"
        "text-transform:uppercase;"
        "padding:3px 10px;"
        "border-radius:4px;"
        "border:1px solid;"
        "white-space:nowrap;"
    )

    sep = '<span style="color:#475569;margin:0 4px;">│</span>'

    if project:
        health = project.get("health_score", 0)
        if health >= 75:
            h_bg, h_border, h_color, h_label = "rgba(16,185,129,0.12)", "#10b981", "#10b981", "STABIL"
        elif health >= 50:
            h_bg, h_border, h_color, h_label = "rgba(245,158,11,0.12)", "#f59e0b", "#f59e0b", "MARGINAL"
        else:
            h_bg, h_border, h_color, h_label = "rgba(239,68,68,0.12)", "#ef4444", "#ef4444", "KRITISK"

        used   = project.get("token_used", 0)
        budget = project.get("token_budget", 20)
        pct    = used / budget * 100 if budget > 0 else 0

        phases = ["Brief", "Data", "Prompts", "Bygg", "Diavolo", "Demo", "Nästa steg"]
        cur    = project.get("current_phase", 1)
        pname  = phases[cur - 1] if 0 < cur <= len(phases) else "—"

        name   = project.get("name", "—").replace("<", "&lt;")
        client = (project.get("client") or "—").replace("<", "&lt;")

        badges = (
            f'<span style="{badge_base}background:rgba(255,255,255,0.03);border-color:rgba(255,255,255,0.08);color:#f1f5f9;">'
            f"{name} · {client}</span>"
            + sep
            + f'<span style="{badge_base}background:{h_bg};border-color:{h_border};color:{h_color};">'
            f"● {health}/100 {h_label}</span>"
            + sep
            + f'<span style="{badge_base}background:rgba(99,102,241,0.08);border-color:rgba(99,102,241,0.3);color:#94a3b8;">'
            f"{used:.2f}/{budget:.0f} USD ({pct:.0f}%)</span>"
            + sep
            + f'<span style="{badge_base}background:rgba(99,102,241,0.08);border-color:rgba(99,102,241,0.3);color:#94a3b8;">'
            f"FAS {cur}·7 {pname}</span>"
        )
    else:
        badges = (
            f'<span style="{badge_base}background:rgba(99,102,241,0.08);'
            f'border-color:rgba(99,102,241,0.3);color:#94a3b8;">{app_count} APPAR</span>'
            + sep
            + f'<span style="{badge_base}background:rgba(255,255,255,0.03);'
            f'border-color:rgba(255,255,255,0.08);color:#475569;">{active_project_count} AKTIVA PROJEKT</span>'
        )

    html = f"""
    <div style="
      display:flex;
      align-items:center;
      gap:10px;
      padding:10px 24px;
      background:linear-gradient(180deg,#0d1120 0%,#080b14 100%);
      border-bottom:1px solid rgba(99,102,241,0.15);
      border-radius:0 0 8px 8px;
      margin:-1rem -2rem 1.5rem;
      flex-wrap:nowrap;
      overflow:hidden;
    ">
      <span style="
        font-family:'JetBrains Mono',monospace;
        font-size:15px;
        font-weight:700;
        color:#6366f1;
        letter-spacing:2px;
        text-transform:uppercase;
        white-space:nowrap;
        flex-shrink:0;
      ">DTSM · AI STUDIO</span>

      <span style="flex:1;"></span>

      {badges}
    </div>
    """
    col_html, col_btn = st.columns([20, 1])
    with col_html:
        st.markdown(html, unsafe_allow_html=True)
    with col_btn:
        if st.button("🐛", help="Rapportera bugg eller förbättring",
                     use_container_width=True):
            set_active_view("issues")
            st.rerun()
