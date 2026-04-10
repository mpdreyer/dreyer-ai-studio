"""
Dreyer AI Studio — NotebookLM dokumentationsmotor
Synkar systemdokumentation till NotebookLM-notebooks automatiskt.
"""

import streamlit as st
from datetime import datetime


# ── Hjälpfunktioner ───────────────────────────────────────────────────────────

def _get_notebooks(sb) -> dict:
    """Hämtar app_notebooks-tabellen som dict keyed på app_name."""
    try:
        res = sb.table("app_notebooks").select("*").execute()
        return {row["app_name"]: row for row in (res.data or [])}
    except Exception:
        return {}


def _save_notebook_id(sb, app_name: str, notebook_id: str):
    try:
        sb.table("app_notebooks").upsert(
            {"app_name": app_name, "notebook_id": notebook_id},
            on_conflict="app_name",
        ).execute()
    except Exception as e:
        st.error(f"Kunde inte spara notebook-ID: {e}")


def _mark_synced(sb, app_name: str):
    try:
        sb.table("app_notebooks").update(
            {"last_synced": datetime.utcnow().isoformat()}
        ).eq("app_name", app_name).execute()
    except Exception:
        pass


def _mono(text: str, color: str = "#94a3b8") -> str:
    return (
        f'<span style="font-family:\'JetBrains Mono\',monospace;'
        f'font-size:11px;color:{color};">{text}</span>'
    )


def _badge(label: str, color: str) -> str:
    return (
        f'<span style="font-family:\'JetBrains Mono\',monospace;font-size:9px;'
        f'font-weight:600;letter-spacing:0.5px;text-transform:uppercase;'
        f'padding:2px 8px;border-radius:3px;border:1px solid {color}40;'
        f'color:{color};background:{color}15;">{label}</span>'
    )


# ── Sektion 1 — Auth-status ───────────────────────────────────────────────────

def _render_auth_section() -> tuple[bool, bool]:
    """
    Renderar auth-status.
    Returnerar (mcp_active, nlm_cli_active).
    """
    from helpers.notebooklm_auth import check_mcp_process, check_auth_status, save_cookies
    from components.notebooklm_sync import check_nlm_auth

    mcp_active  = check_mcp_process()
    nlm_active  = check_nlm_auth()
    auth_status = check_auth_status()

    col_mcp, col_nlm, col_info = st.columns([1, 1, 3])

    with col_mcp:
        color = "#10b981" if mcp_active else "#ef4444"
        label = "● MCP AKTIV" if mcp_active else "● MCP EJ AKTIV"
        st.markdown(
            f'<div style="background:{color}1a;border:1px solid {color}40;'
            f'border-radius:6px;padding:10px 14px;text-align:center;">'
            f'{_mono(label, color)}</div>',
            unsafe_allow_html=True,
        )

    with col_nlm:
        color = "#6366f1" if nlm_active else "#f59e0b"
        label = "● nlm AKTIV" if nlm_active else "● nlm EJ AUTH"
        st.markdown(
            f'<div style="background:{color}1a;border:1px solid {color}40;'
            f'border-radius:6px;padding:10px 14px;text-align:center;">'
            f'{_mono(label, color)}</div>',
            unsafe_allow_html=True,
        )

    with col_info:
        if mcp_active:
            st.markdown(
                '<div style="font-size:12px;color:#94a3b8;">'
                'MCP aktiv — direkt synk tillgänglig.</div>',
                unsafe_allow_html=True,
            )
        elif nlm_active:
            st.markdown(
                '<div style="font-size:12px;color:#94a3b8;">'
                'nlm CLI aktiv med persistent Google-auth — synkar utan cookies.</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                '<div style="font-size:12px;color:#94a3b8;">'
                'Varken MCP eller nlm är aktiva. Kör <code>nlm login</code> i terminalen '
                'för persistent autentisering.</div>',
                unsafe_allow_html=True,
            )

    if not mcp_active and not nlm_active:
        with st.expander("🔑 Autentiseringsalternativ", expanded=False):
            st.markdown(
                "**Alternativ 1 — nlm CLI (rekommenderat, persistent):**\n\n"
                "```\nnlm login\n```\n\n"
                "Kör en gång — autentiseringen sparas i macOS Keychain.\n\n"
                "---\n\n"
                "**Alternativ 2 — Manuell cookie-klistring (temporär):**"
            )
            saved = auth_status.get("saved_at", "aldrig")
            n     = auth_status.get("n_cookies", 0)
            st.caption(f"Senast sparad cookie-auth: {saved} ({n} cookies)")
            cookie_input = st.text_area(
                "Klistra in cookies här",
                height=80,
                placeholder="__Secure-1PSID=...; __Secure-1PAPISID=...; ...",
                key="nlm_cookie_input",
            )
            if st.button("🔑 Spara cookies", key="nlm_save_cookies") and cookie_input.strip():
                try:
                    save_cookies(cookie_input.strip())
                    st.success("✓ Cookies sparade!")
                except Exception as e:
                    st.error(f"Kunde inte spara cookies: {e}")

    return mcp_active, nlm_active


# ── Sektion 2 — App-notebook-tabell ──────────────────────────────────────────

def _render_notebook_table(sb, notebooks: dict, apps: list) -> str | None:
    """Renderar notebook-tabell. Returnerar vald app-namn eller None."""
    st.markdown(
        '<div style="font-family:\'JetBrains Mono\',monospace;font-size:10px;'
        'font-weight:600;letter-spacing:1px;text-transform:uppercase;'
        'color:#475569;margin:16px 0 8px;">APP-NOTEBOOKS</div>',
        unsafe_allow_html=True,
    )

    selected_app = None

    for app_name in apps:
        nb   = notebooks.get(app_name, {})
        nid  = nb.get("notebook_id") or ""
        last = nb.get("last_synced")
        last_str = datetime.fromisoformat(last).strftime("%d %b %H:%M") if last else "aldrig"
        status_html = _badge("● SYNKAD", "#10b981") if last else _badge("⚠ EJ SYNKAD", "#f59e0b")

        col_name, col_id, col_last, col_status, col_btn = st.columns([2, 2, 1, 1, 1])

        with col_name:
            st.markdown(
                f'<div style="font-family:\'JetBrains Mono\',monospace;'
                f'font-size:12px;color:#f1f5f9;padding:8px 0;">{app_name}</div>',
                unsafe_allow_html=True,
            )
        with col_id:
            new_id = st.text_input(
                "notebook_id",
                value=nid,
                key=f"nbid_{app_name}",
                label_visibility="collapsed",
                placeholder="notebook-id…",
            )
            if new_id != nid and new_id.strip():
                _save_notebook_id(sb, app_name, new_id.strip())
        with col_last:
            st.markdown(
                f'<div style="font-size:10px;color:#475569;padding:8px 0;">{last_str}</div>',
                unsafe_allow_html=True,
            )
        with col_status:
            st.markdown(
                f'<div style="padding:8px 0;">{status_html}</div>',
                unsafe_allow_html=True,
            )
        with col_btn:
            action = "Skapa" if not nid else "Synka"
            if st.button(action, key=f"action_{app_name}", use_container_width=True):
                selected_app = app_name

    return selected_app


# ── Sektion 3 — Synk per app ─────────────────────────────────────────────────

def _render_sync_section(app_name: str, notebook_id: str, mcp_active: bool, nlm_active: bool, sb):
    from components.notebooklm_sync import (
        render_mode_a_button,
        render_mode_cli,
        render_mode_b_prompt,
        render_mode_c_export,
    )

    st.markdown(
        f'<div style="background:#111827;border:1px solid rgba(255,255,255,0.04);'
        f'border-left:3px solid #6366f1;border-radius:6px;padding:14px 18px;'
        f'margin:12px 0;">'
        f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:13px;'
        f'font-weight:700;color:#f1f5f9;margin-bottom:4px;">⚡ {app_name}</div>'
        f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:10px;'
        f'color:#475569;">NOTEBOOK: {notebook_id or "EJ KONFIGURERAD"}</div>'
        f'</div>',
        unsafe_allow_html=True,
    )

    tab_a, tab_b, tab_c, tab_d = st.tabs(["⚡ Direkt MCP", "📡 nlm CLI", "📋 Prompt", "⬇️ Export"])

    with tab_a:
        if mcp_active:
            render_mode_a_button(app_name, notebook_id)
            if st.session_state.get(f"docs_{app_name}") and notebook_id:
                _mark_synced(sb, app_name)
        else:
            st.markdown(
                '<div style="font-size:12px;color:#475569;padding:8px 0;">'
                'MCP-processen är inte aktiv.</div>',
                unsafe_allow_html=True,
            )

    with tab_b:
        if nlm_active:
            render_mode_cli(app_name, notebook_id)
            if st.session_state.get(f"docs_{app_name}") and notebook_id:
                _mark_synced(sb, app_name)
        else:
            st.markdown(
                '<div style="font-size:12px;color:#475569;padding:8px 0;">'
                'nlm CLI inte autentiserat. Kör <code>nlm login</code> i terminalen.</div>',
                unsafe_allow_html=True,
            )

    with tab_c:
        render_mode_b_prompt(app_name, notebook_id)

    with tab_d:
        render_mode_c_export(app_name)


# ── Huvud-render ──────────────────────────────────────────────────────────────

def render_notebooklm(project, sb):
    st.markdown("## 📚 NotebookLM")
    st.markdown(
        '<div style="font-family:\'Inter\',sans-serif;font-size:13px;color:#94a3b8;'
        'margin-bottom:16px;">Automatisk systemdokumentation synkad till NotebookLM-notebooks.</div>',
        unsafe_allow_html=True,
    )

    APPS = ["Dreyer AI Studio", "Dreyer Council", "DiscCaddy", "Tactical 24H"]

    # ── Sektion 1: Auth
    st.markdown("---")
    mcp_active, nlm_active = _render_auth_section()

    # ── Sektion 2: Tabell
    st.markdown("---")
    notebooks   = _get_notebooks(sb)
    selected    = _render_notebook_table(sb, notebooks, APPS)

    # ── Sektion 3: Synk-panel
    if selected:
        st.session_state["nlm_selected_app"] = selected

    active_app = st.session_state.get("nlm_selected_app")
    if active_app:
        st.markdown("---")
        nb_row     = notebooks.get(active_app, {})
        nb_id      = nb_row.get("notebook_id") or ""
        _render_sync_section(active_app, nb_id, mcp_active, nlm_active, sb)
    else:
        st.markdown(
            '<div style="font-size:12px;color:#475569;padding:12px 0;">'
            'Klicka på "Synka" eller "Skapa" för en app ovan för att öppna synk-panelen.</div>',
            unsafe_allow_html=True,
        )
