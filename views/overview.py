import streamlit as st
from db.supabase_client import (
    get_tasks, get_deliverables, get_token_summary,
    get_chat_history, save_message, log_tokens,
)
from core.errors import error_boundary
from agents.router import route_message, build_project_context
from agents.council import AGENTS

PHASES = ["Brief", "Data", "Prompts", "Bygg", "Diavolo", "Demo", "Nästa steg"]

PHASE_ACTIONS = {
    1: [
        ("📝 Brief med Architetto",
         "Hjälp mig skriva en strukturerad brief för detta projekt. "
         "Inkludera: syfte, målgrupp, success criteria och tekniska krav."),
        ("🎯 Definiera success criteria",
         "Hjälp mig definiera tydliga och mätbara success criteria för projektet."),
    ],
    2: [
        ("🗄️ Kartlägg datakällor",
         "Du är Datatjej. Hjälp mig kartlägga vilka datakällor som behövs för projektet "
         "och hur de ska integreras. Vilka API:er och databaser behövs?"),
        ("🔌 Designa API-integration",
         "Du är Datatjej. Designa en API-integrationsplan för projektet. "
         "Vilka endpoints, autentisering och dataformat behövs?"),
    ],
    3: [
        ("🧪 Starta prompt-testning",
         "Du är Logica. Hjälp mig designa ett systematiskt test-upplägg för prompt-varianterna. "
         "Vilka edge cases ska vi testa och hur mäter vi precision?"),
        ("📊 Prompt-strategi",
         "Du är Logica. Rekommendera en prompt-strategi för projektet. "
         "Vilka tekniker (few-shot, CoT, system prompts) passar bäst?"),
    ],
    4: [
        ("💻 Koduppdrag till Codex",
         "Du är Codex. Ge mig ett konkret implementationsförslag för nästa byggsteg i projektet. "
         "Inkludera filstruktur, huvudfunktioner och kodexempel."),
        ("🏗️ Arkitekturgenomgång",
         "Du är Codex. Gör en snabb arkitekturgenomgång. "
         "Är strukturen skalbar? Finns det teknisk skuld vi bör hantera nu?"),
    ],
    5: [
        ("🔴 Red team-analys",
         "Du är Diavolo. Kör en red team-analys av projektet. "
         "Angrip från tre perspektiv: Säkerhet, Etik/Bias och Kraschtest. "
         "Rangordna fynden med severity HÖG/MEDIUM/LÅG."),
        ("🛡️ GDPR-granskning",
         "Du är Guardiano. Granska projektet ur GDPR- och AI Act-perspektiv. "
         "Flagga risker och ge konkreta åtgärdsrekommendationer."),
    ],
    6: [
        ("🎤 Bygg demo-script",
         "Du är Narratrix. Hjälp mig bygga ett övertygande demo-script för kunden. "
         "Fokus på ROI-argument och konkreta use cases. Max 10 minuter."),
        ("💰 Generera ROI-rapport",
         "Du är Narratrix. Beräkna och presentera ROI för projektet. "
         "Inkludera kostnadsbesparingar, effektivitetsvinster och payback-tid."),
    ],
    7: [
        ("📚 Synka till NotebookLM",
         "Projektet är nu klart. Summera de viktigaste lärdomarna och besluten "
         "så att vi kan synka dem till NotebookLM som dokumentation."),
        ("🏛️ Pattern Memory",
         "Du är Memoria. Indexera detta projekt i pattern memory. "
         "Vilka mönster och lösningar från detta projekt bör återanvändas i framtiden?"),
    ],
}


def _update_phase(sb, project_id: str, phase: int):
    sb.table("projects").update({"current_phase": phase}).eq("id", project_id).execute()
    if phase == 7:
        st.info("🎉 Projekt klart! Genererar användarmanual automatiskt...")
        st.session_state["ss_active_view"] = "user_manual"
        st.session_state["auto_generate_manual"] = True
    st.rerun()


def _health_color(health: int) -> tuple[str, str, str]:
    if health >= 75:
        return "rgba(16,185,129,0.12)", "#10b981", "STABIL"
    elif health >= 50:
        return "rgba(245,158,11,0.12)", "#f59e0b", "MARGINAL"
    return "rgba(239,68,68,0.12)", "#ef4444", "KRITISK"


@error_boundary
def render_overview(project: dict | None, sb):
    if not project:
        st.info("Inget aktivt projekt. Gå till DTSM Portfolio och öppna ett projekt.")
        return

    project_id = project["id"]
    cur        = project.get("current_phase", 1)
    health     = project.get("health_score", 0)
    used       = project.get("token_used", 0)
    budget     = project.get("token_budget", 20)
    pct        = used / budget * 100 if budget > 0 else 0
    deploy     = project.get("deployment_mode", "cloud")
    h_bg, h_color, h_label = _health_color(health)

    # ── SEKTION 1 — Projekthuvud ──────────────────────────────────────────────
    col_info, col_talk, col_analyze = st.columns([3, 1, 1])

    with col_info:
        st.markdown(
            f'<div style="font-size:22px;font-weight:700;color:#e8e8f0;margin-bottom:4px;">'
            f'{project.get("name","—")}</div>'
            f'<div style="font-size:12px;color:#9090a8;margin-bottom:6px;">'
            f'{project.get("client","—")} &nbsp;·&nbsp; Fas {cur}/7 · {PHASES[cur-1] if 0 < cur <= 7 else "—"}'
            f'</div>'
            f'<div style="display:flex;gap:6px;flex-wrap:wrap;">'
            f'<span style="font-size:10px;font-family:monospace;font-weight:600;'
            f'background:{h_bg};color:{h_color};border-radius:4px;padding:2px 8px;">'
            f'● {health}/100 {h_label}</span>'
            f'<span style="font-size:10px;font-family:monospace;'
            f'background:rgba(99,102,241,0.1);color:#6366f1;border-radius:4px;padding:2px 8px;">'
            f'{used:.2f}/{budget:.0f} USD ({pct:.0f}%)</span>'
            f'<span style="font-size:10px;font-family:monospace;'
            f'background:rgba(255,255,255,0.05);color:#9090a8;border-radius:4px;padding:2px 8px;">'
            f'{deploy}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

    with col_talk:
        if st.button("💬 Tala med Architetto", type="primary", use_container_width=True):
            st.session_state["active_agent"]  = "Architetto"
            st.session_state["active_view"]   = "chat"
            st.rerun()

    with col_analyze:
        run_analysis = st.button("🔍 Analysera projektet", use_container_width=True)

    st.markdown("---")

    # ── SEKTION 2 — Fas-kontroll ──────────────────────────────────────────────
    st.markdown(
        '<div style="font-size:10px;font-family:monospace;color:#5a5a72;'
        'letter-spacing:1px;margin-bottom:8px;">PROJEKTFASER — klicka för att ändra</div>',
        unsafe_allow_html=True,
    )
    phase_cols = st.columns(7)
    for i, (col, phase) in enumerate(zip(phase_cols, PHASES), 1):
        with col:
            if i < cur:
                if st.button(f"✅ {phase}", key=f"ph_{i}", use_container_width=True):
                    _update_phase(sb, project_id, i)
            elif i == cur:
                st.button(f"▶ {phase}", key=f"ph_{i}", type="primary",
                          use_container_width=True, disabled=False)
            else:
                if st.button(phase, key=f"ph_{i}", use_container_width=True):
                    _update_phase(sb, project_id, i)

    st.markdown("---")

    # ── SEKTION 3 — Projektanalys ─────────────────────────────────────────────
    if run_analysis:
        tasks        = get_tasks(sb, project_id)
        token_data   = get_token_summary(sb, project_id)
        done_tasks   = [t for t in tasks if t["status"] == "done"]
        open_tasks   = [t for t in tasks if t["status"] != "done"]
        blocking     = [t for t in tasks if t.get("blocks_delivery")]

        prompt = (
            f"Analysera detta projekt och ge en konkret statusrapport med nästa steg:\n\n"
            f"Projekt: {project.get('name','—')} | Kund: {project.get('client','—')}\n"
            f"Fas: {cur}/7 — {PHASES[cur-1] if 0 < cur <= 7 else '—'}\n"
            f"Uppgifter klara: {len(done_tasks)}/{len(tasks)}\n"
            f"Blockerare: {len(blocking)} st\n"
            f"Token-budget: {used:.2f}/{budget} USD\n\n"
            f"Öppna uppgifter: {[t['title'] for t in open_tasks[:5]]}\n"
            f"Blockerare: {[t['title'] for t in blocking]}\n\n"
            f"Ge:\n"
            f"1. En kort statusbedömning (2 meningar)\n"
            f"2. Tre konkreta nästa steg\n"
            f"3. En risk du ser\n"
            f"4. Rekommendation för nästa fas"
        )

        with st.spinner("Architetto analyserar projektet…"):
            reply, tokens, cost = route_message(
                "Architetto",
                [{"role": "user", "content": prompt}],
                project_context=build_project_context(project),
                max_tokens=600,
            )

        st.success(f"**🏛️ Architetto — Projektanalys**\n\n{reply}")
        save_message(sb, project_id, "assistant", reply,
                     agent="Architetto", model=AGENTS["Architetto"]["model"],
                     tokens=tokens, cost=cost)
        log_tokens(sb, project_id, "Architetto", AGENTS["Architetto"]["model"],
                   tokens // 2, tokens - tokens // 2, cost)

    # ── SEKTION 4 — Fas-specifika snabbknappar ────────────────────────────────
    actions = PHASE_ACTIONS.get(cur, [])
    if actions:
        st.markdown(
            f'<div style="font-size:10px;font-family:monospace;color:#5a5a72;'
            f'letter-spacing:1px;margin-bottom:8px;">SNABBÅTGÄRDER — Fas {cur}: {PHASES[cur-1]}</div>',
            unsafe_allow_html=True,
        )
        action_cols = st.columns(len(actions))
        for col, (label, agent_prompt) in zip(action_cols, actions):
            with col:
                if st.button(label, use_container_width=True, key=f"action_{label}"):
                    if agent_prompt:
                        with st.spinner(f"Rådet arbetar…"):
                            reply, tokens, cost = route_message(
                                "Architetto",
                                [{"role": "user", "content": agent_prompt}],
                                project_context=build_project_context(project),
                                max_tokens=800,
                            )
                        st.info(f"**Architetto:** {reply}")
                        save_message(sb, project_id, "assistant", reply,
                                     agent="Architetto",
                                     model=AGENTS["Architetto"]["model"],
                                     tokens=tokens, cost=cost)
                        log_tokens(sb, project_id, "Architetto",
                                   AGENTS["Architetto"]["model"],
                                   tokens // 2, tokens - tokens // 2, cost)

    st.markdown("---")

    # ── Uppgifter + Token-förbrukning ─────────────────────────────────────────
    tasks        = get_tasks(sb, project_id)
    token_summary = get_token_summary(sb, project_id)
    done_count   = sum(1 for t in tasks if t["status"] == "done")

    col_a, col_b = st.columns(2)

    with col_a:
        st.markdown(
            f'<div style="font-size:10px;font-family:monospace;color:#5a5a72;'
            f'letter-spacing:1px;margin-bottom:8px;">'
            f'UPPGIFTER ({done_count}/{len(tasks)} klara)</div>',
            unsafe_allow_html=True,
        )
        recent = sorted(tasks, key=lambda x: x.get("created_at",""), reverse=True)[:6]
        if not recent:
            st.markdown('<div style="color:#5a5a72;font-size:12px;">Inga uppgifter ännu.</div>',
                        unsafe_allow_html=True)
        for task in recent:
            status = task.get("status", "todo")
            dot = (
                '<span class="status-dot active"></span>' if status == "done" else
                '<span class="status-dot busy"></span>'  if status == "in_progress" else
                '<span class="status-dot red"></span>'   if task.get("blocks_delivery") else
                '<span class="status-dot idle"></span>'
            )
            owner = task.get("owner_agent", "—")
            title = task["title"].replace("<", "&lt;")
            st.markdown(
                f'<div class="studio-card" style="padding:10px 14px;margin-bottom:6px;">'
                f'{dot}<span style="font-size:12px;color:#e8e8f0;">{title}</span>'
                f'<span style="float:right;font-size:10px;font-family:monospace;'
                f'color:#5a5a72;">{owner}</span></div>',
                unsafe_allow_html=True,
            )

    with col_b:
        st.markdown(
            '<div style="font-size:10px;font-family:monospace;color:#5a5a72;'
            'letter-spacing:1px;margin-bottom:8px;">TOKEN-FÖRBRUKNING PER AGENT</div>',
            unsafe_allow_html=True,
        )
        if not token_summary:
            st.markdown('<div style="color:#5a5a72;font-size:12px;">Ingen tokenanvändning ännu.</div>',
                        unsafe_allow_html=True)
        for row in token_summary[:6]:
            pct_bar = min(row["cost"] / max(used, 0.001) * 100, 100)
            st.markdown(
                f'<div style="margin-bottom:8px;">'
                f'<div style="display:flex;justify-content:space-between;'
                f'font-size:11px;margin-bottom:3px;">'
                f'<span style="font-family:monospace;color:#AFA9EC;">{row["agent"]}</span>'
                f'<span style="color:#5a5a72;">{row["tokens"]:,} tok · {row["cost"]:.4f} USD</span>'
                f'</div>'
                f'<div style="background:#1a1d27;border-radius:4px;height:4px;">'
                f'<div style="width:{pct_bar:.0f}%;height:100%;border-radius:4px;'
                f'background:linear-gradient(90deg,#7F77DD,#1D9E75);"></div>'
                f'</div></div>',
                unsafe_allow_html=True,
            )

    st.markdown("---")

    # ── SEKTION 5 — Projektinställningar ─────────────────────────────────────
    with st.expander("⚙️ Projektinställningar"):
        with st.form("project_settings"):
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                new_name   = st.text_input("Projektnamn", value=project.get("name", ""))
                new_client = st.text_input("Kund", value=project.get("client", ""))
                new_budget = st.number_input("Token-budget (USD)",
                                             value=float(project.get("token_budget", 20.0)),
                                             step=5.0, min_value=1.0)
            with col_s2:
                new_health = st.slider("Health Score", 0, 100,
                                       value=int(project.get("health_score", 75)))
                deploy_opts = ["cloud", "hybrid", "airgap"]
                cur_deploy  = project.get("deployment_mode", "cloud")
                new_deploy  = st.selectbox("Deployment", deploy_opts,
                                           index=deploy_opts.index(cur_deploy)
                                           if cur_deploy in deploy_opts else 0)
                import datetime
                raw_deadline = project.get("deadline")
                default_dl   = (datetime.date.fromisoformat(raw_deadline[:10])
                                if raw_deadline else datetime.date.today())
                new_deadline = st.date_input("Deadline", value=default_dl)

            if st.form_submit_button("💾 Spara ändringar", type="primary"):
                sb.table("projects").update({
                    "name":            new_name,
                    "client":          new_client,
                    "token_budget":    new_budget,
                    "health_score":    new_health,
                    "deployment_mode": new_deploy,
                    "deadline":        str(new_deadline),
                }).eq("id", project_id).execute()
                st.success("Projekt uppdaterat!")
                st.rerun()
