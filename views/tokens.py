import streamlit as st


def render_tokens(project: dict | None, sb):
    st.subheader("🪙 Token-användning")
    if not project:
        st.info("Skapa ett projekt för att se token-statistik.")
        return
    res = sb.table("token_log").select("*").eq("project_id", project["id"]).order("logged_at", desc=True).execute()
    rows = res.data or []
    if not rows:
        st.info("Ingen token-logg ännu.")
        return
    import pandas as pd
    df = pd.DataFrame(rows)[["agent", "input_tokens", "output_tokens", "logged_at"]]
    st.dataframe(df, use_container_width=True)
    st.metric("Totalt input", sum(r["input_tokens"] for r in rows))
    st.metric("Totalt output", sum(r["output_tokens"] for r in rows))
