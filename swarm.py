import streamlit as st
import asyncio
import sys
import os


def render_swarm(project: dict | None, sb):
    st.subheader("🐝 Ruflo Testsvärm")
    st.caption("Upp till 90 parallella worker-agenter · Claude Code kör svärmens motor")

    project_id = project["id"] if project else None

    # Konfiguration
    with st.container(border=True):
        st.markdown("**Svärm-konfiguration**")
        col1, col2, col3 = st.columns(3)
        with col1:
            variant = st.text_area("Prompt-variant att testa", height=80,
                                   value="Du är en hjälpsam AI-assistent. Besvara frågan: {input}")
            variant_id = st.text_input("Variant-ID", value="v1")
        with col2:
            n_workers = st.slider("Antal workers", 5, 90, 30, step=5)
            max_concurrent = st.slider("Max parallella (rate limit)", 5, 30, 20, step=5)
        with col3:
            domain = st.text_input("Testdomän", value="general")
            st.metric("Estimerad kostnad", f"~{n_workers * 0.001:.3f} USD")
            st.metric("Estimerad tid", f"~{n_workers // max_concurrent * 3 + 10}s")

    # Kör-knapp
    if st.button("🐝 Starta svärm", use_container_width=True, type="primary"):
        st.info(f"""**Svärm konfigurerad:**
- {n_workers} workers · max {max_concurrent} parallella
- Variant: {variant_id}
- Domän: {domain}

**Kör i terminal:**
```bash
cd dreyer-ai-studio
python -m agents.swarm_runner \\
  --variant "{variant[:50]}..." \\
  --variant-id {variant_id} \\
  --workers {n_workers} \\
  --concurrent {max_concurrent}
```

Eller öppna **Claude Code** och kör `swarm.py` direkt — den är konfigurerad och klar.""")

    st.divider()

    # Historiska körningar från Supabase
    st.markdown("**Historiska svärm-körningar**")
    try:
        runs = sb.table("swarm_runs").select("*").order("created_at", desc=True).limit(10).execute()
        if runs.data:
            for run in runs.data:
                status_icon = "✅" if run["status"] == "completed" else "🔄" if run["status"] == "running" else "❌"
                with st.container(border=True):
                    col1, col2, col3, col4 = st.columns([2, 1, 1, 2])
                    col1.markdown(f"{status_icon} **{run['variant_id']}**")
                    col1.caption(run["created_at"][:16] if run.get("created_at") else "—")
                    col2.metric("Workers", run["n_workers"])
                    pass_rate = run.get("pass_rate")
                    col3.metric("Pass rate", f"{pass_rate*100:.1f}%" if pass_rate else "—")
                    decision = run.get("decision", "—")
                    if decision and "GODKÄND" in decision:
                        col4.success(decision[:80])
                    elif decision and decision != "—":
                        col4.error(decision[:80])
        else:
            st.caption("Inga svärm-körningar ännu. Kör din första svärm via terminalen.")
    except Exception as e:
        st.caption("swarm_runs-tabellen saknas — kör schema.sql i Supabase först.")

    st.divider()
    st.markdown("**Ruflo-arkitektur**")
    st.code("""
Spawner (Claude Code)
    │
    ├── Worker-01 (testcase #001) ─┐
    ├── Worker-02 (testcase #002)  │  Alla parallella
    ├── Worker-03 (testcase #003)  │  Supabase tar emot resultaten
    ├── ...                         │  live medan de trillar in
    └── Worker-90 (testcase #090) ─┘
                   │
              Supabase (worker_results)
                   │
    Architetto aggregerar + beslutar
                   │
    Diavolo säkerhetsgranskar parallellt
    """, language="text")
