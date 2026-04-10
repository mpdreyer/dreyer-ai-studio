import os
import pathlib
import subprocess
from datetime import datetime

import streamlit as st

from agents.council import AGENTS
from agents.router import build_project_context, route_message
from db.supabase_client import log_tokens, save_message
from core.errors import error_boundary

DTSM_APPS = {
    "Dreyer AI Studio":    "~/dreyer-ai-studio",
    "Dreyer Council":      "~/dreyer-council",
    "DiscCaddy":           "~/DiscCaddy",
    "Receptsamlingen":     "~/recipe-scraper",
    "24-hour-race-helper": "~/24Timmars/24-hour-race-helper",
    "24h Race Helper AI":  "~/24Timmars/24-hour-race-helper-AI",
    "pixel-agents":        "~/pixel-agents/src",
    "DiscGolf Caddy":      "~/DiscGolfCaddy",
    "F1 Analytics":        None,
}

NOTEBOOK_IDS = {
    "Dreyer AI Studio": "5386eaa2-23ba-4f00-b649-db82221caf4d",
    "Dreyer Council":   "552d945a-ad70-4fa2-8961-311135532800",
    "DiscCaddy":        "9586d84f-9035-4e39-b345-d33e1b4dc564",
    "Receptsamlingen":  "ff6e6018-0f64-45dc-ab8a-0dbe86093971",
    "F1 Analytics":     "d844af5d-74de-4fe3-9c0a-c80577080769",
}

FILE_EXTENSIONS = {
    "Python (.py)":         ".py",
    "TypeScript (.ts/.tsx)": ".ts",
    "JavaScript (.js/.jsx)": ".js",
    "Alla":                  None,
}

MAX_CHARS = 15_000
SKIP_DIRS = {".git", "__pycache__", "node_modules", ".venv", "dist", "build", ".next"}


def _read_files(app_path: str, ext_filter: str | None, max_files: int = 10) -> dict:
    path = pathlib.Path(os.path.expanduser(app_path))
    if not path.exists():
        return {}
    exts = ({".py", ".ts", ".tsx", ".js", ".jsx"} if ext_filter is None
            else {ext_filter, ext_filter + "x"})

    def _priority(f):
        rel = str(f.relative_to(path))
        for i, kw in enumerate(["components", "views", "agents", "db", "helpers"]):
            if kw in rel:
                return i + 1
        return 0 if f.parent == path else 6

    files = sorted(
        [f for f in path.rglob("*")
         if f.suffix in exts and not any(s in f.parts for s in SKIP_DIRS)],
        key=_priority,
    )
    result = {}
    for f in files[:max_files]:
        try:
            result[str(f.relative_to(path))] = f.read_text(encoding="utf-8", errors="replace")
        except Exception:
            pass
    return result


def _build_code_block(files: dict) -> str:
    out, chars = "", 0
    for fname, content in files.items():
        if chars >= MAX_CHARS:
            out += f"\n[… fler filer ej inkluderade pga token-budget …]\n"
            break
        excerpt = content[:MAX_CHARS - chars]
        out += f"\n\n{'='*40}\nFIL: {fname}\n{'='*40}\n{excerpt}"
        chars += len(excerpt)
    return out


def _run_agent(agent: str, prompt: str, ctx: str, max_tok: int,
               pid: str | None, sb) -> str:
    reply, tokens, cost = route_message(
        agent, [{"role": "user", "content": prompt}],
        project_context=ctx, max_tokens=max_tok,
    )
    if pid:
        save_message(sb, pid, "assistant", reply,
                     agent=agent, model=AGENTS[agent]["model"],
                     tokens=tokens, cost=cost)
        log_tokens(sb, pid, agent, AGENTS[agent]["model"],
                   tokens // 2, tokens - tokens // 2, cost)
    return reply


@error_boundary
def render_code_analyzer(project: dict | None, sb):
    st.markdown("## 🔬 Kodanalys")
    st.caption("Rådet granskar koden — buggar, säkerhet och teknisk skuld.")

    pid = project["id"] if project else None
    ctx = build_project_context(project) if project else ""

    # ── Val ───────────────────────────────────────────────────────────────────
    c1, c2, c3 = st.columns([3, 2, 2])
    with c1:
        opts = list(DTSM_APPS.keys())
        default = 0
        if project:
            pname = project.get("name", "").lower()
            for i, n in enumerate(opts):
                if n.lower() in pname or pname in n.lower():
                    default = i
                    break
        selected = st.selectbox("App", opts, index=default,
                                label_visibility="collapsed")
    with c2:
        ext_label = st.selectbox("Filtyp", list(FILE_EXTENSIONS.keys()),
                                  label_visibility="collapsed")
    with c3:
        uploaded = st.file_uploader("Ladda upp fil",
                                    type=["py","ts","tsx","js","jsx"],
                                    label_visibility="collapsed")

    analysis_types = st.multiselect(
        "Fokus",
        ["🐛 Buggar och fel", "🏗️ Arkitektur", "🔒 Säkerhet",
         "⚡ Prestanda", "🧹 Teknisk skuld", "📈 Förbättringspotential",
         "🔄 Refaktorering", "📚 Dokumentation"],
        default=["🐛 Buggar och fel", "🏗️ Arkitektur", "📈 Förbättringspotential"],
        label_visibility="collapsed",
    )
    focus = ", ".join(t.split(" ", 1)[1] for t in analysis_types) or "generell kvalitet"

    # ── Ladda kod ─────────────────────────────────────────────────────────────
    code_files: dict = {}
    if uploaded:
        txt = uploaded.read().decode("utf-8", errors="replace")
        code_files[uploaded.name] = txt
        st.info(f"Uppladdad: **{uploaded.name}** ({len(txt):,} tecken)")
    else:
        app_path = DTSM_APPS.get(selected)
        if app_path:
            code_files = _read_files(app_path, FILE_EXTENSIONS[ext_label])
            if code_files:
                st.success(f"**{len(code_files)} filer** laddade från `{app_path}`")
                with st.expander(f"Filer ({len(code_files)} st)"):
                    for f in code_files:
                        st.code(f, language="text")
            else:
                st.warning(f"Inga filer hittades i `{app_path}`. Ladda upp manuellt.")
        else:
            st.info(f"Ingen lokal sökväg för **{selected}**. Ladda upp fil ovan.")

    with st.expander("📋 Klistra in kod manuellt"):
        manual = st.text_area("Kod", height=150, placeholder="# Klistra in kod…")
        mname  = st.text_input("Filnamn", value="code.py")
        if manual.strip():
            code_files[mname] = manual

    st.divider()

    if not code_files:
        st.info("Välj en app, ladda upp en fil eller klistra in kod ovan.")
        return

    code_block = _build_code_block(code_files)
    total_ch   = sum(len(v) for v in code_files.values())
    st.caption(f"{total_ch:,} tecken · {len(code_files)} filer · "
               f"max {MAX_CHARS:,} tecken per anrop")

    # ── Enskilda knappar ──────────────────────────────────────────────────────
    ca, cb, cc = st.columns(3)

    with ca:
        if st.button("🏛️ Architetto — Arkitektur",
                     use_container_width=True, type="primary"):
            p = (f"Du är Architetto, Chief AI Architect.\n"
                 f"Analysera koden från **{selected}** med fokus på: {focus}\n\n"
                 f"KOD:\n{code_block}\n\n"
                 "Ge:\n1. Övergripande bedömning (2-3 meningar)\n"
                 "2. Arkitektur och struktur\n"
                 "3. Problem (HÖG/MEDIUM/LÅG)\n"
                 "4. Tre förbättringsförslag med kodexempel\n"
                 "5. Teknisk skuld att adressera långsiktigt")
            with st.spinner("Architetto analyserar…"):
                r = _run_agent("Architetto", p, ctx, 1500, pid, sb)
            st.markdown("### 🏛️ Architetto — Arkitekturanalys")
            st.markdown(r)
            st.session_state["ca_arch"] = r

    with cb:
        if st.button("🔴 Diavolo — Säkerhet", use_container_width=True):
            p = (f"Du är Diavolo. Granska koden från **{selected}** ur säkerhetsperspektiv.\n\n"
                 f"KOD:\n{code_block}\n\n"
                 "Analysera: säkerhetssårbarheter, API-nyckelexponering, "
                 "indata-validering, prompt injection, dependency-risker.\n"
                 "Rangordna 🔴 HÖG / 🟡 MEDIUM / 🟢 LÅG. "
                 "Åtgärdsrekommendation per fynd.")
            with st.spinner("Diavolo granskar…"):
                r = _run_agent("Diavolo", p, ctx, 1200, pid, sb)
            st.markdown("### 🔴 Diavolo — Säkerhetsanalys")
            st.markdown(r)
            st.session_state["ca_sec"] = r

    with cc:
        if st.button("🧪 Logica — Kodkvalitet", use_container_width=True):
            p = (f"Du är Logica. Analysera kodkvaliteten i **{selected}**.\n\n"
                 f"KOD:\n{code_block}\n\n"
                 "Granska: DRY-brott, funktionskomplexitet, felhantering, "
                 "testbarhet, namngivning, dokumentation.\n"
                 "Ge de tre viktigaste refaktoreringsförslagen med kodexempel.")
            with st.spinner("Logica analyserar…"):
                r = _run_agent("Logica", p, ctx, 1200, pid, sb)
            st.markdown("### 🧪 Logica — Kodkvalitetsanalys")
            st.markdown(r)
            st.session_state["ca_qual"] = r

    st.divider()

    # ── Full analys ───────────────────────────────────────────────────────────
    if st.button("🚀 Kör full analys — alla tre agenter",
                 use_container_width=True, type="primary"):
        results: dict = {}
        cfg = [
            ("Architetto", "arkitektur och struktur",
             f"Analysera koden från {selected}, fokus: arkitektur och struktur.\n"
             f"KOD:\n{code_block[:5000]}\nMax 5 prioriterade fynd med åtgärder."),
            ("Diavolo", "säkerhet",
             f"Granska koden från {selected}, fokus: säkerhet.\n"
             f"KOD:\n{code_block[:5000]}\nMax 5 fynd, HÖG/MEDIUM/LÅG."),
            ("Logica", "kodkvalitet",
             f"Analysera kodkvaliteten i {selected}.\n"
             f"KOD:\n{code_block[:5000]}\nMax 5 förbättringsförslag."),
        ]
        bar = st.progress(0)
        for i, (agent, focus_txt, prompt) in enumerate(cfg):
            with st.spinner(f"{agent} analyserar {focus_txt}…"):
                results[agent] = _run_agent(agent, prompt, ctx, 800, pid, sb)
            bar.progress((i + 1) / len(cfg))

        labels = {"Architetto": "🏛️ Arkitektur", "Diavolo": "🔴 Säkerhet", "Logica": "🧪 Kvalitet"}
        cols = st.columns(3)
        for col, (agent, reply) in zip(cols, results.items()):
            with col:
                st.markdown(f"**{labels[agent]}**")
                st.markdown(reply)

        st.divider()
        st.markdown("**🏛️ Architetto — Prioriterade åtgärder:**")
        sum_p = (f"Sammanfatta de viktigaste åtgärderna från dessa tre analyser av {selected}.\n\n"
                 f"Arkitektur: {results.get('Architetto','')[:400]}\n"
                 f"Säkerhet: {results.get('Diavolo','')[:400]}\n"
                 f"Kvalitet: {results.get('Logica','')[:400]}\n\n"
                 "Max 5 åtgärder, prioriterade efter påverkan. "
                 "Grov tidsuppskattning per åtgärd (30 min / 2 h / 1 dag).")
        with st.spinner("Architetto sammanfattar…"):
            summary = _run_agent("Architetto", sum_p, ctx, 600, pid, sb)
        st.success(summary)

        st.session_state.update({
            "ca_full":    results,
            "ca_summary": summary,
            "ca_app":     selected,
            "ca_files":   list(code_files.keys()),
        })

    # ── NotebookLM-export ─────────────────────────────────────────────────────
    if (st.session_state.get("ca_summary")
            and st.session_state.get("ca_app") == selected):
        st.divider()
        if st.button("📚 Spara analys till NotebookLM"):
            results  = st.session_state.get("ca_full", {})
            summary  = st.session_state["ca_summary"]
            fnames   = st.session_state.get("ca_files", [])
            today    = datetime.now().strftime("%Y-%m-%d")
            doc = (
                f"# Kodanalys — {selected}\nDatum: {today}\n"
                f"Analyserade filer: {', '.join(fnames)}\n\n"
                f"## Arkitektur (Architetto)\n{results.get('Architetto','—')}\n\n"
                f"## Säkerhet (Diavolo)\n{results.get('Diavolo','—')}\n\n"
                f"## Kodkvalitet (Logica)\n{results.get('Logica','—')}\n\n"
                f"## Prioriterade åtgärder\n{summary}"
            )
            nb_id = NOTEBOOK_IDS.get(selected)
            if nb_id:
                res = subprocess.run(
                    ["nlm", "source", "add", nb_id,
                     "--text", doc, "--title", f"Kodanalys {today}"],
                    capture_output=True, text=True,
                )
                if res.returncode == 0:
                    st.success(f"✅ Sparad i NotebookLM för {selected}")
                else:
                    st.warning(f"nlm-fel: {res.stderr[:200]}")
                    st.download_button("⬇️ Ladda ner som markdown", doc,
                                       f"kodanalys_{selected}_{today}.md",
                                       mime="text/markdown")
            else:
                st.download_button("⬇️ Ladda ner som markdown", doc,
                                   f"kodanalys_{selected}_{today}.md",
                                   mime="text/markdown")
