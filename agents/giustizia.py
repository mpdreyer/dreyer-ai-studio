"""
Giustizia -- Legal Counsel . Agent 14
=====================================
Compliance-analys for EU AI Act, GDPR och eIDAS 2.0.

"La legge non dorme."
"""

import anthropic
import streamlit as st
from agents.council import get_agent
from agents.giustizia_knowledge import get_relevant_knowledge, get_knowledge
from db.supabase_client import get_supabase


ANALYSIS_TYPES = {
    "ai_act_risk": {
        "label": "EU AI Act -- Riskklassificering",
        "icon": "\U0001f916",
        "description": "Klassificera ett AI-system enligt EU AI Acts riskpyramid",
        "domain": "ai_act",
    },
    "gdpr_review": {
        "label": "GDPR -- Dataskyddsgranskning",
        "icon": "\U0001f512",
        "description": "Granska en spec eller user story mot GDPR",
        "domain": "gdpr",
    },
    "eidas_check": {
        "label": "eIDAS 2.0 -- Identity & Signatur",
        "icon": "\U0001faaa",
        "description": "Bedom en autentiserings- eller signeringslosning mot eIDAS",
        "domain": "eidas",
    },
    "full_compliance": {
        "label": "Full Compliance -- Alla tre regelverk",
        "icon": "\u2696\ufe0f",
        "description": "Komplett compliance-genomgang mot EU AI Act + GDPR + eIDAS",
        "domain": "all",
    },
    "custom": {
        "label": "Fri fraga",
        "icon": "\U0001f4ac",
        "description": "Stall en specifik juridisk fraga till Giustizia",
        "domain": "all",
    },
}


def run_analysis(
    analysis_type: str,
    input_text: str,
    project_context: str = "",
    use_project_context: bool = True,
) -> dict:
    """
    Kor en compliance-analys med Giustizia.

    Returns:
        dict med {analysis: str, tokens_used: int, cost_usd: float, domain: str}
    """
    giustizia = get_agent("Giustizia")
    base_system = giustizia.get("system", "")

    analysis_config = ANALYSIS_TYPES.get(analysis_type, ANALYSIS_TYPES["custom"])
    domain = analysis_config["domain"]

    # Smart kunskapsinjicering
    if domain == "all":
        knowledge = get_knowledge("all")
    else:
        knowledge = get_relevant_knowledge(input_text + " " + analysis_config["label"])

    # Bygg system prompt
    full_system = f"""{base_system}

---
JURIDISK KUNSKAPSBAS:
{knowledge}
---

ANALYSTYP: {analysis_config['label']}
{analysis_config['description']}
"""

    # Bygg user message
    parts = []

    if use_project_context and project_context:
        parts.append(f"## PROJEKTKONTEXTEN\n{project_context}\n")

    parts.append(f"## ATT ANALYSERA\n{input_text}")

    if analysis_type == "ai_act_risk":
        parts.append("""
Ge mig:
1. Riskklassificering (Forbjuden / Hog Risk / Begransad Risk / Minimal Risk)
2. Motivering med specifika artiklar
3. Krav som galler (om Hog Risk eller GPAI)
4. Vad som maste goras INNAN aug 2026
5. Rekommendationer
""")
    elif analysis_type == "gdpr_review":
        parts.append("""
Ge mig:
1. Identifierade personuppgifter som behandlas
2. Rattslig grund for varje behandling
3. GDPR-risker och saknade element
4. DPIA kravs? (ja/nej + motivering)
5. Konkreta atgarder
""")
    elif analysis_type == "eidas_check":
        parts.append("""
Ge mig:
1. Tillitsniva (LoA) som uppnas
2. eIDAS-krav som ar relevanta
3. EU Digital Identity Wallet-relevans
4. Eventuella brister
5. Rekommendationer
""")
    elif analysis_type == "full_compliance":
        parts.append("""
Ge mig en strukturerad genomgang av alla tre regelverk:
1. EU AI Act -- riskklassificering och krav
2. GDPR -- dataskyddsanalys
3. eIDAS 2.0 -- identitet och signatur (om relevant)
4. Sammanfattad riskbild
5. Prioriterade atgarder (top 5)
""")

    user_message = "\n\n".join(parts)

    # Anropa Claude
    client = anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])

    response = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=6000,
        system=full_system,
        messages=[{"role": "user", "content": user_message}]
    )

    analysis_text = response.content[0].text
    tokens_used = response.usage.input_tokens + response.usage.output_tokens
    cost_usd = (response.usage.input_tokens * 3 / 1_000_000) + \
               (response.usage.output_tokens * 15 / 1_000_000)

    return {
        "analysis": analysis_text,
        "tokens_used": tokens_used,
        "cost_usd": round(cost_usd, 4),
        "domain": domain,
        "analysis_type": analysis_type,
    }


def save_analysis(
    project_id: str,
    analysis_type: str,
    input_text: str,
    analysis_result: str,
    tokens_used: int,
    cost_usd: float,
) -> str:
    """Spara analys som deliverable i Supabase. Returnerar deliverable_id."""
    sb = get_supabase()

    config = ANALYSIS_TYPES.get(analysis_type, ANALYSIS_TYPES["custom"])

    data = {
        "project_id": project_id,
        "title": f"{config['icon']} {config['label']}",
        "owner_agent": "Giustizia",
        "doc_type": f"compliance_{analysis_type}",
        "status": "ready",
        "content": analysis_result,
    }

    result = sb.table("deliverables").insert(data).execute()
    return result.data[0]["id"]


def get_recent_analyses(project_id: str, limit: int = 5) -> list:
    """Hamta senaste compliance-analyser for ett projekt."""
    sb = get_supabase()
    result = sb.table("deliverables").select(
        "id, title, owner_agent, status, created_at"
    ).eq("project_id", project_id).eq(
        "owner_agent", "Giustizia"
    ).order("created_at", desc=True).limit(limit).execute()
    return result.data or []
