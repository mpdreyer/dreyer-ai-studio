import streamlit as st
from db.portfolio_client import get_all_apps, get_active_projects_all
from core.state import set_active_project_id, set_active_view
from core.errors import error_boundary

CATEGORY_LABELS = {
    "client_tool": "Klientverktyg",
    "internal":    "Internt",
    "hobby":       "Hobby",
    "personal":    "Personligt",
}

PHASES = ["Brief", "Data", "Prompts", "Bygg", "Diavolo", "Demo", "Nästa steg"]

STATUS_CONFIG = {
    "active":      ("🟢", "Live",      "#EAF3DE", "#3B6D11"),
    "in_progress": ("🔵", "Pågår",     "#EEEDFE", "#3C3489"),
    "maintenance": ("🟡", "Underhåll", "#FAEEDA", "#633806"),
    "archived":    ("⚫", "Arkiverad", "#F1EFE8", "#444441"),
}


def load_or_create_project(sb, app: dict) -> str:
    app_name = app["name"]

    existing = (
        sb.table("projects")
        .select("*")
        .eq("name", app_name)
        .eq("company", "DTSM")
        .eq("status", "active")
        .limit(1)
        .execute()
    )
    if existing.data:
        project_id = existing.data[0]["id"]
    else:
        res = sb.table("projects").insert({
            "name":            app_name,
            "company":         "DTSM",
            "client":          "DTSM",
            "status":          "active",
            "current_phase":   1,
            "health_score":    75,
            "token_budget":    20.0,
            "deployment_mode": "cloud",
            "description":     app.get("description", ""),
        }).execute()
        project_id = res.data[0]["id"]

    # Sätt alltid explicit innan rerun
    set_active_project_id(project_id)
    st.session_state["active_app_name"] = app_name
    return project_id


def _status_badge(status: str) -> str:
    icon, label, bg, color = STATUS_CONFIG.get(status, STATUS_CONFIG["active"])
    return (
        f'<span style="background:{bg};color:{color};padding:2px 8px;'
        f'border-radius:4px;font-size:11px;font-family:monospace;">'
        f'{icon} {label}</span>'
    )


def _render_app_card(app: dict, sb):
    color    = app.get("color_hex", "#6366f1")
    icon     = app.get("icon", "📦")
    name     = app.get("name", "—")
    desc     = app.get("description", "")
    stack    = app.get("tech_stack") or []
    cat_key  = app.get("category", "")
    cat_lbl  = CATEGORY_LABELS.get(cat_key, cat_key)
    status   = app.get("status", "active")
    gh_url   = app.get("github_url")
    live_url = app.get("live_url")
    nb_id    = app.get("notebook_id")
    nb_url   = f"https://notebooklm.google.com/notebook/{nb_id}" if nb_id else None

    with st.container(border=True):
        col_main, col_actions = st.columns([4, 1])

        with col_main:
            st.markdown(
                f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:4px;">'
                f'<span style="font-size:22px;">{icon}</span>'
                f'<span style="font-weight:700;font-size:15px;color:#e8e8f0;">{name}</span>'
                f'<span style="font-size:9px;font-family:monospace;font-weight:600;'
                f'background:rgba(99,102,241,0.15);color:#6366f1;'
                f'border-radius:3px;padding:1px 6px;">DTSM</span>'
                f'&nbsp;{_status_badge(status)}'
                f'</div>'
                f'<div style="font-size:11px;color:#5a5a72;margin-bottom:8px;">{cat_lbl}</div>',
                unsafe_allow_html=True,
            )
            st.markdown(
                f'<div style="font-size:13px;color:#9090a8;margin-bottom:10px;">{desc}</div>',
                unsafe_allow_html=True,
            )
            if stack:
                st.markdown(" ".join(f"`{t}`" for t in stack))

        with col_actions:
            if st.button(
                "Öppna →",
                key=f"open_app_{app['id']}",
                use_container_width=True,
                type="primary",
            ):
                pid = load_or_create_project(sb, app)
                set_active_project_id(pid)
                st.session_state["active_app"] = name
                set_active_view("overview")
                st.rerun()

            if gh_url:
                st.link_button("GitHub", gh_url, use_container_width=True)
            if live_url:
                st.link_button("Live app", live_url, use_container_width=True)
            if nb_url:
                st.link_button("NotebookLM", nb_url, use_container_width=True)


@error_boundary
def render_portfolio(sb):
    # Header
    st.markdown(
        '<h1 style="font-family:\'JetBrains Mono\',monospace;font-size:28px;'
        'font-weight:700;color:#e8e8f0;letter-spacing:2px;margin-bottom:0;">DTSM</h1>',
        unsafe_allow_html=True,
    )
    st.caption("Dreyer Technology & Strategy Management")
    st.markdown("---")

    apps   = get_all_apps(sb)
    active = get_active_projects_all(sb)

    # ── AKTIVA PROJEKT ────────────────────────────────────────────────────────
    if active:
        st.markdown("### Aktiva projekt")
        for proj in active:
            cur   = proj.get("current_phase", 1)
            pname = PHASES[cur - 1] if 0 < cur <= len(PHASES) else "—"
            health = proj.get("health_score", 0)
            hcol = "#10b981" if health >= 75 else ("#f59e0b" if health >= 50 else "#ef4444")

            c_name, c_client, c_phase, c_health, c_btn = st.columns([3, 2, 2, 1, 1])
            with c_name:
                st.markdown(
                    f'<div style="font-weight:600;color:#e8e8f0;">{proj.get("name","—")}</div>',
                    unsafe_allow_html=True,
                )
            with c_client:
                st.markdown(
                    f'<div style="font-size:12px;color:#9090a8;">{proj.get("client","—")}</div>',
                    unsafe_allow_html=True,
                )
            with c_phase:
                st.markdown(
                    f'<div style="font-size:12px;color:#9090a8;">Fas {cur}/7 · {pname}</div>',
                    unsafe_allow_html=True,
                )
            with c_health:
                st.markdown(
                    f'<div style="font-size:12px;color:{hcol};font-weight:600;">{health}/100</div>',
                    unsafe_allow_html=True,
                )
            with c_btn:
                if st.button("Öppna", key=f"open_proj_{proj['id']}", use_container_width=True):
                    set_active_project_id(proj["id"])
                    set_active_view("overview")
                    st.rerun()

        st.markdown("---")

    # ── PORTFOLIO — dela upp i Live och Pågår ────────────────────────────────
    live_apps       = [a for a in apps if a.get("status") == "active"]
    inprogress_apps = [a for a in apps if a.get("status") == "in_progress"]
    other_apps      = [a for a in apps if a.get("status") not in ("active", "in_progress")]

    if live_apps:
        st.markdown("### 🟢 Live-appar")
        for app in live_apps:
            _render_app_card(app, sb)

    if inprogress_apps:
        st.markdown("### 🔵 Pågående projekt")
        st.info("Klicka 'Öppna →' för att starta arbetet med ett pågående projekt i Studio.")
        for app in inprogress_apps:
            _render_app_card(app, sb)

    if other_apps:
        st.markdown("### Övriga")
        for app in other_apps:
            _render_app_card(app, sb)

    st.markdown("---")
    if st.button("＋ Nytt DTSM-projekt", type="primary"):
        st.session_state["show_new_project"] = True
        st.rerun()
