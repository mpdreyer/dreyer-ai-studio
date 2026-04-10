"""
Dreyer AI Studio — Nytt projekt-modal
Rikt brief-formulär med textinmatning och filuppladdning.
"""

import streamlit as st
from datetime import date, timedelta


def _extract_text_from_file(uploaded_file) -> tuple[str, str]:
    """Extraherar text ur uppladdad fil. Returnerar (text, felmeddelande)."""
    name = uploaded_file.name.lower()

    if name.endswith(".txt") or name.endswith(".md"):
        return uploaded_file.read().decode("utf-8"), ""

    if name.endswith(".pdf"):
        try:
            import PyPDF2
            reader = PyPDF2.PdfReader(uploaded_file)
            text = "\n".join(
                page.extract_text() or "" for page in reader.pages
            )
            return text.strip(), ""
        except ImportError:
            return "", "PDF-stöd kräver: pip install PyPDF2"

    if name.endswith(".docx"):
        try:
            import docx
            doc = docx.Document(uploaded_file)
            text = "\n".join(p.text for p in doc.paragraphs)
            return text.strip(), ""
        except ImportError:
            return "", "DOCX-stöd kräver: pip install python-docx"

    return "", f"Filtypen '{name.split('.')[-1]}' stöds ej."


def _call_architetto(sb, project_id: str, project_name: str, brief_text: str):
    """Anropar Architetto för att analysera briefen och sparar svaret."""
    from agents.router import route_message
    from agents.council import AGENTS
    from db.supabase_client import save_message, log_tokens

    agent_name = "Architetto"
    agent = AGENTS[agent_name]

    prompt = (
        f"Nytt projekt: **{project_name}**\n\n"
        f"Brief:\n{brief_text}\n\n"
        "Analysera briefen och ge:\n"
        "1. Ditt intryck av scope och komplexitet\n"
        "2. 3–5 kritiska frågor som bör besvaras innan arbetet startar\n"
        "3. Förslag på första prioriterade steg\n"
        "4. Eventuella risker du ser redan nu"
    )

    messages = [{"role": "user", "content": prompt}]
    content, total_tokens, cost = route_message(agent_name, messages, max_tokens=1024)

    save_message(
        sb, project_id, "assistant", content,
        agent=agent_name, model=agent["model"],
        tokens=total_tokens, cost=cost,
    )
    log_tokens(
        sb, project_id, agent_name, agent["model"],
        tokens_in=total_tokens // 2,
        tokens_out=total_tokens - total_tokens // 2,
        cost=cost,
    )


def render_new_project_modal(sb):
    st.subheader("🏛️ Nytt projekt")
    st.caption("Fyll i ett rikt brief så kan rådet börja arbeta direkt.")

    # ── Sektion 1: Grundinfo ─────────────────────────────────────────────
    st.markdown("**Grundinfo**")
    col1, col2 = st.columns(2)
    with col1:
        name   = st.text_input("Projektnamn *", placeholder="AI POC Kund X")
        client = st.text_input("Kund", placeholder="Kund AB")
    with col2:
        budget   = st.number_input("Token-budget (USD)", value=20.0, min_value=1.0, step=5.0)
        deadline = st.date_input("Deadline", value=date.today() + timedelta(days=30))
        deploy   = st.selectbox("Deployment-läge", ["cloud", "hybrid", "airgap"])

    st.divider()

    # ── Sektion 2: Brief (flikar) ─────────────────────────────────────────
    st.markdown("**Projektbeskrivning**")
    tab_write, tab_upload = st.tabs(["✍️ Skriv brief", "📎 Ladda upp brief"])

    description = requirements = constraints = success_criteria = brief_raw = ""

    with tab_write:
        description = st.text_area(
            "Projektbeskrivning",
            height=120,
            placeholder="Beskriv vad AI-lösningen ska lösa, för vem och varför...",
            key="np_description",
        )
        requirements = st.text_area(
            "Krav och önskemål",
            height=100,
            placeholder="Funktionella krav, tekniska krav, integrationer...",
            key="np_requirements",
        )
        constraints = st.text_area(
            "Begränsningar",
            height=80,
            placeholder="Budget, tidplan, tekniska begränsningar, compliance...",
            key="np_constraints",
        )
        success_criteria = st.text_area(
            "Success criteria",
            height=80,
            placeholder="Hur vet vi att projektet är lyckat? Mätbara mål...",
            key="np_success",
        )

    with tab_upload:
        uploaded = st.file_uploader(
            "Ladda upp brief-dokument",
            type=["pdf", "txt", "md", "docx"],
            help="PDF, TXT, Markdown eller Word-dokument",
        )
        if uploaded:
            text, err = _extract_text_from_file(uploaded)
            if err:
                st.error(err)
            elif text:
                brief_raw = text
                with st.expander("Förhandsgranskning (första 500 tecken)", expanded=True):
                    st.text(text[:500] + ("…" if len(text) > 500 else ""))
                st.success(f"✓ {len(text):,} tecken inlästa från **{uploaded.name}**")
            else:
                st.warning("Filen verkar vara tom.")

    st.divider()

    # ── Sektion 3: Architetto-analys ──────────────────────────────────────
    ask_architetto = st.checkbox(
        "Låt Architetto analysera briefen och föreslå scope",
        value=True,
        help="Architetto läser briefen och ger kritiska frågor och prioriterade steg.",
    )

    # ── Knappar ───────────────────────────────────────────────────────────
    st.divider()
    col_save, col_cancel = st.columns([1, 4])

    with col_save:
        save_clicked = st.button("🏛️ Skapa projekt", type="primary", use_container_width=True)
    with col_cancel:
        if st.button("Avbryt", use_container_width=False):
            st.session_state.pop("show_new_project", None)
            st.rerun()

    if save_clicked:
        if not name.strip():
            st.error("Projektnamn är obligatoriskt.")
            return

        # Sätt ihop brief_raw om inte fil laddades upp
        combined_brief = brief_raw or "\n\n".join(filter(None, [
            f"Beskrivning:\n{description}" if description else "",
            f"Krav:\n{requirements}" if requirements else "",
            f"Begränsningar:\n{constraints}" if constraints else "",
            f"Success criteria:\n{success_criteria}" if success_criteria else "",
        ]))

        with st.spinner("Sparar projekt…"):
            res = sb.table("projects").insert({
                "name":             name.strip(),
                "client":           client.strip() or None,
                "token_budget":     budget,
                "deadline":         str(deadline),
                "deployment_mode":  deploy,
                "status":           "active",
                "description":      description or None,
                "requirements":     requirements or None,
                "constraints":      constraints or None,
                "success_criteria": success_criteria or None,
                "brief_raw":        combined_brief or None,
            }).execute()

        if not res.data:
            st.error("Kunde inte spara projektet. Kontrollera Supabase-anslutningen.")
            return

        project_id = res.data[0]["id"]
        st.session_state["active_project_id"] = project_id

        if ask_architetto and combined_brief.strip():
            with st.spinner("Architetto analyserar briefen…"):
                try:
                    _call_architetto(sb, project_id, name.strip(), combined_brief)
                except Exception as e:
                    st.warning(f"Architetto-analys misslyckades: {e}")

        st.success(f"✓ Projekt **{name}** skapat!")
        st.session_state.pop("show_new_project", None)
        st.rerun()
