import json
import streamlit as st
from agents.router import route_message, build_project_context
from agents.council import AGENTS
from db.supabase_client import get_token_summary, save_message, log_tokens


def render_analyze(project: dict | None, sb):
    st.markdown("## 🔍 Projektanalys")
    st.caption("Hela rådet analyserar projektet — status, risker, ekonomi och säkerhet.")

    if not project:
        st.info("Inget aktivt projekt. Öppna ett projekt från DTSM Portfolio.")
        return

    project_id = project["id"]
    ctx        = build_project_context(project)

    if st.button("🚀 Kör full rådsanalys", type="primary"):
        results = {}

        with st.spinner("Architetto bedömer projektstatus…"):
            results["architetto"] = route_message(
                "Architetto",
                [{"role": "user", "content":
                  f"Ge en ärlig statusbedömning av projektet:\n{ctx}\n\n"
                  "Vad är bra? Vad är oroande? Vad är nästa steg?"}],
                max_tokens=400,
            )

        with st.spinner("Risico identifierar risker…"):
            results["risico"] = route_message(
                "Risico",
                [{"role": "user", "content":
                  f"Identifiera de tre största riskerna i detta projekt:\n{ctx}\n\n"
                  "Var specifik och konstruktiv. Rangordna HÖG/MEDIUM/LÅG."}],
                max_tokens=300,
            )

        with st.spinner("Datatjej analyserar token-ekonomin…"):
            token_data = get_token_summary(sb, project_id)
            results["datatjej"] = route_message(
                "Datatjej",
                [{"role": "user", "content":
                  f"Analysera token-förbrukningen för projektet:\n"
                  f"{json.dumps(token_data, ensure_ascii=False)}\n\n"
                  "Är vi på rätt spår kostnadsmässigt? Finns avvikelser?"}],
                max_tokens=300,
            )

        with st.spinner("Diavolo granskar säkerheten…"):
            results["diavolo"] = route_message(
                "Diavolo",
                [{"role": "user", "content":
                  f"Granska projektet ur säkerhetsperspektiv:\n{ctx}\n\n"
                  "Finns det säkerhetsrisker, bias-risker eller etikproblem? "
                  "Rangordna severity HÖG/MEDIUM/LÅG."}],
                max_tokens=300,
            )

        st.markdown("---")

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**🏛️ Architetto — Projektstatus**")
            st.info(results["architetto"][0])

            st.markdown("**📊 Datatjej — Token-ekonomi**")
            st.info(results["datatjej"][0])

        with col2:
            st.markdown("**⚠️ Risico — Risker**")
            st.warning(results["risico"][0])

            st.markdown("**🔴 Diavolo — Säkerhet**")
            st.error(results["diavolo"][0])

        # Spara analysen som sammansatt meddelande
        full_analysis = (
            f"**Rådsanalys — {project.get('name','—')}**\n\n"
            f"**Architetto:** {results['architetto'][0]}\n\n"
            f"**Risico:** {results['risico'][0]}\n\n"
            f"**Datatjej:** {results['datatjej'][0]}\n\n"
            f"**Diavolo:** {results['diavolo'][0]}"
        )
        total_tokens = sum(r[1] for r in results.values())
        total_cost   = sum(r[2] for r in results.values())
        save_message(sb, project_id, "assistant", full_analysis,
                     agent="Architetto", model=AGENTS["Architetto"]["model"],
                     tokens=total_tokens, cost=total_cost)
        st.caption(f"Analys sparad · {total_tokens:,} tokens · {total_cost:.4f} USD")

    else:
        st.markdown(
            '<div style="color:#5a5a72;font-size:13px;padding:20px 0;">'
            'Klicka "Kör full rådsanalys" för att aktivera Architetto, Risico, '
            'Datatjej och Diavolo samtidigt.</div>',
            unsafe_allow_html=True,
        )
