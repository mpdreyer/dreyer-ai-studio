import streamlit as st
from agents.router import route_message
from db.supabase_client import save_message, log_tokens
from agents.council import AGENTS

INTEL_CARDS = [
    {
        "title":     "GPT-4.5 släppt — vad betyder det för Claude?",
        "source":    "OpenAI Blog",
        "date":      "2026-03",
        "relevance": "Hög relevans",
        "summary":   (
            "OpenAI lanserade GPT-4.5 med förbättrad reasoning och lägre latens. "
            "Prissättningen är 20% lägre än GPT-4o för höga volymer."
        ),
    },
    {
        "title":     "EU AI Act — compliance-krav från aug 2026",
        "source":    "EU Official Journal",
        "date":      "2026-02",
        "relevance": "Hög relevans",
        "summary":   (
            "High-risk AI-system kräver dokumentation, human oversight och "
            "registrering i EU-databasen från och med 2 aug 2026."
        ),
    },
    {
        "title":     "Gemini 2.0 Pro — långt kontextfönster (2M tokens)",
        "source":    "Google DeepMind",
        "date":      "2026-01",
        "relevance": "Medium relevans",
        "summary":   (
            "Gemini 2.0 Pro stödjer 2M tokens context. Intressant för "
            "dokumentanalys och RAG-pipelines med stora dataset."
        ),
    },
    {
        "title":     "DeepSeek R2 — open source reasoning",
        "source":    "DeepSeek GitHub",
        "date":      "2026-01",
        "relevance": "Medium relevans",
        "summary":   (
            "DeepSeek R2 matchar GPT-o1 på reasoning-benchmarks till en "
            "bråkdel av kostnaden. Self-hostable."
        ),
    },
]

SCAN_PROMPT = (
    "Du är Spejaren. Gör en omvärldsskanning inom AI. "
    "Fokus: nya modeller, regulatorik (EU AI Act), "
    "forskning relevant för AI-konsulter, kostnadsnyheter. "
    "Format: 4-5 nyheter med rubrik, sammanfattning, "
    "relevans för AI-konsulter. Faktabaserad och kortfattad."
)


def render_intelligence(project: dict | None, sb):
    st.markdown("## 🔭 Intelligence")
    st.caption("Spejaren bevakar AI-världen — modeller, regulatorik, forskning.")

    project_id = project["id"] if project else None

    # ── Relevans-filter ───────────────────────────────────────────────────────
    relevance_filter = st.selectbox(
        "Filtrera relevans",
        ["Alla", "Hög relevans", "Medium relevans"],
        key="intel_filter",
    )

    # ── Senaste Spejaren-rapport ──────────────────────────────────────────────
    latest_report = None
    if project_id:
        res = (
            sb.table("chat_messages")
            .select("*")
            .eq("project_id", project_id)
            .eq("agent", "Spejaren")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
            .data
        )
        if res:
            latest_report = res[0]

    if latest_report:
        st.success("**Senaste omvärldsskanning:**")
        st.markdown(latest_report["content"])
        st.caption(f"Körd: {latest_report['created_at'][:16].replace('T', ' ')}")
    else:
        st.info("Ingen skanning körd än. Klicka 'Kör skanning' nedan för en live-rapport från Spejaren.")

    # ── Kör ny skanning ───────────────────────────────────────────────────────
    if st.button("🔭 Kör ny omvärldsskanning", type="primary"):
        agent = AGENTS["Spejaren"]
        with st.spinner("Spejaren skannar AI-världen…"):
            reply, tokens, cost = route_message(
                "Spejaren",
                [{"role": "user", "content": SCAN_PROMPT}],
                max_tokens=800,
            )
        if project_id:
            save_message(
                sb, project_id, "assistant", reply,
                agent="Spejaren", model=agent["model"],
                tokens=tokens, cost=cost,
            )
            log_tokens(sb, project_id, "Spejaren", agent["model"],
                       tokens // 2, tokens - tokens // 2, cost)
        st.success("**Spejaren rapporterar:**")
        st.markdown(reply)
        st.rerun()

    st.markdown("---")
    st.markdown("### Nyhetskort")

    # ── Statiska intel-kort ───────────────────────────────────────────────────
    filtered_cards = [
        c for c in INTEL_CARDS
        if relevance_filter == "Alla" or c["relevance"] == relevance_filter
    ]

    if not filtered_cards:
        st.markdown(
            '<div style="color:#5a5a72;font-size:13px;">Inga kort matchar filtret.</div>',
            unsafe_allow_html=True,
        )

    for i, card in enumerate(filtered_cards):
        rel_color = "#10b981" if card["relevance"] == "Hög relevans" else "#f59e0b"
        st.markdown(
            f'<div style="background:#1e2130;border:1px solid rgba(255,255,255,0.07);'
            f'border-left:3px solid {rel_color};border-radius:8px;padding:14px 16px;margin-bottom:8px;">'
            f'<div style="font-weight:600;color:#e8e8f0;margin-bottom:4px;">{card["title"]}</div>'
            f'<div style="font-size:11px;color:#9090a8;margin-bottom:8px;">'
            f'{card["source"]} · {card["date"]} · '
            f'<span style="color:{rel_color};">{card["relevance"]}</span></div>'
            f'<div style="font-size:13px;color:#c0c0d0;">{card["summary"]}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        if st.button("Analysera", key=f"intel_analyze_{i}"):
            prompt = (
                f"{card['title']}\n\n{card['summary']}\n\n"
                "Vad innebär detta för pågående AI-konsultprojekt?"
            )
            with st.spinner("Spejaren analyserar…"):
                reply, _tokens, _cost = route_message(
                    "Spejaren",
                    [{"role": "user", "content": prompt}],
                    max_tokens=300,
                )
            st.info(f"**Spejaren:** {reply}")
