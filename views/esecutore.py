"""
Esecutore View — Execution Hub
==============================
UI for att generera exekverbara prompts till Claude Code och Codex CLI.
"""

import streamlit as st
from datetime import datetime
from agents.esecutore import (
    generate_execution_prompt,
    save_execution_prompt,
    mark_as_executed,
    get_recent_prompts,
)
from db.supabase_client import get_supabase


PROMPT_TYPES = {
    "init": ("\U0001f195", "Initiera nytt repo", "Skapar git-repo, mappstruktur, requirements, README"),
    "feature": ("\u2795", "Lagg till feature", "Lagger till ny funktionalitet i befintligt repo"),
    "fix": ("\U0001f41b", "Fixa bug", "Identifierar och fixar specifik bug eller issue"),
    "refactor": ("\U0001f527", "Refaktorera", "Strukturella forbattringar utan beteendeandring"),
    "test": ("\u2705", "Generera tester", "Happy path + edge cases + mocks"),
    "docs": ("\U0001f4da", "Dokumentation", "Komplett docs/-mapp + NotebookLM-sync"),
    "custom": ("\u2728", "Custom", "Fri-text -- du beskriver, Esecutore exekverar"),
}

TARGETS = {
    "claude_code": ("\u26a1", "Claude Code", "Stegvis, konversationell stil"),
    "codex_cli": ("\U0001f916", "Codex CLI", "Kommandodriven, kort stil"),
    "custom": ("\U0001f3a8", "Custom", "Anpassat format"),
}


def render_esecutore(project: dict = None, sb=None):
    """Render the Esecutore Execution Hub view."""

    if sb is None:
        sb = get_supabase()

    # --- Custom CSS ---------------------------------------------------------
    st.markdown("""
    <style>
    .esecutore-header {
        border-bottom: 1px solid #f59e0b;
        padding-bottom: 1rem;
        margin-bottom: 1.5rem;
    }
    .esecutore-header h1 {
        font-family: 'JetBrains Mono', monospace;
        color: #f59e0b;
        font-size: 1.2rem;
        letter-spacing: 0.15em;
        margin: 0;
    }
    .esecutore-tagline {
        font-family: 'JetBrains Mono', monospace;
        color: #94a3b8;
        font-size: 0.75rem;
        font-style: italic;
        margin-top: 0.3rem;
    }
    .prompt-output {
        background: #0d1220;
        border: 1px solid #f59e0b;
        border-radius: 8px;
        padding: 1.2rem;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.82rem;
        white-space: pre-wrap;
        max-height: 500px;
        overflow-y: auto;
    }
    .history-item {
        background: #0d1220;
        border: 1px solid #1a2540;
        border-radius: 6px;
        padding: 0.7rem 1rem;
        margin-bottom: 0.5rem;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
    }
    .badge-generated { color: #f59e0b; }
    .badge-executed { color: #22c55e; }
    .badge-completed { color: #6366f1; }
    .badge-failed { color: #ef4444; }
    </style>
    """, unsafe_allow_html=True)

    # --- HEADER -------------------------------------------------------------
    st.markdown("""
    <div class="esecutore-header">
        <h1>\u26a1 ESECUTORE \u00b7 EXECUTION HUB</h1>
        <div class="esecutore-tagline">"Basta parlare. Facciamo." \u2014 Agent 13</div>
    </div>
    """, unsafe_allow_html=True)

    # --- PROJEKT-VAL (om inte redan valt) -----------------------------------
    if project is None:
        projects = sb.table("projects").select("id, name, brief_raw, tech_stack, status").eq("status", "active").execute()
        if not projects.data:
            st.warning("Inga aktiva projekt hittades. Skapa ett projekt forst.")
            return

        project_options = {p["name"]: p for p in projects.data}
        selected_name = st.selectbox(
            "VALJ PROJEKT",
            options=list(project_options.keys()),
            key="esecutore_project_select"
        )
        project = project_options[selected_name]

    st.caption(f"\U0001f4c2 **{project['name']}** \u00b7 {project.get('status', 'active')}")

    # --- SESSION STATE ------------------------------------------------------
    for key in ["generated_prompt", "prompt_id", "generation_meta"]:
        if key not in st.session_state:
            st.session_state[key] = None

    # --- KONFIGURATION ------------------------------------------------------
    st.markdown("### Konfiguration")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Target**")
        target = st.radio(
            "target",
            options=list(TARGETS.keys()),
            format_func=lambda x: f"{TARGETS[x][0]} {TARGETS[x][1]}",
            label_visibility="collapsed",
            key="esecutore_target"
        )
        st.caption(TARGETS[target][2])

    with col2:
        st.markdown("**Prompt-typ**")
        prompt_type = st.radio(
            "prompt_type",
            options=list(PROMPT_TYPES.keys()),
            format_func=lambda x: f"{PROMPT_TYPES[x][0]} {PROMPT_TYPES[x][1]}",
            label_visibility="collapsed",
            key="esecutore_prompt_type"
        )
        st.caption(PROMPT_TYPES[prompt_type][2])

    user_context = st.text_area(
        "EXTRA KONTEXT (optional)",
        placeholder="T.ex. specifik feature, bug-beskrivning, eller annat du vill ge Esecutore...",
        height=100,
        key="esecutore_user_context"
    )

    st.markdown("**Inkludera automatiskt:**")
    col_a, col_b, col_c, col_d, col_e = st.columns(5)
    with col_a:
        inc_brief = st.checkbox("Brief", value=True, key="esecutore_inc_brief")
    with col_b:
        inc_sc = st.checkbox("Success Criteria", value=True, key="esecutore_inc_sc")
    with col_c:
        inc_ts = st.checkbox("Tech Stack", value=True, key="esecutore_inc_ts")
    with col_d:
        inc_dlv = st.checkbox("Deliverables", value=True, key="esecutore_inc_dlv")
    with col_e:
        inc_nb = st.checkbox("NotebookLM", value=False, key="esecutore_inc_nb")

    # --- GENERATE BUTTON ----------------------------------------------------
    st.markdown("---")
    if st.button("\u26a1 GENERERA EXEKVERINGSPROMPT", use_container_width=True, type="primary"):
        with st.spinner("Esecutore genererar prompt..."):
            try:
                result = generate_execution_prompt(
                    project=project,
                    prompt_type=prompt_type,
                    target=target,
                    user_context=user_context,
                    include_brief=inc_brief,
                    include_success_criteria=inc_sc,
                    include_tech_stack=inc_ts,
                    include_deliverables=inc_dlv,
                    include_notebooklm=inc_nb,
                )

                # Spara i Supabase
                prompt_id = save_execution_prompt(
                    project_id=project["id"],
                    prompt_type=prompt_type,
                    target=target,
                    user_context=user_context,
                    generated_prompt=result["prompt"],
                    tokens_used=result["tokens_used"],
                    cost_usd=result["cost_usd"],
                    include_flags={
                        "include_brief": inc_brief,
                        "include_success_criteria": inc_sc,
                        "include_tech_stack": inc_ts,
                        "include_deliverables": inc_dlv,
                        "include_notebooklm": inc_nb,
                    },
                )

                st.session_state.generated_prompt = result["prompt"]
                st.session_state.prompt_id = prompt_id
                st.session_state.generation_meta = {
                    "tokens": result["tokens_used"],
                    "cost": result["cost_usd"],
                }
                st.rerun()
            except Exception as e:
                st.error(f"Esecutore-fel: {e}")

    # --- OUTPUT -------------------------------------------------------------
    if st.session_state.generated_prompt:
        st.markdown("---")
        st.markdown("### \U0001f4cb Genererad prompt")

        meta = st.session_state.generation_meta
        if meta:
            st.caption(f"\U0001f525 {meta['tokens']} tokens \u00b7 ${meta['cost']:.4f}")

        st.code(st.session_state.generated_prompt, language="markdown")

        col_x, col_y = st.columns(2)
        with col_x:
            if st.button("\u2713 MARKERA SOM EXEKVERAD", use_container_width=True):
                mark_as_executed(st.session_state.prompt_id)
                st.success("Markerad som exekverad!")
                st.session_state.generated_prompt = None
                st.session_state.prompt_id = None
                st.rerun()
        with col_y:
            if st.button("\U0001f5d1 RENSA", use_container_width=True):
                st.session_state.generated_prompt = None
                st.session_state.prompt_id = None
                st.rerun()

    # --- HISTORIK -----------------------------------------------------------
    st.markdown("---")
    st.markdown("### \U0001f4dc Historik (senaste 5)")

    recent = get_recent_prompts(project["id"], limit=5)
    if not recent:
        st.caption("Inga tidigare prompts for detta projekt.")
    else:
        for r in recent:
            status_class = f"badge-{r['status']}"
            created = r['created_at'][:16].replace('T', ' ')
            st.markdown(
                f"""<div class="history-item">
                <span class="{status_class}">\u25cf</span>
                <strong>{r['prompt_type']}</strong> \u00b7 {r['target']} \u00b7
                <span class="{status_class}">{r['status']}</span> \u00b7
                <span style="color:#64748b">{created}</span>
                </div>""",
                unsafe_allow_html=True
            )
