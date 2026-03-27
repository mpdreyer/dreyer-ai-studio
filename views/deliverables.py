import streamlit as st


def render_deliverables(project: dict | None, sb):
    st.subheader("📦 Leverabler")
    if not project:
        st.info("Skapa ett projekt för att se leverabler.")
        return
    res = sb.table("deliverables").select("*").eq("project_id", project["id"]).order("created_at", desc=True).execute()
    items = res.data or []
    if not items:
        st.info("Inga leverabler ännu.")
        return
    for item in items:
        with st.expander(f"{item.get('title','Utan titel')} — {item.get('status','?')}"):
            st.markdown(item.get("content", ""))
