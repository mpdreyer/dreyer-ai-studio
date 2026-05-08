"""
Giustizia View -- Compliance Hub
================================
UI for EU AI Act, GDPR och eIDAS 2.0 compliance-analyser.
"""

import streamlit as st
from agents.giustizia import run_analysis, save_analysis, get_recent_analyses, ANALYSIS_TYPES
from db.supabase_client import get_supabase


def render_giustizia(project: dict = None, sb=None):
    """Render the Giustizia Compliance Hub view."""

    if sb is None:
        sb = get_supabase()

    # --- CSS --------------------------------------------------------------
    st.markdown("""
    <style>
    .giustizia-header {
        border-bottom: 2px solid #0ea5e9;
        padding-bottom: 1rem;
        margin-bottom: 1.5rem;
    }
    .giustizia-header h1 {
        font-family: 'JetBrains Mono', monospace;
        color: #0ea5e9;
        font-size: 1.2rem;
        letter-spacing: 0.15em;
        margin: 0;
    }
    .giustizia-tagline {
        font-family: 'JetBrains Mono', monospace;
        color: #94a3b8;
        font-size: 0.75rem;
        font-style: italic;
        margin-top: 0.3rem;
    }
    .regulation-badge {
        display: inline-block;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.65rem;
        padding: 0.25rem 0.6rem;
        border-radius: 4px;
        margin-right: 0.4rem;
        font-weight: 600;
        letter-spacing: 0.08em;
    }
    .badge-ai-act { background: rgba(14,165,233,0.15); color: #0ea5e9; border: 1px solid #0ea5e9; }
    .badge-gdpr   { background: rgba(99,102,241,0.15); color: #6366f1; border: 1px solid #6366f1; }
    .badge-eidas  { background: rgba(34,197,94,0.15);  color: #22c55e; border: 1px solid #22c55e; }
    .risk-card {
        border-radius: 8px;
        padding: 1rem 1.2rem;
        margin-bottom: 0.8rem;
        font-family: 'JetBrains Mono', monospace;
    }
    .risk-forbidden  { background: rgba(239,68,68,0.1);  border: 1px solid #ef4444; }
    .risk-high       { background: rgba(245,158,11,0.1); border: 1px solid #f59e0b; }
    .risk-limited    { background: rgba(99,102,241,0.1); border: 1px solid #6366f1; }
    .risk-minimal    { background: rgba(34,197,94,0.1);  border: 1px solid #22c55e; }
    .analysis-output {
        background: #0d1220;
        border: 1px solid #0ea5e9;
        border-radius: 8px;
        padding: 1.4rem;
        font-size: 0.88rem;
        line-height: 1.7;
    }
    .history-item {
        background: #0d1220;
        border: 1px solid #1a2540;
        border-radius: 6px;
        padding: 0.7rem 1rem;
        margin-bottom: 0.5rem;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        color: #94a3b8;
    }
    .deadline-warning {
        background: rgba(245,158,11,0.1);
        border: 1px solid #f59e0b;
        border-radius: 6px;
        padding: 0.8rem 1rem;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.75rem;
        color: #f59e0b;
        margin-bottom: 1rem;
    }
    </style>
    """, unsafe_allow_html=True)

    # --- HEADER -----------------------------------------------------------
    st.markdown("""
    <div class="giustizia-header">
        <h1>\u2696\ufe0f GIUSTIZIA \u00b7 COMPLIANCE HUB</h1>
        <div class="giustizia-tagline">"La legge non dorme." \u2014 Agent 14</div>
        <div style="margin-top:0.8rem">
            <span class="regulation-badge badge-ai-act">EU AI ACT</span>
            <span class="regulation-badge badge-gdpr">GDPR</span>
            <span class="regulation-badge badge-eidas">eIDAS 2.0</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # --- DEADLINE-VARNING -------------------------------------------------
    st.markdown("""
    <div class="deadline-warning">
        \u23f0 <strong>EU AI ACT DEADLINE:</strong>
        Hogrisk-krav (Annex III) trader i kraft 2 augusti 2026 --
        mindre an 3 manader kvar.
        Forbjudna system (Art. 5) och GPAI-krav (Kap. V) galler REDAN.
    </div>
    """, unsafe_allow_html=True)

    # --- PROJEKT-VAL ------------------------------------------------------
    if project is None:
        projects = sb.table("projects").select(
            "id, name, brief_raw, tech_stack, status"
        ).eq("status", "active").execute()

        if not projects.data:
            st.warning("Inga aktiva projekt hittades.")
            return

        project_options = {p["name"]: p for p in projects.data}
        selected_name = st.selectbox(
            "VALJ PROJEKT",
            options=list(project_options.keys()),
            key="giustizia_project_select"
        )
        project = project_options[selected_name]

    st.caption(f"\U0001f4c2 **{project['name']}** \u00b7 {project.get('status', 'active')}")

    # --- SESSION STATE ----------------------------------------------------
    for key in ["giustizia_result", "giustizia_meta"]:
        if key not in st.session_state:
            st.session_state[key] = None

    # --- LAYOUT -----------------------------------------------------------
    left, right = st.columns([1, 1], gap="large")

    with left:
        st.markdown("### Konfiguration")

        # Analystyp
        st.markdown("**Analystyp**")
        analysis_type = st.radio(
            "analysis_type",
            options=list(ANALYSIS_TYPES.keys()),
            format_func=lambda x: f"{ANALYSIS_TYPES[x]['icon']} {ANALYSIS_TYPES[x]['label']}",
            label_visibility="collapsed",
            key="giustizia_analysis_type"
        )
        st.caption(ANALYSIS_TYPES[analysis_type]["description"])

        st.markdown("<br>", unsafe_allow_html=True)

        # Input
        st.markdown("**Vad ska analyseras?**")
        input_text = st.text_area(
            "input",
            label_visibility="collapsed",
            placeholder="Beskriv ditt AI-system, spec, user story, eller stall en juridisk fraga...\n\nEx: Vi bygger ett system som analyserar CV:n och rankar jobbsokande automatiskt.",
            height=180,
            key="giustizia_input"
        )

        # Projekt-kontext
        use_project_context = st.checkbox(
            "Inkludera projektkontexten automatiskt",
            value=True,
            key="giustizia_use_context"
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # Snabbreferens-riskpyramid
        with st.expander("\U0001f4ca EU AI Act Riskpyramid (snabbreferens)"):
            st.markdown("""
<div class="risk-card risk-forbidden">
\U0001f6ab <strong>FORBJUDEN</strong> -- Social scoring, subliminal manipulation,
realtids-biometri i offentliga rum, kansloigenkanning pa arbetsplatser
</div>
<div class="risk-card risk-high">
\u26a0\ufe0f <strong>HOG RISK (Annex III)</strong> -- HR/rekrytering, kreditbedomning,
biometri, kritisk infrastruktur, utbildning, rattsvasendet
<br><small>Krav trader i kraft: 2 aug 2026</small>
</div>
<div class="risk-card risk-limited">
\u2139\ufe0f <strong>BEGRANSAD RISK</strong> -- Chatbottar, deepfakes
<br><small>Krav: informera anvandaren att de interagerar med AI</small>
</div>
<div class="risk-card risk-minimal">
\u2705 <strong>MINIMAL RISK</strong> -- Majoriteten av AI-applikationer
<br><small>Inga specifika krav</small>
</div>
""", unsafe_allow_html=True)

        # Generera-knapp
        st.markdown("---")
        generate_btn = st.button(
            "\u2696\ufe0f ANALYSERA MED GIUSTIZIA",
            disabled=not input_text,
            use_container_width=True,
            type="primary",
            key="giustizia_generate"
        )

    with right:
        st.markdown("### Analys")

        if generate_btn and input_text:
            with st.spinner("Giustizia analyserar..."):
                try:
                    project_context = ""
                    if use_project_context:
                        project_context = f"""
Projektnamn: {project['name']}
Brief: {project.get('brief_raw', '')[:800]}
Tech stack: {project.get('tech_stack', '')}
"""
                    result = run_analysis(
                        analysis_type=analysis_type,
                        input_text=input_text,
                        project_context=project_context,
                        use_project_context=use_project_context,
                    )
                    st.session_state.giustizia_result = result
                    st.rerun()
                except Exception as e:
                    st.error(f"Giustizia-fel: {e}")

        if st.session_state.giustizia_result:
            result = st.session_state.giustizia_result
            meta = st.session_state.giustizia_result

            st.caption(
                f"\U0001f525 {meta['tokens_used']} tokens \u00b7 "
                f"${meta['cost_usd']:.4f} \u00b7 "
                f"{ANALYSIS_TYPES[meta['analysis_type']]['icon']} "
                f"{ANALYSIS_TYPES[meta['analysis_type']]['label']}"
            )

            st.markdown(
                f'<div class="analysis-output">{result["analysis"]}</div>',
                unsafe_allow_html=True
            )

            st.markdown("<br>", unsafe_allow_html=True)

            col_a, col_b = st.columns(2)
            with col_a:
                if st.button(
                    "\U0001f4be SPARA SOM DELIVERABLE",
                    use_container_width=True,
                    key="giustizia_save"
                ):
                    try:
                        save_analysis(
                            project_id=project["id"],
                            analysis_type=meta["analysis_type"],
                            input_text=input_text,
                            analysis_result=result["analysis"],
                            tokens_used=meta["tokens_used"],
                            cost_usd=meta["cost_usd"],
                        )
                        st.success("\u2713 Sparad som deliverable i AI Studio!")
                    except Exception as e:
                        st.error(f"Fel vid sparande: {e}")
            with col_b:
                if st.button(
                    "\U0001f5d1 RENSA",
                    use_container_width=True,
                    key="giustizia_clear"
                ):
                    st.session_state.giustizia_result = None
                    st.rerun()
        else:
            st.markdown(
                '<p style="color:#64748b;font-family:JetBrains Mono,monospace;'
                'font-size:0.8rem;margin-top:2rem">Valj analystyp och beskriv '
                'vad du vill analysera...</p>',
                unsafe_allow_html=True
            )

        # --- HISTORIK -----------------------------------------------------
        st.markdown("---")
        st.markdown("### \U0001f4dc Tidigare analyser")
        recent = get_recent_analyses(project["id"], limit=5)
        if not recent:
            st.caption("Inga tidigare analyser for detta projekt.")
        else:
            for r in recent:
                created = r["created_at"][:16].replace("T", " ")
                st.markdown(
                    f'<div class="history-item">'
                    f'<strong>{r["title"]}</strong> \u00b7 '
                    f'<span style="color:#64748b">{created}</span>'
                    f'</div>',
                    unsafe_allow_html=True
                )
