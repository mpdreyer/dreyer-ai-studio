import streamlit as st
from datetime import datetime
import subprocess

from db.supabase_client import get_tasks, get_deliverables
from db.portfolio_client import get_all_apps
from agents.router import route_message, build_project_context
from core.errors import error_boundary

AUDIENCES = [
    "👤 Slutanvändare",
    "🔧 Administratör",
    "👨‍💻 Utvecklare",
    "📊 Kund/Beslutsfattare",
]

FORMATS = [
    "📄 Fullständig manual",
    "⚡ Snabbstartsguide",
    "📋 FAQ",
    "🎓 Steg-för-steg tutorial",
]

# Notebook-ID per app-namn
NOTEBOOK_IDS = {
    "Dreyer AI Studio":       "5386eaa2-23ba-4f00-b649-db82221caf4d",
    "DiscCaddy":              "9586d84f-9035-4e39-b345-d33e1b4dc564",
    "Dreyer Council":         "552d945a-ad70-4fa2-8961-311135532800",
    "24-hour-race-helper":    "bd7437e0-d3e1-4b37-acda-79edb0785d77",
    "F1 Analytics":           "d844af5d-74de-4fe3-9c0a-c80577080769",
    "Receptsamlingen":        "ff6e6018-0f64-45dc-ab8a-0dbe86093971",
}


def _build_prompt(app: dict, audience: str, format_type: str) -> str:
    name  = app.get("name", "—")
    desc  = app.get("description", "")
    stack = app.get("tech_stack", [])
    gh    = app.get("github_url", "")
    live  = app.get("live_url", "Inte live än")

    if audience == "👤 Slutanvändare":
        return f"""Du är Narratrix, Demo & Storytelling-expert.
Skriv en vänlig och tydlig användarmanual för {name}
anpassad för icke-tekniska användare.

App-info:
- Beskrivning: {desc}
- Stack: {stack}
- Live: {live}

Format: {format_type}

Manualen ska innehålla:
1. Välkommen — vad är {name} och varför är det användbart?
2. Kom igång på 5 minuter (steg-för-steg)
3. Huvudfunktioner med skärmbeskrivningar
4. Vanliga uppgifter (use cases)
5. Felsökning — vanliga problem och lösningar
6. Tips och tricks
7. Kontakt och support

Skriv på svenska. Undvik teknisk jargong.
Använd rubriker, punktlistor och numrerade steg."""

    if audience == "🔧 Administratör":
        return f"""Skriv en administratörsmanual för {name}.

Innehåll:
1. Installation och konfiguration
2. Miljövariabler och secrets
3. Databas-setup (Supabase)
4. Deployment (Streamlit Cloud / lokal / air-gapped)
5. Användarhantering
6. Backup och underhåll
7. Uppdatering och versionshantering
8. Loggning och felsökning
9. Säkerhetsinställningar

Stack: {stack}
GitHub: {gh}
Skriv tekniskt och precist på svenska."""

    if audience == "👨‍💻 Utvecklare":
        return f"""Skriv en teknisk referensmanual för {name}.

Innehåll:
1. Arkitekturöversikt med filstruktur
2. API-dokumentation (endpoints, parametrar)
3. Databasschema (Supabase-tabeller)
4. Komponenter och moduler
5. Agenter och AI-integration
6. Miljövariabler
7. Testning och kvalitetssäkring
8. Bidra till projektet (pull requests, standards)
9. Changelog och roadmap

GitHub: {gh}
Skriv på engelska med kodexempel."""

    # 📊 Kund/Beslutsfattare
    return f"""Skriv en executive summary / kundbeskrivning
för {name} anpassad för beslutsfattare.

Innehåll:
1. Vad är lösningen? (2 meningar max)
2. Affärsvärde och ROI
3. Hur det fungerar (utan teknisk detalj)
4. Implementeringstid och resurser
5. Nästa steg

Skriv säljande men ärligt på svenska.
Max 1 A4-sida."""


def generate_manual(app_name: str, audience: str, format_type: str,
                    project: dict | None, sb) -> str:
    app_res = sb.table("portfolio_apps").select("*").eq("name", app_name).limit(1).execute()
    app = app_res.data[0] if app_res.data else {"name": app_name}

    prompt = _build_prompt(app, audience, format_type)
    ctx = build_project_context(project) if project else ""

    reply, tokens, cost = route_message(
        "Narratrix",
        [{"role": "user", "content": prompt}],
        project_context=ctx,
        max_tokens=2000,
    )

    if project:
        sb.table("deliverables").insert({
            "project_id":  project["id"],
            "title":       f"Användarmanual — {app_name} ({audience})",
            "owner_agent": "Narratrix",
            "doc_type":    "Markdown",
            "status":      "done",
            "content":     reply,
        }).execute()

    return reply


def _export_manual(manual_text: str, app_name: str, audience: str):
    safe_name = app_name.lower().replace(" ", "_")
    safe_aud  = audience.split()[-1].lower()

    col1, col2, col3 = st.columns(3)

    with col1:
        st.download_button(
            "⬇️ Ladda ner Markdown",
            manual_text,
            file_name=f"{safe_name}_manual_{safe_aud}.md",
            mime="text/markdown",
            use_container_width=True,
        )

    with col2:
        html = f"""<!DOCTYPE html>
<html lang="sv">
<head>
<meta charset="UTF-8">
<title>{app_name} — Användarmanual</title>
<style>
  body {{ font-family: 'Segoe UI', sans-serif;
         max-width: 800px; margin: 40px auto;
         line-height: 1.6; color: #333; }}
  h1 {{ color: #6366f1; border-bottom: 2px solid #6366f1; }}
  h2 {{ color: #1e2130; margin-top: 2em; }}
  code {{ background: #f0f0f0; padding: 2px 6px; border-radius: 4px; }}
  pre {{ background: #1e2130; color: #f1f5f9;
         padding: 16px; border-radius: 8px; }}
  .header {{ background: #0f1117; color: white;
             padding: 20px; border-radius: 8px;
             margin-bottom: 2em; }}
  .footer {{ color: #888; font-size: 12px;
             margin-top: 3em; border-top: 1px solid #eee;
             padding-top: 1em; }}
</style>
</head>
<body>
<div class="header">
  <h1 style="color:white;border:none">{app_name}</h1>
  <p>Användarmanual · DTSM · {audience}</p>
</div>
{manual_text.replace(chr(10), '<br>')}
<div class="footer">
  Genererad av Dreyer AI Studio · Narratrix · DTSM
</div>
</body>
</html>"""
        st.download_button(
            "⬇️ Ladda ner HTML (PDF-redo)",
            html,
            file_name=f"{safe_name}_manual.html",
            mime="text/html",
            use_container_width=True,
        )

    with col3:
        if st.button("📚 Synka till NotebookLM", use_container_width=True,
                     key="nlm_sync_btn"):
            nb_id = NOTEBOOK_IDS.get(app_name)
            if nb_id:
                result = subprocess.run(
                    [
                        "nlm", "source", "add", nb_id,
                        "--text", manual_text,
                        "--title",
                        f"Användarmanual · {audience} · {datetime.now():%Y-%m-%d}",
                    ],
                    capture_output=True, text=True,
                )
                if result.returncode == 0:
                    st.success("Synkad till NotebookLM!")
                else:
                    st.error(f"nlm fel: {result.stderr}")
            else:
                st.warning("Notebook-ID saknas för denna app.")


@error_boundary
def render_user_manual(project: dict | None, sb):
    st.markdown("## 📖 Användarmanual")
    st.caption("Generera automatisk dokumentation via Narratrix")
    st.markdown("---")

    # Hämta alla appar för selectbox
    apps = get_all_apps(sb)
    app_names = [a["name"] for a in apps] if apps else []
    if not app_names:
        st.warning("Inga appar hittades i portfolio_apps.")
        return

    # ── SEKTION 1 — Välj app och nivå ────────────────────────────────────────
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        # Förval: aktiv app om tillgänglig
        default_app = project.get("name") if project else app_names[0]
        default_idx = app_names.index(default_app) if default_app in app_names else 0
        chosen_app = st.selectbox("Välj app", app_names, index=default_idx,
                                  key="manual_app")
    with col2:
        audience = st.selectbox("Målgrupp", AUDIENCES, key="manual_audience")
    with col3:
        fmt = st.selectbox("Format", FORMATS, key="manual_format")

    # ── SEKTION 2 — Knappar ───────────────────────────────────────────────────
    st.markdown("")
    btn1, btn2, btn3 = st.columns(3)
    with btn1:
        do_generate = st.button("✍️ Generera manual", type="primary",
                                use_container_width=True)
    with btn2:
        do_preview = st.button("🔍 Förhandsgranska", use_container_width=True)
    with btn3:
        do_export = st.button("📥 Exportera", use_container_width=True)

    st.markdown("---")

    # Auto-trigger från fas 7
    if st.session_state.pop("auto_generate_manual", False):
        with st.spinner("Narratrix genererar manual automatiskt…"):
            manual = generate_manual(
                project["name"] if project else chosen_app,
                "👤 Slutanvändare",
                "📄 Fullständig manual",
                project,
                sb,
            )
            st.session_state["generated_manual"] = manual
        st.success("Manual genererad automatiskt!")

    # Generera
    if do_generate:
        with st.spinner("Narratrix skriver manualen…"):
            manual = generate_manual(chosen_app, audience, fmt, project, sb)
            st.session_state["generated_manual"] = manual
        st.success("Manual genererad och sparad som leverans!")

    # Förhandsgranska
    if do_preview and "generated_manual" in st.session_state:
        st.markdown(st.session_state["generated_manual"])
    elif do_preview:
        st.info("Generera en manual först.")

    # Exportera
    if do_export:
        if "generated_manual" in st.session_state:
            _export_manual(st.session_state["generated_manual"], chosen_app, audience)
        else:
            st.info("Generera en manual först.")

    # Visa sparad manual om den finns
    if "generated_manual" in st.session_state and not do_preview:
        with st.expander("Senast genererad manual", expanded=True):
            st.markdown(st.session_state["generated_manual"])
            st.markdown("---")
            _export_manual(st.session_state["generated_manual"], chosen_app, audience)
