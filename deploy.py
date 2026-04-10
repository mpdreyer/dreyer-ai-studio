import streamlit as st
from agents.router import route_message, build_project_context
from db.supabase_client import save_message, log_tokens
from agents.council import AGENTS

DEPLOY_MODES = {
    "cloud":   ("☁️ Cloud",    "Anthropic / OpenAI API. Snabbast, lägst startkostnad."),
    "hybrid":  ("⇄ Hybrid",   "Känslig data lokalt. Metadata kan gå till molnet."),
    "airgap":  ("🔒 Air-gapped", "Noll extern trafik. Komplett on-prem installation."),
}

MODEL_MAPPING = {
    "cloud":  {"Claude Sonnet": "Anthropic API", "GPT-4o": "OpenAI API", "Gemini": "Google API", "DeepSeek": "DeepSeek API"},
    "hybrid": {"Claude Sonnet": "Anthropic API", "GPT-4o": "Azure Private Link", "Gemini": "Vertex AI VPC", "DeepSeek": "Lokal"},
    "airgap": {"Claude Sonnet": "Mistral 7B (Ollama)", "GPT-4o": "Llama 3.1 8B (Ollama)", "Gemini": "Phi-3 Medium (Ollama)", "DeepSeek": "DeepSeek-Coder (lokal)"},
}


def render_deploy(project: dict | None, sb):
    st.subheader("🔒 Deployment-konfigurator")
    st.caption("Välj kundmiljö · agenter och modeller anpassas automatiskt")

    project_id = project["id"] if project else None
    ctx = build_project_context(project) if project else ""

    current_mode = project.get("deployment_mode", "cloud") if project else "cloud"

    # Välj läge
    mode_cols = st.columns(3)
    selected_mode = current_mode

    for col, (mode_id, (label, desc)) in zip(mode_cols, DEPLOY_MODES.items()):
        with col:
            active = current_mode == mode_id
            with st.container(border=True):
                st.markdown(f"**{label}**")
                st.caption(desc)
                if st.button("Välj" if not active else "✅ Aktiv", key=f"deploy_{mode_id}",
                           disabled=active, use_container_width=True):
                    if project_id:
                        sb.table("projects").update({"deployment_mode": mode_id}).eq("id", project_id).execute()
                    st.rerun()

    st.divider()

    # Modell-mapping
    mapping = MODEL_MAPPING.get(current_mode, MODEL_MAPPING["cloud"])
    st.markdown(f"**Modell-mapping — {DEPLOY_MODES[current_mode][0]}**")

    cols = st.columns(4)
    for col, (model, target) in zip(cols, mapping.items()):
        with col:
            color = "🟢" if "API" in target and current_mode == "cloud" else "🟡" if current_mode == "hybrid" else "🔒"
            st.metric(model, target, color)

    if current_mode == "airgap":
        st.warning("Air-gapped: Spejaren degraderas till lokal RSS-bevakning. Ingen extern internettrafik.")
        st.info("Rekommenderad GPU: NVIDIA A10G (24 GB VRAM) · Est. 18 000 kr/mån vs 42 000 kr/mån moln")

    st.divider()

    # Scalero-installationsguide
    if st.button("📋 Generera installationsguide · Scalero"):
        prompt = f"""Generera en steg-för-steg installationsguide för Dreyer AI Studio 
i {DEPLOY_MODES[current_mode][0]}-läge.

Inkludera:
1. Förutsättningar (hårdvara, mjukvara, API-nycklar)
2. Installationssteg med konkreta kommandon
3. Konfiguration av miljövariabler
4. Validering att systemet fungerar
5. Felsökning av vanliga problem

{"För air-gapped: inkludera Ollama-setup och modell-nedladdning." if current_mode == "airgap" else ""}
Skriv konkreta bash-kommandon där tillämpligt."""

        with st.spinner("Scalero skriver guide..."):
            reply, tokens, cost = route_message(
                "Scalero",
                [{"role": "user", "content": prompt}],
                project_context=ctx,
                max_tokens=1000,
            )

        if project_id:
            save_message(sb, project_id, "assistant", reply,
                       agent="Scalero", model=AGENTS["Scalero"]["model"],
                       tokens=tokens, cost=cost)

        st.markdown("**Scalero — Installationsguide:**")
        st.markdown(reply)
