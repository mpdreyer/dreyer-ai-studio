import streamlit as st


def get_active_view() -> str:
    return st.session_state.get("ss_active_view", "portfolio")


def set_active_view(view: str) -> None:
    st.session_state["ss_active_view"] = view


def get_active_project_id() -> str | None:
    return st.session_state.get("ss_active_project_id")


def set_active_project_id(project_id: str) -> None:
    st.session_state["ss_active_project_id"] = project_id


def clear_active_project() -> None:
    st.session_state.pop("ss_active_project_id", None)


def get_selected_agent() -> str:
    return st.session_state.get("ss_selected_agent", "Architetto")


def set_selected_agent(agent: str) -> None:
    st.session_state["ss_selected_agent"] = agent
