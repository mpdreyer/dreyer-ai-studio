import streamlit as st
from supabase import create_client, Client
from functools import lru_cache
from core.state import get_active_project_id


@st.cache_resource
def get_supabase() -> Client:
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"],
    )


def get_active_project(sb: Client) -> dict | None:
    pid = get_active_project_id()
    if not pid:
        return None
    res = sb.table("projects").select("*").eq("id", pid).single().execute()
    return res.data


def get_tasks(sb: Client, project_id: str) -> list:
    res = sb.table("tasks").select("*").eq("project_id", project_id).order("phase").execute()
    return res.data or []


def get_deliverables(sb: Client, project_id: str) -> list:
    res = sb.table("deliverables").select("*").eq("project_id", project_id).order("created_at").execute()
    return res.data or []


def get_chat_history(sb: Client, project_id: str, limit: int = 50) -> list:
    res = sb.table("chat_messages").select("*").eq("project_id", project_id).order("created_at", desc=True).limit(limit).execute()
    return list(reversed(res.data or []))


def save_message(sb: Client, project_id: str, role: str, content: str,
                 agent: str = None, model: str = None, tokens: int = 0, cost: float = 0.0):
    sb.table("chat_messages").insert({
        "project_id":  project_id,
        "role":        role,
        "content":     content,
        "agent":       agent,
        "model":       model,
        "tokens_used": tokens,
        "cost_usd":    cost,
    }).execute()


def log_tokens(sb: Client, project_id: str, agent: str, model: str,
               tokens_in: int, tokens_out: int, cost: float):
    sb.table("token_log").insert({
        "project_id": project_id,
        "agent":      agent,
        "model":      model,
        "tokens_in":  tokens_in,
        "tokens_out": tokens_out,
        "cost_usd":   cost,
    }).execute()
    # Uppdatera projekt-total
    proj = sb.table("projects").select("token_used").eq("id", project_id).single().execute()
    if proj.data:
        new_total = (proj.data["token_used"] or 0) + cost
        sb.table("projects").update({"token_used": round(new_total, 4)}).eq("id", project_id).execute()


def get_token_summary(sb: Client, project_id: str) -> list:
    res = sb.table("token_log").select("agent, model, tokens_in, tokens_out, cost_usd").eq("project_id", project_id).execute()
    data = res.data or []
    # Aggregera per agent
    summary = {}
    for row in data:
        key = row["agent"]
        if key not in summary:
            summary[key] = {"agent": key, "model": row["model"], "tokens": 0, "cost": 0.0}
        summary[key]["tokens"] += row["tokens_in"] + row["tokens_out"]
        summary[key]["cost"]   += row["cost_usd"]
    return sorted(summary.values(), key=lambda x: x["cost"], reverse=True)
