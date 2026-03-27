import streamlit as st
from agents.router import route_message, build_project_context
from db.supabase_client import save_message, log_tokens
from agents.council import AGENTS


def render_roi(project: dict | None, sb):
    st.subheader("💰 ROI-kalkylator")
    st.caption("Externt kundverktyg · Narratrix (Claude) exporterar till rapport")

    project_id = project["id"] if project else None
    ctx = build_project_context(project) if project else ""

    col1, col2 = st.columns(2)

    with col1:
        hours   = st.number_input("Timmar/vecka · manuell process", min_value=1, max_value=500, value=40)
        staff   = st.number_input("Antal anställda som berörs", min_value=1, max_value=1000, value=8)
        cost_h  = st.number_input("Snittkostnad (kr/h)", min_value=100, max_value=5000, value=650)

    with col2:
        eff     = st.slider("Förväntad AI-effektivisering (%)", 10, 90, 65)
        invest  = st.number_input("POC-investering (kr)", min_value=10000, max_value=2000000, value=120000, step=10000)
        err_rate = st.slider("Felfrekvens idag (%)", 0, 50, 12)

    # Beräkning
    annual_cost = hours * staff * cost_h * 52
    saving      = annual_cost * (eff / 100)
    payback_months = invest / saving * 12 if saving > 0 else 0
    roi_pct     = ((saving - invest) / invest * 100) if invest > 0 else 0

    def fmt(v):
        if v >= 1_000_000:
            return f"{v/1_000_000:.1f} Mkr"
        return f"{v/1000:.0f}k kr"

    st.divider()
    st.markdown("**Beräknat utfall — år 1**")
    c1, c2, c3 = st.columns(3)
    c1.metric("Besparing/år", fmt(saving))
    c2.metric("Återbetalningstid", f"{payback_months:.1f} mån")
    c3.metric("ROI år 1", f"{roi_pct:.0f}%")

    st.divider()

    col_a, col_b = st.columns(2)

    with col_a:
        if st.button("📄 Generera kundrapport · Narratrix", use_container_width=True):
            prompt = f"""Generera en professionell en-sidig ROI-rapport för kunden. 
Skriv på svenska, beslutsfattarnivå. Inga tekniska detaljer.

Underlag:
- Manuell processtid: {hours} timmar/vecka × {staff} anställda
- Snittkostnad: {cost_h} kr/h  
- AI-effektivisering: {eff}%
- Aktuell felfrekvens: {err_rate}%
- POC-investering: {invest:,} kr

Beräknat utfall:
- Besparing: {fmt(saving)}/år
- Återbetalningstid: {payback_months:.1f} månader
- ROI år 1: {roi_pct:.0f}%

Rapporten ska innehålla: Sammanfattning, Nuläge, AI-lösningens värde, Investering & ROI, Rekommendation.
Avsluta med en tydlig uppmaning till beslut."""

            with st.spinner("Narratrix skriver rapport..."):
                reply, tokens, cost = route_message(
                    "Narratrix",
                    [{"role": "user", "content": prompt}],
                    project_context=ctx,
                    max_tokens=1200,
                )

            if project_id:
                save_message(sb, project_id, "assistant", reply,
                           agent="Narratrix", model=AGENTS["Narratrix"]["model"],
                           tokens=tokens, cost=cost)
                log_tokens(sb, project_id, "Narratrix", AGENTS["Narratrix"]["model"],
                          tokens//2, tokens//2, cost)

            st.markdown("---")
            st.markdown("**Narratrix — Kundrapport:**")
            st.markdown(reply)

    with col_b:
        if st.button("💬 Förbered invändningar · Kontrakto", use_container_width=True):
            prompt = f"""Kunden har fått en ROI-kalkyl som visar {fmt(saving)}/år i besparing 
och {payback_months:.1f} månaders återbetalningstid på en investering på {invest:,} kr.

Vilka är de tre vanligaste invändningarna en kund i denna situation brukar ha?
Ge ett förberett svar på varje invändning. Kort och säljande."""

            with st.spinner("Kontrakto förbereder..."):
                reply, tokens, cost = route_message(
                    "Kontrakto",
                    [{"role": "user", "content": prompt}],
                    project_context=ctx,
                    max_tokens=600,
                )
            st.markdown("**Kontrakto — Invändningar & svar:**")
            st.markdown(reply)
