"""
Agent-router för Dreyer AI Studio.
Fas 1: Claude only med unika systemprompts per agent.
Fas 2: Multi-model routing (Claude / GPT-4o / Gemini / DeepSeek).
"""

import streamlit as st
import anthropic
from agents.council import AGENTS, MODEL_COSTS


@st.cache_resource
def get_anthropic() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])


def route_message(
    agent_name: str,
    messages: list[dict],
    project_context: str = "",
    max_tokens: int = 1024,
) -> tuple[str, int, float]:
    """
    Skickar meddelanden till rätt agent.
    Returnerar (svar, tokens_totalt, kostnad_usd).
    """
    agent = AGENTS.get(agent_name, AGENTS["Architetto"])
    client = get_anthropic()

    # Bygg systemprompt med projektkontext
    system = agent["system"]
    if project_context:
        system += f"\n\nAktivt projekt:\n{project_context}"

    try:
        response = client.messages.create(
            model=agent["model"],
            max_tokens=max_tokens,
            system=system,
            messages=messages,
        )

        content = response.content[0].text
        tokens_in  = response.usage.input_tokens
        tokens_out = response.usage.output_tokens
        total_tok  = tokens_in + tokens_out
        cost       = round((total_tok / 1000) * MODEL_COSTS.get(agent["model"], 0.003), 6)

        return content, total_tok, cost

    except Exception as e:
        return f"[{agent_name} fel: {str(e)}]", 0, 0.0


def detect_agent_from_message(message: str) -> str:
    """
    Enkel heuristik för att avgöra vilken agent som ska svara
    baserat på nyckelord i meddelandet.
    """
    msg = message.lower()

    routing = {
        "Diavolo":    ["diavolo", "red team", "säkerhet", "injection", "attack", "sårbar"],
        "Logica":     ["prompt", "variant", "eval", "testa", "precision", "svärm"],
        "Codex":      ["kod", "bygg", "streamlit", "python", "implementation", "deploy"],
        "Datatjej":   ["data", "pipeline", "databas", "supabase", "api", "integration"],
        "Narratrix":  ["demo", "presentation", "kund", "pitch", "one-pager", "slides"],
        "Guardiano":  ["gdpr", "compliance", "etik", "risk", "ai act", "bias"],
        "Scalero":    ["deploy", "hosting", "server", "kostnad", "skala", "produktion"],
        "Kontrakto":  ["kontrakt", "affär", "offert", "kund", "budget", "förhandl"],
        "Spejaren":   ["nyhet", "nyheter", "omvärld", "modell", "lansering", "forskning"],
        "Memoria":    ["tidigare", "pattern", "liknande", "minns", "historia", "projekt"],
        "Risico":     ["risk", "problem", "ifrågasätt", "kritik", "alternativ"],
        "Datatjej":   ["data", "pipeline", "databas"],
    }

    for agent, keywords in routing.items():
        if any(kw in msg for kw in keywords):
            return agent

    return "Architetto"  # Default


def build_project_context(project: dict) -> str:
    if not project:
        return ""
    phases = ["Brief", "Data", "Prompts", "Bygg", "Diavolo", "Demo", "Nästa steg"]
    current = project.get("current_phase", 1)
    phase_name = phases[current - 1] if 0 < current <= len(phases) else "Okänd"
    return (
        f"Projekt: {project.get('name', 'Okänt')} | Kund: {project.get('client', '—')} | "
        f"Fas {current}/7: {phase_name} | "
        f"Health: {project.get('health_score', 0)}/100 | "
        f"Token-budget: {project.get('token_used', 0):.2f}/{project.get('token_budget', 20):.0f} USD | "
        f"Deployment: {project.get('deployment_mode', 'cloud')}"
    )
