"""
Esecutore — Execution Specialist
================================
Genererar exekverbara prompts for Claude Code och Codex CLI
baserat pa projekt-kontext fran Dreyer AI Studio.

"Basta parlare. Facciamo."
"""

import anthropic
import streamlit as st
from datetime import datetime
from agents.esecutore_templates import get_template
from agents.council import get_agent
from db.supabase_client import get_supabase


def build_project_context(
    project: dict,
    sb,
    include_brief: bool = True,
    include_success_criteria: bool = True,
    include_tech_stack: bool = True,
    include_deliverables: bool = True,
    include_notebooklm: bool = False,
) -> str:
    """Bygg en strukturerad kontext-string baserat pa flaggorna."""

    parts = [f"# PROJEKT: {project['name']}", f"Status: {project.get('status', 'active')}", ""]

    if include_brief and project.get("brief_raw"):
        parts.append("## BRIEF")
        parts.append(project["brief_raw"])
        parts.append("")

    if include_tech_stack and project.get("tech_stack"):
        stack = project["tech_stack"]
        if isinstance(stack, list):
            stack_str = ", ".join(stack)
        else:
            stack_str = str(stack)
        parts.append("## TECH STACK")
        parts.append(stack_str)
        parts.append("")

    if include_success_criteria:
        try:
            sc = sb.table("deliverables").select("content").eq("project_id", project["id"]).eq("doc_type", "success_criteria").execute()
            if sc.data:
                parts.append("## SUCCESS CRITERIA")
                parts.append(sc.data[0]["content"])
                parts.append("")
        except Exception:
            pass

    if include_deliverables:
        try:
            dlv = sb.table("deliverables").select("title, owner_agent, content").eq("project_id", project["id"]).execute()
            if dlv.data:
                parts.append("## DELIVERABLES")
                for d in dlv.data:
                    parts.append(f"### {d['title']} (by {d['owner_agent']})")
                    parts.append(d["content"][:1500])
                    parts.append("")
        except Exception:
            pass

    if include_notebooklm:
        try:
            nb = sb.table("app_notebooks").select("notebook_url").eq("app_name", project["name"].lower().replace(" ", "-")).execute()
            if nb.data:
                parts.append("## NOTEBOOKLM")
                parts.append(nb.data[0]["notebook_url"])
                parts.append("")
        except Exception:
            pass

    return "\n".join(parts)


def generate_execution_prompt(
    project: dict,
    prompt_type: str,
    target: str,
    user_context: str = "",
    include_brief: bool = True,
    include_success_criteria: bool = True,
    include_tech_stack: bool = True,
    include_deliverables: bool = True,
    include_notebooklm: bool = False,
) -> dict:
    """
    Huvudfunktionen -- generera en exekverbar prompt.

    Returns:
        dict med {prompt: str, tokens_used: int, cost_usd: float}
    """

    sb = get_supabase()

    # 1. Hamta Esecutore-agenten for system prompt
    esecutore = get_agent("Esecutore")
    base_system_prompt = esecutore.get("system", "")

    # 2. Hamta mall
    template_instructions = get_template(prompt_type, target)

    # 3. Bygg projekt-kontext
    project_context = build_project_context(
        project, sb,
        include_brief, include_success_criteria,
        include_tech_stack, include_deliverables, include_notebooklm
    )

    # 4. Bygg system prompt
    full_system_prompt = f"""{base_system_prompt}

---
SPECIFIKA INSTRUKTIONER FOR DENNA PROMPT:
{template_instructions}

---
TARGET: {target}
PROMPT TYPE: {prompt_type}
"""

    # 5. Bygg user message
    user_message = f"""Generera den exekverbara prompten baserat pa projekt-kontexten nedan.

{project_context}

EXTRA KONTEXT FRAN ANVANDAREN:
{user_context if user_context else "(ingen extra kontext)"}

---
Generera nu prompten. Output ska vara DIREKT KOPIERINGSBAR -- inga forklaringar, ingen meta-kommentar.
Bara prompten sjalv, redo att klistras in i {target}.
"""

    # 6. Anropa Claude
    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=8000,
        system=full_system_prompt,
        messages=[{"role": "user", "content": user_message}]
    )

    generated_prompt = response.content[0].text
    tokens_used = response.usage.input_tokens + response.usage.output_tokens

    # Sonnet 4.5 pricing: $3/M input, $15/M output
    cost_usd = (response.usage.input_tokens * 3 / 1_000_000) + (response.usage.output_tokens * 15 / 1_000_000)

    return {
        "prompt": generated_prompt,
        "tokens_used": tokens_used,
        "cost_usd": round(cost_usd, 4),
    }


def save_execution_prompt(
    project_id: str,
    prompt_type: str,
    target: str,
    user_context: str,
    generated_prompt: str,
    tokens_used: int,
    cost_usd: float,
    include_flags: dict,
) -> str:
    """Spara genererad prompt i Supabase. Returnerar prompt_id."""

    sb = get_supabase()

    data = {
        "project_id": project_id,
        "prompt_type": prompt_type,
        "target": target,
        "user_context": user_context,
        "generated_prompt": generated_prompt,
        "tokens_used": tokens_used,
        "cost_usd": cost_usd,
        "status": "generated",
        **include_flags,
    }

    result = sb.table("execution_prompts").insert(data).execute()
    return result.data[0]["id"]


def mark_as_executed(prompt_id: str, notes: str = "") -> bool:
    """Markera en prompt som exekverad."""
    sb = get_supabase()
    sb.table("execution_prompts").update({
        "status": "executed",
        "executed_at": datetime.utcnow().isoformat(),
        "completion_notes": notes,
    }).eq("id", prompt_id).execute()
    return True


def get_recent_prompts(project_id: str, limit: int = 5) -> list:
    """Hamta de senaste genererade prompts for ett projekt."""
    sb = get_supabase()
    result = sb.table("execution_prompts").select(
        "id, prompt_type, target, status, created_at, executed_at"
    ).eq("project_id", project_id).order("created_at", desc=True).limit(limit).execute()
    return result.data or []
