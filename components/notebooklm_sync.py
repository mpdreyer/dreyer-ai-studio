"""
NotebookLM-synk-komponent.
Fyra lägen: A) MCP aktiv  B) nlm CLI  C) Manuell prompt  D) Export till fil
"""

import os
import subprocess
import streamlit as st
from datetime import date
from pathlib import Path


# ── nlm CLI-hjälpfunktioner ───────────────────────────────────────────────────

def check_nlm_auth() -> bool:
    """Returnerar True om nlm är autentiserat och kan lista notebooks."""
    try:
        result = subprocess.run(
            ["nlm", "notebook", "list"],
            capture_output=True, text=True, timeout=15,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def sync_notebook_via_cli(notebook_id: str, text: str, title: str) -> bool:
    """Lägger till en textkälla i ett notebook via nlm CLI. Returnerar True vid framgång."""
    try:
        result = subprocess.run(
            ["nlm", "source", "add", notebook_id,
             "--text", text, "--title", title],
            capture_output=True, text=True, timeout=60,
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False


def get_nlm_notebooks() -> list[dict]:
    """Hämtar lista med notebooks via nlm CLI. Returnerar lista med dicts."""
    try:
        result = subprocess.run(
            ["nlm", "notebook", "list", "--json"],
            capture_output=True, text=True, timeout=15,
        )
        if result.returncode == 0:
            import json
            return json.loads(result.stdout)
    except Exception:
        pass
    return []


# ── App-konfiguration ─────────────────────────────────────────────────────────

APP_CONFIGS = {
    "Dreyer AI Studio": {
        "path":       str(Path.home() / "dreyer-ai-studio"),
        "github":     "mpdreyer/dreyer-ai-studio",
        "sources": [
            ("README.md",            "README"),
            ("db/schema.sql",        "Databas-schema"),
            ("requirements.txt",     "Beroenden"),
            ("agents/council.py",    "Agent-definitioner"),
        ],
    },
    "DiscCaddy": {
        "path":       str(Path.home() / "DiscCaddy"),
        "github":     "mpdreyer/DiscCaddy",
        "sources": [
            ("README.md",        "README"),
            ("disc_app.py",      "Huvud-app"),
            ("requirements.txt", "Beroenden"),
        ],
    },
    "Dreyer Council": {
        "path":       str(Path.home() / "dreyer-council"),
        "github":     "mpdreyer/dreyer-council",
        "sources": [
            ("README.md",    "README"),
            ("council.py",   "Council-logik"),
        ],
    },
    "Tactical 24H": {
        "path":       str(Path.home() / "24-hour-race-helper"),
        "github":     "mpdreyer/24-hour-race-helper",
        "sources": [
            ("README.md", "README"),
        ],
    },
}


def _read_source_files(app_name: str) -> str:
    """Läser källfiler för en app och returnerar sammanslagen text."""
    cfg      = APP_CONFIGS.get(app_name, {})
    app_path = Path(cfg.get("path", ""))
    sources  = cfg.get("sources", [])
    parts    = []

    for rel_path, label in sources:
        full = app_path / rel_path
        if full.exists():
            content = full.read_text(errors="replace")
            # Trunkera långa filer
            if len(content) > 4000:
                content = content[:4000] + "\n… [trunkerad]"
            parts.append(f"## {label} ({rel_path})\n\n```\n{content}\n```")

    # Generera dynamisk filstruktur
    if app_path.exists():
        tree_lines = []
        for root, dirs, files in os.walk(app_path):
            # Skippa dolda och cache-mappar
            dirs[:] = [d for d in sorted(dirs)
                       if not d.startswith(".") and d not in ("__pycache__", ".venv", "node_modules")]
            level  = len(Path(root).relative_to(app_path).parts)
            indent = "  " * level
            folder = Path(root).name
            if level > 0:
                tree_lines.append(f"{indent}{folder}/")
            for f in sorted(files):
                if not f.startswith(".") and not f.endswith(".pyc"):
                    tree_lines.append(f"{indent}  {f}")
            if level >= 2:
                break  # Max 3 nivåer
        if tree_lines:
            parts.insert(0, "## Filstruktur\n\n```\n" + "\n".join(tree_lines[:60]) + "\n```")

    return "\n\n---\n\n".join(parts) if parts else "Inga källfiler hittades."


def generate_app_documentation(app_name: str) -> str:
    """
    Genererar komplett systemdokumentation via Architetto.
    Returnerar markdown-sträng.
    """
    from agents.router import route_message

    file_contents = _read_source_files(app_name)
    cfg           = APP_CONFIGS.get(app_name, {})
    github        = cfg.get("github", "")

    prompt = f"""Baserat på dessa filer från **{app_name}**, generera komplett systemdokumentation på svenska.

GitHub: https://github.com/{github}

{file_contents}

Inkludera följande sektioner:
1. **Syfte och målgrupp** — vad appen löser och för vem
2. **Teknisk arkitektur och stack** — ramverk, databaser, AI-modeller
3. **Installation och konfiguration** — steg-för-steg
4. **Moduler och komponenter** — vad varje fil gör
5. **API-integrationer** — externa tjänster och nycklar som krävs
6. **Kända begränsningar och nästa steg** — vad som saknas

Var konkret och teknisk. Rikta dokumentationen till en senior utvecklare."""

    content, tokens, cost = route_message(
        "Architetto",
        [{"role": "user", "content": prompt}],
        max_tokens=2048,
    )
    return content, tokens, cost


def build_notebooklm_prompt(app_name: str, notebook_id: str, documentation: str) -> str:
    """Bygger en färdig Claude-prompt för NotebookLM-synk."""
    cfg    = APP_CONFIGS.get(app_name, {})
    github = cfg.get("github", "")
    today  = date.today().isoformat()

    return f"""Synka {app_name} till NotebookLM.

Notebook-ID: {notebook_id}

Kör dessa kommandon i ordning:

1. notebooklm:notebook_add_text
   notebook_id: {notebook_id}
   title: "{app_name} · Systemdokumentation · {today}"
   text: [SE DOKUMENTATION NEDAN]

2. notebooklm:notebook_add_url
   notebook_id: {notebook_id}
   url: https://github.com/{github}

3. notebooklm:report_create
   notebook_id: {notebook_id}
   report_format: "Briefing Doc"
   language: "sv"
   confirm: true

━━━ DOKUMENTATION ━━━

{documentation}"""


def render_mode_a_button(app_name: str, notebook_id: str):
    """Läge A: Direkt MCP-synk (visas bara om MCP är aktiv)."""
    st.success("🟢 NotebookLM MCP aktiv — direkt synk tillgänglig")
    if st.button(f"⚡ Synka {app_name} direkt", key=f"mcp_sync_{app_name}", type="primary"):
        with st.spinner(f"Genererar dokumentation för {app_name}…"):
            try:
                docs, tokens, cost = generate_app_documentation(app_name)
                st.session_state[f"docs_{app_name}"] = docs
                st.session_state[f"prompt_{app_name}"] = build_notebooklm_prompt(
                    app_name, notebook_id or "[NOTEBOOK-ID]", docs
                )
                st.success(f"✓ Dokumentation genererad — {tokens:,} tokens, {cost:.4f} USD")
            except Exception as e:
                st.error(f"Fel: {e}")


def render_mode_cli(app_name: str, notebook_id: str):
    """Läge B: nlm CLI-synk (persistent auth via Google, ingen cookie-klistring)."""
    st.info("🔵 nlm CLI aktiv — synkar via persistent Google-autentisering")
    col1, col2 = st.columns([1, 3])
    with col1:
        run_cli = st.button(
            f"📡 Synka via nlm",
            key=f"cli_sync_{app_name}",
            use_container_width=True,
            type="primary",
        )
    with col2:
        if not notebook_id:
            st.caption("⚠️ Notebook-ID saknas — kan inte synka.")

    if run_cli and notebook_id:
        with st.spinner(f"Genererar dokumentation och synkar till NotebookLM…"):
            try:
                docs, tokens, cost = generate_app_documentation(app_name)
                today = date.today().isoformat()
                title = f"{app_name} · Systemdokumentation · {today}"
                ok = sync_notebook_via_cli(notebook_id, docs, title)
                if ok:
                    st.success(
                        f"✅ Synkat till NotebookLM via nlm CLI — "
                        f"{tokens:,} tokens, {cost:.4f} USD"
                    )
                else:
                    st.error("nlm CLI returnerade fel. Kontrollera att `nlm login` är kört.")
            except Exception as e:
                st.error(f"Fel: {e}")


def render_mode_b_prompt(app_name: str, notebook_id: str):
    """Läge B: Genererar prompt för manuell klistring."""
    st.warning("🟡 MCP inte aktiv — generera prompt att köra i Claude")

    col1, col2 = st.columns([1, 3])
    with col1:
        generate = st.button(
            "📝 Generera prompt",
            key=f"gen_prompt_{app_name}",
            use_container_width=True,
        )
    with col2:
        if not notebook_id:
            st.caption("⚠️ Notebook-ID saknas — lägg till det i tabellen ovan för att generera komplett prompt.")

    if generate:
        with st.spinner(f"Architetto dokumenterar {app_name}…"):
            try:
                docs, tokens, cost = generate_app_documentation(app_name)
                st.session_state[f"docs_{app_name}"] = docs
                st.session_state[f"prompt_{app_name}"] = build_notebooklm_prompt(
                    app_name, notebook_id or "[NOTEBOOK-ID SAKNAS]", docs
                )
                st.caption(f"{tokens:,} tokens · {cost:.4f} USD")
            except Exception as e:
                st.error(f"Kunde inte generera dokumentation: {e}")

    if st.session_state.get(f"prompt_{app_name}"):
        st.markdown("**Klistra in denna prompt i Claude:**")
        st.code(st.session_state[f"prompt_{app_name}"], language="text")


def render_mode_c_export(app_name: str):
    """Läge C: Ladda ner dokumentation som markdown-fil."""
    docs = st.session_state.get(f"docs_{app_name}")

    if not docs:
        col1, col2 = st.columns([1, 3])
        with col1:
            if st.button("📄 Generera dokument", key=f"gen_doc_{app_name}", use_container_width=True):
                with st.spinner("Genererar…"):
                    try:
                        docs, tokens, cost = generate_app_documentation(app_name)
                        st.session_state[f"docs_{app_name}"] = docs
                        st.rerun()
                    except Exception as e:
                        st.error(str(e))
        return

    today    = date.today().isoformat()
    filename = f"{app_name.lower().replace(' ', '_')}_dokumentation_{today}.md"
    full_doc = f"# {app_name} · Systemdokumentation\n_Genererad: {today}_\n\n{docs}"

    st.download_button(
        label="⬇️ Ladda ner markdown",
        data=full_doc,
        file_name=filename,
        mime="text/markdown",
        key=f"download_{app_name}",
        use_container_width=False,
    )
    st.caption(
        "Ladda upp denna fil på **notebooklm.google.com** → "
        "ditt notebook → **+ Lägg till källa**"
    )
    with st.expander("Förhandsgranska dokumentation"):
        st.markdown(docs)
