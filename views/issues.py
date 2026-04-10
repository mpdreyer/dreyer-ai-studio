import json
import streamlit as st
from datetime import datetime
from agents.router import route_message
from core.errors import error_boundary

TYPE_CONFIG = {
    "bug":         ("🐛", "Bugg",        "#FCEBEB", "#A32D2D"),
    "improvement": ("✨", "Förbättring", "#EEEDFE", "#3C3489"),
    "feature":     ("🚀", "Ny funktion", "#E1F5EE", "#085041"),
}

PRIORITY_CONFIG = {
    "critical": ("🔴", "Kritisk"),
    "high":     ("🟠", "Hög"),
    "medium":   ("🟡", "Medium"),
    "low":      ("🟢", "Låg"),
}

STATUS_CONFIG = {
    "open":        ("⭕", "Öppen"),
    "in_progress": ("🔄", "Pågår"),
    "done":        ("✅", "Klar"),
    "wont_fix":    ("🚫", "Fixas ej"),
}

DTSM_APPS = [
    "Dreyer AI Studio", "Dreyer Council", "DiscCaddy",
    "24-hour-race-helper", "F1 Analytics", "Receptsamlingen",
]

AGENT_EXPERTISE = {
    "Codex": {
        "icon": "💻",
        "focus": "Rotorsak och fix med kodexempel",
        "prompt_template": (
            "Du är Codex, Lead Developer.\n"
            "Analysera buggen och ge en konkret fix:\n\n"
            "App: {app_name}\nProblem: {title}\n"
            "Beskrivning: {description}\nSteg: {steps}\n"
            "Faktiskt: {actual}\nFörväntat: {expected}\n\n"
            "Ge:\n1. Trolig rotorsak (1-2 meningar)\n"
            "2. Konkret fix med kodexempel\n3. Verifieringssteg"
        ),
    },
    "Diavolo": {
        "icon": "🔴",
        "focus": "Säkerhetsimplikationer av buggen",
        "prompt_template": (
            "Du är Diavolo, Red Team.\n"
            "Analysera säkerhetsaspekterna av denna bugg:\n\n"
            "App: {app_name}\nProblem: {title}\n"
            "Beskrivning: {description}\n\n"
            "Är detta en säkerhetsrisk? Kan buggen utnyttjas?\n"
            "Severity: HÖG/MEDIUM/LÅG — motivera.\nÅtgärdsrekommendation."
        ),
    },
    "Logica": {
        "icon": "🧪",
        "focus": "Testfall och edge cases",
        "prompt_template": (
            "Du är Logica, QA-ansvarig.\n"
            "Analysera denna bugg och designa testfall:\n\n"
            "App: {app_name}\nProblem: {title}\n"
            "Steg: {steps}\nFaktiskt: {actual}\nFörväntat: {expected}\n\n"
            "Ge:\n1. Vad missades i testningen?\n"
            "2. 3 testfall som skulle ha fångat buggen\n"
            "3. Edge cases att testa efter fix"
        ),
    },
    "Datatjej": {
        "icon": "🗄️",
        "focus": "Data- och integrationsproblem",
        "prompt_template": (
            "Du är Datatjej, Data & Integration.\n"
            "Analysera om buggen beror på data- eller integrationsproblem:\n\n"
            "App: {app_name}\nProblem: {title}\n"
            "Beskrivning: {description}\n\n"
            "Är det ett problem med:\n- Dataformat eller schema?\n"
            "- API-anrop eller respons?\n- Supabase-integration?\n"
            "- Validering av indata?\nKonkret åtgärdsförslag."
        ),
    },
    "Guardiano": {
        "icon": "🛡️",
        "focus": "GDPR och compliance-aspekter",
        "prompt_template": (
            "Du är Guardiano, AI Safety & Ethics.\n"
            "Analysera compliance-aspekterna av denna bugg:\n\n"
            "App: {app_name}\nProblem: {title}\n"
            "Beskrivning: {description}\n\n"
            "Påverkar buggen:\n- Persondata eller GDPR?\n"
            "- Datalagring eller loggning?\n- Användarintegritet?\n"
            "Severity och rekommendation."
        ),
    },
    "Architetto": {
        "icon": "🏛️",
        "focus": "Arkitekturproblem och långsiktig lösning",
        "prompt_template": (
            "Du är Architetto, Chief Architect.\n"
            "Analysera om buggen beror på arkitekturella problem:\n\n"
            "App: {app_name}\nProblem: {title}\n"
            "Beskrivning: {description}\n\n"
            "Är detta ett symptom på ett djupare arkitekturproblem?\n"
            "Föreslå en hållbar lösning som förhindrar liknande buggar."
        ),
    },
    "Risico": {
        "icon": "⚠️",
        "focus": "Affärsrisk och kundpåverkan",
        "prompt_template": (
            "Du är Risico, Risk & Critique.\n"
            "Analysera affärsrisken med denna bugg:\n\n"
            "App: {app_name}\nProblem: {title}\n"
            "Beskrivning: {description}\nPrioritet: {priority}\n\n"
            "Vad är kundpåverkan?\nHur akut är åtgärden?\n"
            "Ska leverans blockeras?"
        ),
    },
}


def _parse_log(fix_notes: str | None) -> list:
    if not fix_notes:
        return []
    try:
        log = json.loads(fix_notes)
        if isinstance(log, list):
            return log
        return [{"agent": "Codex", "text": fix_notes, "date": ""}]
    except Exception:
        return [{"agent": "Codex", "text": fix_notes, "date": ""}]


def _render_agent_panel(issue: dict, sb):
    issue_id = issue["id"]
    with st.expander("🤖 Fråga rådet om denna bugg", expanded=False):

        # Agent-väljarrad
        agent_cols = st.columns(len(AGENT_EXPERTISE))
        selected = st.session_state.get(f"agent_{issue_id}", "Codex")

        for col, (agent_name, cfg) in zip(agent_cols, AGENT_EXPERTISE.items()):
            with col:
                if st.button(
                    f"{cfg['icon']} {agent_name}",
                    key=f"sel_{agent_name}_{issue_id}",
                    use_container_width=True,
                    type="primary" if selected == agent_name else "secondary",
                    help=cfg["focus"],
                ):
                    st.session_state[f"agent_{issue_id}"] = agent_name
                    st.rerun()

        cfg = AGENT_EXPERTISE[selected]
        st.caption(f"**{cfg['icon']} {selected}:** {cfg['focus']}")

        if st.button(
            f"Kör analys med {selected}",
            key=f"run_{issue_id}",
            type="primary",
            use_container_width=True,
        ):
            prompt = cfg["prompt_template"].format(
                app_name=issue.get("app_name", ""),
                title=issue.get("title", ""),
                description=issue.get("description", ""),
                steps=issue.get("steps_to_reproduce", ""),
                actual=issue.get("actual_behavior", ""),
                expected=issue.get("expected_behavior", ""),
                priority=issue.get("priority", ""),
            )
            with st.spinner(f"{selected} analyserar..."):
                reply, _, _ = route_message(
                    selected,
                    [{"role": "user", "content": prompt}],
                    max_tokens=700,
                )
            log = _parse_log(issue.get("fix_notes"))
            log.append({
                "agent": selected,
                "text":  reply,
                "date":  datetime.now().isoformat()[:16],
            })
            sb.table("issues").update({
                "fix_notes":   json.dumps(log, ensure_ascii=False),
                "assigned_to": selected,
                "updated_at":  "now()",
            }).eq("id", issue_id).execute()
            st.markdown(f"**{cfg['icon']} {selected}:**")
            st.info(reply)

        # Tidigare analyser
        log = _parse_log(issue.get("fix_notes"))
        if log:
            st.markdown("**Tidigare analyser:**")
            for entry in reversed(log[-3:]):
                agent = entry.get("agent", "?")
                text  = entry.get("text", "")
                date  = entry.get("date", "")
                icon  = AGENT_EXPERTISE.get(agent, {}).get("icon", "🤖")
                with st.expander(f"{icon} {agent} · {date}", expanded=False):
                    st.markdown(text)


@error_boundary
def render_issues(project, sb):
    st.subheader("🐛 Buggar & Förbättringar")
    st.caption("Spåra buggar och förbättringsförslag per app och projekt")

    # ── Snabb-rapport ────────────────────────────────────────────────────────
    with st.expander("➕ Rapportera bugg eller förbättring", expanded=False):
        with st.form("new_issue_form"):
            col1, col2 = st.columns(2)
            with col1:
                title = st.text_input(
                    "Titel *", placeholder="Kort beskrivning av problemet")
                default_app = (
                    project["name"]
                    if project and project.get("name") in DTSM_APPS
                    else "Dreyer AI Studio"
                )
                app_name = st.selectbox(
                    "App", DTSM_APPS, index=DTSM_APPS.index(default_app))
                issue_type = st.selectbox(
                    "Typ", ["bug", "improvement", "feature"],
                    format_func=lambda x:
                        f"{TYPE_CONFIG[x][0]} {TYPE_CONFIG[x][1]}")
            with col2:
                priority = st.selectbox(
                    "Prioritet", ["critical", "high", "medium", "low"],
                    index=1,
                    format_func=lambda x:
                        f"{PRIORITY_CONFIG[x][0]} {PRIORITY_CONFIG[x][1]}")
                assigned = st.selectbox(
                    "Tilldela agent",
                    ["Codex", "Architetto", "Logica",
                     "Datatjej", "Guardiano", "—"])
                description = st.text_area("Beskrivning", height=80)

            steps = actual = expected = ""
            if issue_type == "bug":
                steps = st.text_area(
                    "Steg att återskapa felet", height=60,
                    placeholder="1. Gör X\n2. Klicka Y\n3. Ser Z")
                col_a, col_b = st.columns(2)
                with col_a:
                    actual = st.text_area("Vad händer?", height=60)
                with col_b:
                    expected = st.text_area("Vad borde hända?", height=60)

            if st.form_submit_button("Rapportera", type="primary") and title:
                sb.table("issues").insert({
                    "app_name":           app_name,
                    "project_id":         project["id"] if project else None,
                    "title":              title,
                    "description":        description,
                    "type":               issue_type,
                    "priority":           priority,
                    "assigned_to":        assigned if assigned != "—" else None,
                    "steps_to_reproduce": steps,
                    "actual_behavior":    actual,
                    "expected_behavior":  expected,
                }).execute()
                st.success(f"'{title}' rapporterad!")
                st.rerun()

    st.divider()

    # ── Filter ───────────────────────────────────────────────────────────────
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        filter_app = st.selectbox(
            "App", ["Alla"] + DTSM_APPS, label_visibility="collapsed")
    with col2:
        filter_type = st.selectbox(
            "Typ", ["Alla typer", "bug", "improvement", "feature"],
            label_visibility="collapsed",
            format_func=lambda x: "Alla typer" if x == "Alla typer"
                else f"{TYPE_CONFIG[x][0]} {TYPE_CONFIG[x][1]}")
    with col3:
        filter_status = st.selectbox(
            "Status", ["Öppna", "Pågår", "Klara", "Alla"],
            label_visibility="collapsed")
    with col4:
        filter_priority = st.selectbox(
            "Prioritet", ["Alla", "critical", "high", "medium", "low"],
            label_visibility="collapsed",
            format_func=lambda x: "Alla" if x == "Alla"
                else f"{PRIORITY_CONFIG[x][0]} {PRIORITY_CONFIG[x][1]}")

    # ── Hämta issues ─────────────────────────────────────────────────────────
    query = sb.table("issues").select("*").order("created_at", desc=True)
    if filter_app != "Alla":
        query = query.eq("app_name", filter_app)
    if filter_type != "Alla typer":
        query = query.eq("type", filter_type)
    if filter_status == "Öppna":
        query = query.eq("status", "open")
    elif filter_status == "Pågår":
        query = query.eq("status", "in_progress")
    elif filter_status == "Klara":
        query = query.eq("status", "done")
    if filter_priority != "Alla":
        query = query.eq("priority", filter_priority)

    issues = query.execute().data or []

    # ── Metrics ──────────────────────────────────────────────────────────────
    all_issues = (
        sb.table("issues").select("type,status,priority").execute().data or []
    )
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Totalt", len(all_issues))
    c2.metric("🐛 Buggar",
              sum(1 for i in all_issues if i["type"] == "bug"))
    c3.metric("⭕ Öppna",
              sum(1 for i in all_issues if i["status"] == "open"))
    c4.metric("🔴 Kritiska",
              sum(1 for i in all_issues if i["priority"] == "critical"))

    st.divider()

    if not issues:
        st.info("Inga issues matchar filtret. 🎉")
        return

    # ── Lista issues ─────────────────────────────────────────────────────────
    for issue in issues:
        type_cfg = TYPE_CONFIG.get(issue["type"], ("❓", "Okänd", "#eee", "#333"))
        prio_cfg = PRIORITY_CONFIG.get(issue["priority"], ("⚪", "Okänd"))

        with st.container(border=True):

            # Övre rad — info + status
            col1, col2 = st.columns([6, 1])

            with col1:
                st.markdown(
                    f'<span style="background:{type_cfg[2]};color:{type_cfg[3]};'
                    f'padding:2px 8px;border-radius:4px;font-size:11px;'
                    f'font-family:monospace">{type_cfg[0]} {type_cfg[1]}</span> '
                    f'<span style="font-size:11px;color:#888">'
                    f'{prio_cfg[0]} {prio_cfg[1]} · {issue["app_name"]} · '
                    f'{issue["created_at"][:10]}</span>',
                    unsafe_allow_html=True,
                )
                st.markdown(f"**{issue['title']}**")
                if issue.get("description"):
                    st.caption(issue["description"])
                if issue.get("assigned_to"):
                    st.caption(f"👤 {issue['assigned_to']}")

            with col2:
                statuses = ["open", "in_progress", "done", "wont_fix"]
                new_status = st.selectbox(
                    "Status",
                    statuses,
                    index=statuses.index(issue.get("status", "open")),
                    key=f"status_{issue['id']}",
                    label_visibility="collapsed",
                    format_func=lambda x:
                        f"{STATUS_CONFIG[x][0]} {STATUS_CONFIG[x][1]}",
                )
                if new_status != issue.get("status"):
                    sb.table("issues").update({
                        "status":     new_status,
                        "updated_at": "now()",
                    }).eq("id", issue["id"]).execute()
                    st.rerun()

            # Agent-panel i full bredd
            _render_agent_panel(issue, sb)
