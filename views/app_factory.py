"""
Dreyer AI Studio — App Factory
Starta, planera och bygg nya AI-appar direkt från Studio.
"""

import streamlit as st


# ── Promptbibliotek ───────────────────────────────────────────────────────────

PROMPTS = [
    {
        "id": "cc_setup",
        "title": "Setup nytt Streamlit-projekt",
        "system": "Claude Code",
        "color": "#6366f1",
        "description": "Skapar komplett projektstruktur med secrets och beroenden.",
        "text": """Skapa ett nytt Streamlit-projekt med denna struktur:
├── app.py
├── requirements.txt
├── .gitignore
├── .streamlit/
│   ├── secrets.toml
│   └── secrets.toml.example
├── components/
├── views/
├── db/
└── assets/

Installera: streamlit anthropic supabase python-dotenv
Konfigurera secrets från ~/dreyer-council/.env
Skapa ett demo-projekt och verifiera att appen startar på localhost:8501.""",
    },
    {
        "id": "cc_importerror",
        "title": "Fixa ImportError",
        "system": "Claude Code",
        "color": "#6366f1",
        "description": "Analyserar och rättar import-fel automatiskt.",
        "text": """Jag får detta fel i min Streamlit-app:
[KLISTRA IN FELMEDDELANDE]

Analysera felet, hitta orsaken och fixa det.
Kontrollera imports, installera saknade paket med pip,
uppdatera berörda filer och verifiera att appen startar utan fel.""",
    },
    {
        "id": "cc_new_view",
        "title": "Lägg till ny vy",
        "system": "Claude Code",
        "color": "#6366f1",
        "description": "Skapar ny vy och registrerar den i app.py.",
        "text": """Lägg till en ny vy i ~/[APP-NAMN]/
Vynamn: [NAMN]
Funktionalitet: [BESKRIV]

Skapa views/[namn].py med en render_[namn](project, sb)-funktion.
Registrera vyn i components/sidebar.py VIEWS-dict.
Lägg till elif-block i app.py.
Följ samma mönster som befintliga vyer.""",
    },
    {
        "id": "cc_push",
        "title": "Pusha till GitHub",
        "system": "Claude Code",
        "color": "#6366f1",
        "description": "Commitar och pushar med säkerhetskontroll.",
        "text": """Pusha ~/[APP-NAMN] till GitHub.
1. Kontrollera att .gitignore exkluderar secrets.toml och .env
2. Kör: git status för att se ändringar
3. git add . && git commit -m "[MEDDELANDE]"
4. git push
Fixa eventuella konflikter automatiskt.
Rapportera URL till repot när pushen är klar.""",
    },
    {
        "id": "cc_deploy",
        "title": "Deploy till Streamlit Cloud",
        "system": "Claude Code",
        "color": "#6366f1",
        "description": "Förbereder och validerar för Streamlit Cloud.",
        "text": """Förbered ~/[APP-NAMN] för Streamlit Cloud.
1. Kontrollera att requirements.txt är komplett (kör pip freeze > requirements.txt om osäkert)
2. Verifiera att inga hardkodade API-nycklar finns i källkoden
3. Kontrollera att .streamlit/secrets.toml.example är uppdaterad
4. Generera en lista med alla secrets som behöver konfigureras på share.streamlit.io
5. Pusha till GitHub om inte redan gjort""",
    },
    {
        "id": "cc_supabase_table",
        "title": "Lägg till Supabase-tabell",
        "system": "Claude Code",
        "color": "#6366f1",
        "description": "Genererar SQL och CRUD-funktioner för ny tabell.",
        "text": """Lägg till en ny tabell i Supabase för ~/[APP-NAMN].
Tabellnamn: [NAMN]
Kolumner: [BESKRIV - t.ex. id uuid pk, name text, created_at timestamptz]

1. Generera CREATE TABLE SQL med IF NOT EXISTS
2. Kör mot Supabase via Supabase MCP eller curl med SUPABASE_KEY från .streamlit/secrets.toml
3. Lägg till get_[namn](), save_[namn](), update_[namn]()-funktioner i db/supabase_client.py
4. Verifiera att tabellen skapades korrekt""",
    },
    {
        "id": "nlm_sync",
        "title": "Synka projektdokumentation",
        "system": "NotebookLM",
        "color": "#10b981",
        "description": "Skapar notebook och lägger till projektkällor.",
        "text": """Skapa notebook "[APP-NAMN] · Dokumentation" i NotebookLM.
Lägg till dessa källor:
- README.md (notebook_add_text)
- Arkitekturdiagram och filstruktur (notebook_add_text)
- API-dokumentation (notebook_add_text)
- db/schema.sql (notebook_add_text)

Generera sedan en Briefing Doc på svenska som sammanfattar:
projektsyfte, teknisk arkitektur, databas-design och nästa steg.""",
    },
    {
        "id": "nlm_audio",
        "title": "Generera Audio Overview",
        "system": "NotebookLM",
        "color": "#10b981",
        "description": "Skapar Audio Overview för projektet.",
        "text": """Generera Audio Overview för notebook [NOTEBOOK-ID].
Innehåll som ska täckas:
- Projektets syfte och affärsvärde
- Teknisk arkitektur och val
- Nuvarande status och färdiga features
- Nästa steg och öppna frågor
Språk: svenska. Ton: professionell men tillgänglig.""",
    },
    {
        "id": "gh_create_repo",
        "title": "Skapa nytt GitHub-repo",
        "system": "GitHub",
        "color": "#f1f5f9",
        "description": "Initierar repo och pushar första commit.",
        "text": """gh repo create mpdreyer/[APP-NAMN] --public --source=. --push

Om gh CLI inte är installerat:
  brew install gh
  gh auth login

Alternativt — skapa repot via GitHub.com och kör sedan:
  git remote add origin git@github.com:mpdreyer/[APP-NAMN].git
  git push -u origin main""",
    },
    {
        "id": "gh_ci",
        "title": "Skapa GitHub Actions CI",
        "system": "GitHub",
        "color": "#f1f5f9",
        "description": "Sätter upp CI-pipeline med syntax-validering.",
        "text": """Skapa .github/workflows/ci.yml för [APP-NAMN].
Pipeline ska köra på push till main och pull requests:
1. pip install -r requirements.txt
2. python -m py_compile app.py (syntax-check)
3. Kontrollera att inga secrets är hårdkodade (grep-scan)

Skapa filen, committa och pusha.""",
    },
    {
        "id": "sb_schema",
        "title": "Kör schema.sql mot Supabase",
        "system": "Supabase",
        "color": "#f59e0b",
        "description": "Läser och exekverar schema mot databasen.",
        "text": """Läs db/schema.sql och kör det mot Supabase:

SUPABASE_KEY=$(grep SUPABASE_KEY ~/[APP-NAMN]/.streamlit/secrets.toml | cut -d'"' -f2)

Försök köra via Supabase MCP (execute_sql).
Om det misslyckas — visa SQL-innehållet så jag kan klistra in det
manuellt i Supabase SQL Editor på supabase.com.

Verifiera att alla tabeller skapades korrekt efteråt.""",
    },
    {
        "id": "sb_backup",
        "title": "Backup Supabase-data",
        "system": "Supabase",
        "color": "#f59e0b",
        "description": "Exporterar alla tabeller till JSON-filer.",
        "text": """Exportera alla tabeller från Supabase till ~/[APP-NAMN]/backup/
Tabeller att exportera: [LISTA TABELLER]

Använd Supabase REST API:
SUPABASE_KEY=$(grep SUPABASE_KEY .streamlit/secrets.toml | cut -d'"' -f2)
SUPABASE_URL=$(grep SUPABASE_URL .streamlit/secrets.toml | cut -d'"' -f2)

curl "$SUPABASE_URL/rest/v1/[TABELL]?select=*" \\
  -H "apikey: $SUPABASE_KEY" \\
  -H "Authorization: Bearer $SUPABASE_KEY" > backup/[TABELL].json

Skapa backup/-mappen om den inte finns. Rapportera filstorlekar.""",
    },
]

SYSTEM_COLORS = {
    "Claude Code": "#6366f1",
    "NotebookLM":  "#10b981",
    "GitHub":      "#f1f5f9",
    "Supabase":    "#f59e0b",
}

# ── Befintliga appar ──────────────────────────────────────────────────────────

APPS = [
    {
        "emoji": "🏛️",
        "name": "Dreyer AI Studio",
        "repo": "mpdreyer/dreyer-ai-studio",
        "url": "https://github.com/mpdreyer/dreyer-ai-studio",
        "app_url": None,
        "stack": ["Streamlit", "Claude API", "Supabase"],
        "status": "live",
        "status_label": "Live · Fas 1",
    },
    {
        "emoji": "🏎️",
        "name": "Dreyer Council",
        "repo": "mpdreyer/dreyer-council",
        "url": "https://github.com/mpdreyer/dreyer-council",
        "app_url": None,
        "stack": ["Streamlit", "Multi-LLM"],
        "status": "live",
        "status_label": "Live",
    },
    {
        "emoji": "🥏",
        "name": "DiscCaddy",
        "repo": "mpdreyer/DiscCaddy",
        "url": "https://github.com/mpdreyer/DiscCaddy",
        "app_url": None,
        "stack": ["Streamlit", "Supabase", "GPT-4o"],
        "status": "wip",
        "status_label": "Kamera-funktion ej klar",
    },
    {
        "emoji": "⛵",
        "name": "Scuderia del Mare",
        "repo": "mpdreyer/24-hour-race-helper",
        "url": "https://github.com/mpdreyer/24-hour-race-helper",
        "app_url": None,
        "stack": ["React", "TypeScript", "Claude API"],
        "status": "live",
        "status_label": "Live · iOS-app",
    },
]

# ── Snabbstart-mallar ─────────────────────────────────────────────────────────

TEMPLATES = [
    {
        "id": "standard",
        "icon": "🚀",
        "name": "Streamlit + Claude + Supabase",
        "subtitle": "Standard AI-app · Produktionsklar",
        "description": "Komplett mall för en produktionsklar AI-app med Streamlit-frontend, Claude API-integration och Supabase-databas. Inkluderar autentisering, multi-vy-navigation och token-tracking.",
        "stack": ["Streamlit ≥1.35", "anthropic ≥0.28", "supabase ≥2.4", "pandas"],
        "setup_time": "5 minuter med Claude Code",
        "prompt": """Sätt upp ett nytt Streamlit-projekt med namn [APP-NAMN].
Använd denna struktur:
├── app.py                    # Huvud-app, set_page_config, routing
├── requirements.txt          # streamlit anthropic supabase pandas
├── .gitignore                # secrets.toml, .env, __pycache__
├── .streamlit/
│   ├── secrets.toml          # ANTHROPIC_API_KEY, SUPABASE_URL, SUPABASE_KEY
│   └── secrets.toml.example
├── components/
│   ├── __init__.py
│   ├── sidebar.py            # Navigation
│   └── topbar.py             # Header med projektinfo
├── views/
│   ├── __init__.py
│   └── overview.py           # Startvy
├── db/
│   ├── __init__.py
│   ├── schema.sql
│   └── supabase_client.py    # get_supabase(), CRUD-funktioner
└── assets/
    └── style.css             # Mörkt tema

Kopiera API-nycklar från ~/dreyer-council/.env
Kör schema.sql mot Supabase via MCP.
Starta appen och verifiera localhost:8501.""",
    },
    {
        "id": "airgap",
        "icon": "🔒",
        "name": "Air-gapped AI-app",
        "subtitle": "Känsliga kunder · Ingen extern API-trafik",
        "description": "Samma struktur som standard men med Ollama för lokal LLM-inferens. Ingen data lämnar kundens nätverk. Inkluderar deployment-guide för on-premise installation.",
        "stack": ["Streamlit", "Ollama (local)", "Supabase (self-hosted)"],
        "setup_time": "15 minuter inkl. Ollama-install",
        "prompt": """Sätt upp en air-gapped AI-app med namn [APP-NAMN].
Samma struktur som standard men:
- Byt ut anthropic-paketet mot ollama (pip install ollama)
- Konfigurera OLLAMA_HOST i secrets.toml (default: http://localhost:11434)
- Standardmodell: llama3.2 (byt med OLLAMA_MODEL i secrets)
- Ingen extern nätverkstrafik — verifiera med lsof

Installation av Ollama (om ej gjort):
  brew install ollama
  ollama serve &
  ollama pull llama3.2

Skapa en router.py som wrappar ollama.chat() med samma API som anthropic.
Starta och verifiera att chat fungerar utan internet.""",
    },
    {
        "id": "swarm",
        "icon": "🐝",
        "name": "Ruflo-svärm-app",
        "subtitle": "Eval-fokus · Parallell testning",
        "description": "App-mall för prompt-evaluering med Ruflo-svärm. Kör upp till 90 parallella worker-agenter och aggregerar resultat i Supabase. Inkluderar swarm.py, dashboard och Supabase-schema.",
        "stack": ["Streamlit", "Claude API", "Supabase", "asyncio"],
        "setup_time": "10 minuter med Claude Code",
        "prompt": """Sätt upp en Ruflo-svärm-app med namn [APP-NAMN].
Utöka standard-strukturen med:
├── views/
│   ├── swarm.py              # render_swarm(project, sb)
│   └── dashboard.py          # Svärm-resultat och statistik

Supabase-tabeller att skapa:
  swarm_runs(id, project_id, variant_id, variant, n_workers, status,
             pass_rate, median_score, p95_latency, decision, created_at)
  worker_results(id, run_id, worker_idx, testcase_id,
                 score, latency_ms, passed, error, created_at)

Svärm-konfiguration i swarm.py:
- n_workers: 1-90 (slider)
- variant: prompt-text (text_area)
- testcases: JSON-lista
- Kör asynkront med asyncio.gather()
- Visa realtids-progress med st.progress()
- Aggregera: pass_rate, median_score, p95_latency

Starta och verifiera att svärmen kör med 3 workers.""",
    },
]


# ── Hjälpfunktioner ───────────────────────────────────────────────────────────

def _badge(label: str, color: str) -> str:
    return (
        f'<span style="font-family:\'JetBrains Mono\',monospace;font-size:9px;'
        f'font-weight:600;letter-spacing:0.5px;text-transform:uppercase;'
        f'padding:2px 8px;border-radius:3px;border:1px solid {color}40;'
        f'color:{color};background:{color}15;white-space:nowrap;">{label}</span>'
    )


def _copy_prompt(text: str, key: str):
    st.code(text, language="text")
    col_btn, col_msg = st.columns([1, 4])
    with col_btn:
        if st.button("📋 Kopiera", key=f"copy_{key}", use_container_width=True):
            st.session_state[f"copied_{key}"] = True
    with col_msg:
        if st.session_state.get(f"copied_{key}"):
            st.success("✓ Kopierad till kodrutan ovan — välj allt och kopiera (⌘A ⌘C)")


def _section_header(text: str, mono: bool = True):
    font = "'JetBrains Mono',monospace" if mono else "'Inter',sans-serif"
    st.markdown(
        f'<div style="font-family:{font};font-size:10px;font-weight:600;'
        f'letter-spacing:1px;text-transform:uppercase;color:#475569;'
        f'margin:16px 0 8px;">{text}</div>',
        unsafe_allow_html=True,
    )


# ── Flik 1 — Ny app ──────────────────────────────────────────────────────────

def _tab_new_app(project, sb):
    st.markdown(
        '<div style="font-family:\'Inter\',sans-serif;font-size:13px;'
        'color:#94a3b8;margin-bottom:16px;">'
        'Fyll i formuläret nedan. Architetto genererar en strukturerad brief, '
        'filstruktur och feature-lista som du kan ge direkt till Claude Code.</div>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        app_name = st.text_input("App-namn", placeholder="min-ai-app", key="af_name")
        description = st.text_area(
            "Beskrivning", height=100,
            placeholder="Vad ska appen göra? Vilket problem löser den?",
            key="af_description",
        )
        audience = st.text_input("Målgrupp", placeholder="Vem använder appen?", key="af_audience")
    with col2:
        stack = st.multiselect(
            "Tech stack",
            ["Streamlit", "FastAPI", "React", "Claude API",
             "Supabase", "Ruflo-svärm", "NotebookLM", "Ollama"],
            default=["Streamlit", "Claude API", "Supabase"],
            key="af_stack",
        )
        deployment = st.selectbox(
            "Deployment", ["cloud", "hybrid", "airgap"], key="af_deploy"
        )
        timeline = st.selectbox(
            "Tidsestimate",
            ["En helg", "1 vecka", "2–4 veckor"],
            key="af_timeline",
        )

    st.divider()

    generate = st.button(
        "⚡ Generera brief med Architetto",
        type="primary",
        disabled=not (app_name and description),
        key="af_generate",
    )

    if not app_name or not description:
        st.caption("Fyll i App-namn och Beskrivning för att aktivera genereringen.")

    if generate and app_name and description:
        stack_str = ", ".join(stack) if stack else "Streamlit, Claude API"
        prompt_text = (
            f"Ny app-brief:\n\n"
            f"App-namn: {app_name}\n"
            f"Beskrivning: {description}\n"
            f"Målgrupp: {audience or '—'}\n"
            f"Tech stack: {stack_str}\n"
            f"Deployment: {deployment}\n"
            f"Tidsestimate: {timeline}\n\n"
            f"Ge mig:\n"
            f"1. En strukturerad projektbeskrivning (2–3 stycken)\n"
            f"2. Föreslagen filstruktur med kommentarer\n"
            f"3. Prioriterad feature-lista (P0/P1/P2)\n"
            f"4. Kritiska tekniska beslut att ta innan start\n"
            f"5. En färdig Claude Code-prompt för att sätta upp projektet"
        )

        with st.spinner("Architetto analyserar…"):
            try:
                from agents.router import route_message
                from agents.council import AGENTS

                messages = [{"role": "user", "content": prompt_text}]
                content, tokens, cost = route_message("Architetto", messages, max_tokens=2048)

                st.session_state["af_result"] = content
                st.session_state["af_tokens"] = tokens
                st.session_state["af_cost"] = cost

                if project and sb:
                    from db.supabase_client import save_message, log_tokens
                    agent = AGENTS["Architetto"]
                    save_message(sb, project["id"], "user", prompt_text)
                    save_message(
                        sb, project["id"], "assistant", content,
                        agent="Architetto", model=agent["model"],
                        tokens=tokens, cost=cost,
                    )
                    log_tokens(
                        sb, project["id"], "Architetto", agent["model"],
                        tokens // 2, tokens - tokens // 2, cost,
                    )
            except Exception as e:
                st.error(f"Kunde inte nå Architetto: {e}")

    if st.session_state.get("af_result"):
        st.divider()
        tok  = st.session_state.get("af_tokens", 0)
        cost = st.session_state.get("af_cost", 0.0)
        st.markdown(
            f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:10px;'
            f'color:#475569;margin-bottom:8px;">'
            f'ARCHITETTO · {tok:,} TOKENS · {cost:.4f} USD</div>',
            unsafe_allow_html=True,
        )
        st.markdown(st.session_state["af_result"])


# ── Flik 2 — Promptbibliotek ─────────────────────────────────────────────────

def _tab_prompts():
    systems = list(dict.fromkeys(p["system"] for p in PROMPTS))
    filter_system = st.selectbox(
        "Filtrera per system",
        ["Alla"] + systems,
        key="af_filter",
        label_visibility="collapsed",
    )

    search = st.text_input(
        "Sök prompt", placeholder="t.ex. deploy, supabase, import…",
        key="af_search", label_visibility="collapsed",
    )

    filtered = [
        p for p in PROMPTS
        if (filter_system == "Alla" or p["system"] == filter_system)
        and (not search or search.lower() in p["title"].lower() or search.lower() in p["text"].lower())
    ]

    if not filtered:
        st.markdown('<div style="color:#475569;font-size:13px;padding:12px 0;">Inga promtar matchar sökningen.</div>', unsafe_allow_html=True)
        return

    current_system = None
    for p in filtered:
        if p["system"] != current_system:
            current_system = p["system"]
            color = SYSTEM_COLORS.get(current_system, "#94a3b8")
            _section_header(f"── {current_system}")

        with st.expander(f"{p['title']}  ·  {p['description']}", expanded=False):
            st.markdown(
                _badge(p["system"], SYSTEM_COLORS.get(p["system"], "#94a3b8")),
                unsafe_allow_html=True,
            )
            st.markdown("")
            _copy_prompt(p["text"], p["id"])


# ── Flik 3 — Mina appar ──────────────────────────────────────────────────────

def _app_status_badge(status: str, label: str) -> str:
    if status == "live":
        return _badge(f"● {label}", "#10b981")
    elif status == "wip":
        return _badge(f"◐ {label}", "#f59e0b")
    else:
        return _badge(f"○ {label}", "#475569")


def _quick_prompt_for_app(app: dict, action: str) -> str:
    name = app["name"]
    repo = app["repo"]
    if action == "bug":
        return (
            f"Öppna ~/dreyer-ai-studio eller det relevanta projektet och fixa detta bugg i {name}:\n"
            f"[BESKRIV BUGGEN]\n\n"
            f"Repo: github.com/{repo}\n"
            f"1. Läs felmeddelandet\n2. Hitta rotorsaken\n3. Fixa och verifiera"
        )
    elif action == "feature":
        return (
            f"Lägg till denna feature i {name}:\n"
            f"[BESKRIV FEATURE]\n\n"
            f"Repo: github.com/{repo}\n"
            f"1. Identifiera vilka filer som behöver ändras\n"
            f"2. Implementera featuren\n"
            f"3. Testa lokalt\n4. Pusha till GitHub"
        )
    else:  # docs
        return (
            f"Synka dokumentationen för {name} till NotebookLM.\n"
            f"Repo: github.com/{repo}\n\n"
            f"Läs README.md och viktigaste källfiler.\n"
            f"Skapa eller uppdatera notebook '{name} · Dokumentation'.\n"
            f"Generera Briefing Doc på svenska."
        )


def _tab_my_apps():
    for app in APPS:
        stack_badges = "  ".join(_badge(s, "#94a3b8") for s in app["stack"])
        status_html  = _app_status_badge(app["status"], app["status_label"])

        st.markdown(
            f'<div style="background:#111827;border:1px solid rgba(255,255,255,0.04);'
            f'border-radius:8px;padding:14px 18px;margin-bottom:8px;">'
            f'<div style="display:flex;align-items:flex-start;justify-content:space-between;gap:12px;">'
            f'<div>'
            f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:14px;'
            f'font-weight:700;color:#f1f5f9;margin-bottom:4px;">'
            f'{app["emoji"]} {app["name"]}</div>'
            f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:10px;'
            f'color:#475569;margin-bottom:8px;">{app["repo"]}</div>'
            f'<div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px;">'
            f'{stack_badges}</div>'
            f'</div>'
            f'<div style="flex-shrink:0;">{status_html}</div>'
            f'</div></div>',
            unsafe_allow_html=True,
        )

        # Knappar
        col_repo, col_app, col_fix, col_feat, col_docs, _ = st.columns([1, 1, 1, 1, 1, 2])
        with col_repo:
            st.link_button("Repo →", app["url"], use_container_width=True)
        if app.get("app_url"):
            with col_app:
                st.link_button("App →", app["app_url"], use_container_width=True)

        with col_fix:
            if st.button("🔧 Bugg", key=f"fix_{app['repo']}", use_container_width=True):
                st.session_state[f"quick_{app['repo']}"] = "bug"
        with col_feat:
            if st.button("➕ Feature", key=f"feat_{app['repo']}", use_container_width=True):
                st.session_state[f"quick_{app['repo']}"] = "feature"
        with col_docs:
            if st.button("📚 Docs", key=f"docs_{app['repo']}", use_container_width=True):
                st.session_state[f"quick_{app['repo']}"] = "docs"

        action = st.session_state.get(f"quick_{app['repo']}")
        if action:
            with st.expander("Snabbprompt", expanded=True):
                prompt_text = _quick_prompt_for_app(app, action)
                _copy_prompt(prompt_text, f"quick_{app['repo']}_{action}")


# ── Flik 4 — Snabbstart-mallar ───────────────────────────────────────────────

def _tab_templates():
    for tmpl in TEMPLATES:
        st.markdown(
            f'<div style="background:#111827;border:1px solid rgba(255,255,255,0.04);'
            f'border-radius:8px;padding:16px 20px;margin-bottom:12px;">'
            f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:15px;'
            f'font-weight:700;color:#f1f5f9;margin-bottom:2px;">'
            f'{tmpl["icon"]} {tmpl["name"]}</div>'
            f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:10px;'
            f'color:#6366f1;letter-spacing:0.5px;margin-bottom:8px;">{tmpl["subtitle"]}</div>'
            f'<div style="font-family:\'Inter\',sans-serif;font-size:13px;'
            f'color:#94a3b8;margin-bottom:10px;line-height:1.6;">{tmpl["description"]}</div>'
            f'<div style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:4px;">'
            + "".join(_badge(s, "#6366f1") for s in tmpl["stack"])
            + f'</div>'
            f'<div style="font-family:\'JetBrains Mono\',monospace;font-size:10px;'
            f'color:#475569;margin-top:6px;">⏱ {tmpl["setup_time"]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        with st.expander("Visa Claude Code-prompt", expanded=False):
            _copy_prompt(tmpl["prompt"], f"tmpl_{tmpl['id']}")

        st.markdown("")


# ── Huvud-render ──────────────────────────────────────────────────────────────

def render_app_factory(project, sb):
    st.markdown("## ⚡ App Factory")
    st.markdown(
        '<div style="font-family:\'Inter\',sans-serif;font-size:13px;color:#94a3b8;'
        'margin-bottom:20px;">Starta, planera och bygg nya AI-appar direkt från Studio.</div>',
        unsafe_allow_html=True,
    )

    tab1, tab2, tab3, tab4 = st.tabs([
        "🚀 Ny app",
        "📋 Promptbibliotek",
        "🏗️ Mina appar",
        "⚡ Snabbstart-mallar",
    ])

    with tab1:
        _tab_new_app(project, sb)
    with tab2:
        _tab_prompts()
    with tab3:
        _tab_my_apps()
    with tab4:
        _tab_templates()
