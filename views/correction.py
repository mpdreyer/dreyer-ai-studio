import json
import streamlit as st
from agents.council import AGENTS, agent_list
from agents.router import route_message


AGENTS_DEMO = [
    {"agent": "Kontrakto", "model": "GPT-4o",      "pct": 72, "trend": "↑", "note": "Tonalitet"},
    {"agent": "Narratrix",  "model": "Claude",      "pct": 54, "trend": "→", "note": "Längd"},
    {"agent": "Codex",      "model": "Claude Code", "pct": 28, "trend": "↓", "note": "Förbättras"},
    {"agent": "Logica",     "model": "GPT-4o",      "pct": 19, "trend": "↓", "note": "Bra"},
    {"agent": "Architetto", "model": "Claude",      "pct": 14, "trend": "↓", "note": "Bra"},
    {"agent": "Datatjej",   "model": "Gemini",      "pct":  8, "trend": "↓", "note": "Utmärkt"},
]


def _bar(pct: int, color: str) -> str:
    return (
        f'<div style="background:rgba(255,255,255,0.06);border-radius:4px;height:8px;'
        f'width:100%;margin-top:4px;">'
        f'<div style="background:{color};width:{pct}%;height:8px;border-radius:4px;"></div>'
        f'</div>'
    )


def render_correction(project: dict | None, sb):
    st.markdown("## 📐 Correction Delta")
    st.caption("Mäter var du korrigerar agenternas output — identifierar svagheter per agent.")

    project_id = project["id"] if project else None

    # ── Hämta data ────────────────────────────────────────────────────────────
    corrections = []
    if project_id:
        corrections = (
            sb.table("corrections")
            .select("*")
            .eq("project_id", project_id)
            .order("created_at", desc=True)
            .execute()
            .data or []
        )

    # Aggregera
    summary: dict = {}
    for c in corrections:
        agent = c.get("agent", "Okänd")
        if agent not in summary:
            summary[agent] = {"count": 0, "types": []}
        summary[agent]["count"] += 1
        if c.get("delta_type"):
            summary[agent]["types"].append(c["delta_type"])

    using_demo = len(corrections) == 0

    # ── Visa correction rate ──────────────────────────────────────────────────
    if using_demo:
        st.markdown(
            '<div style="font-size:11px;color:#f59e0b;margin-bottom:12px;">'
            '⚠ Demo-data · Correction Delta aktiveras när du registrerar korrigeringar nedan</div>',
            unsafe_allow_html=True,
        )
        rows = AGENTS_DEMO
    else:
        total = len(corrections)
        rows = []
        for agent_name, data in sorted(summary.items(), key=lambda x: -x[1]["count"]):
            pct = round(data["count"] / total * 100)
            most_common = max(set(data["types"]), key=data["types"].count) if data["types"] else "—"
            rows.append({"agent": agent_name, "pct": pct, "trend": "→", "note": most_common})

    for row in rows:
        pct   = row["pct"]
        color = "#ef4444" if pct >= 60 else ("#f59e0b" if pct >= 30 else "#10b981")
        agent_data = AGENTS.get(row["agent"], {})
        model = row.get("model") or agent_data.get("model_display", "—")

        st.markdown(
            f'<div style="background:#1e2130;border:1px solid rgba(255,255,255,0.07);'
            f'border-radius:8px;padding:14px 16px;margin-bottom:8px;">'
            f'<div style="display:flex;justify-content:space-between;align-items:center;">'
            f'<div>'
            f'<span style="font-weight:600;color:#e8e8f0;">{row["agent"]}</span>'
            f'<span style="font-size:10px;color:#5a5a72;margin-left:8px;font-family:monospace;">{model}</span>'
            f'</div>'
            f'<div style="text-align:right;">'
            f'<span style="font-size:18px;font-weight:700;color:{color};">{pct}%</span>'
            f'<span style="font-size:14px;margin-left:6px;">{row["trend"]}</span>'
            f'<div style="font-size:10px;color:#9090a8;">{row["note"]}</div>'
            f'</div>'
            f'</div>'
            f'{_bar(pct, color)}'
            f'</div>',
            unsafe_allow_html=True,
        )

    # ── Registrera korrigering ────────────────────────────────────────────────
    st.markdown("---")
    with st.expander("＋ Registrera korrigering manuellt"):
        with st.form("correction_form"):
            agent_sel  = st.selectbox("Agent", agent_list())
            delta_type = st.selectbox(
                "Typ av korrigering",
                ["Tonalitet", "Längd", "Faktafel", "Struktur", "Ton", "Annat"],
            )
            original  = st.text_area("Agentens svar", height=80)
            corrected = st.text_area("Ditt korrigerade svar", height=80)
            submitted = st.form_submit_button("Spara korrigering")

        if submitted:
            if not project_id:
                st.warning("Välj ett aktivt projekt för att spara korrigeringar.")
            else:
                sb.table("corrections").insert({
                    "project_id": project_id,
                    "agent":      agent_sel,
                    "delta_type": delta_type,
                    "original":   original,
                    "corrected":  corrected,
                }).execute()
                st.success("Korrigering sparad.")
                st.rerun()

    # ── Gemma-analys ──────────────────────────────────────────────────────────
    if corrections and len(corrections) >= 3:
        st.markdown("---")
        if st.button("🔍 Gemma analyserar mönstret"):
            prompt = (
                f"Du är Gemma, data analyst. Analysera dessa {len(corrections)} korrigeringar "
                f"och identifiera mönster. Vilken agent behöver förbättras mest och hur? "
                f"Data: {json.dumps(summary, ensure_ascii=False)}"
            )
            with st.spinner("Gemma analyserar…"):
                reply, _tokens, _cost = route_message(
                    "Datatjej",
                    [{"role": "user", "content": prompt}],
                    max_tokens=400,
                )
            st.info(f"**Gemma:** {reply}")
