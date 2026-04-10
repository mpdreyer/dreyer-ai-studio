"""
Agent-router för Dreyer AI Studio.
Fas 2: Multi-model routing — Claude / GPT-4o / Gemini / DeepSeek
Fallback till Claude om annan provider misslyckas.
"""

import streamlit as st
import anthropic
from agents.council import AGENTS, MODEL_COSTS


# ── Provider-klienter ─────────────────────────────────────────────────────────

@st.cache_resource
def get_anthropic() -> anthropic.Anthropic:
    return anthropic.Anthropic(api_key=st.secrets["ANTHROPIC_API_KEY"])


@st.cache_resource
def get_openai():
    try:
        from openai import OpenAI
        key = st.secrets.get("OPENAI_API_KEY", "")
        if not key:
            return None
        return OpenAI(api_key=key)
    except Exception:
        return None


@st.cache_resource
def get_gemini():
    try:
        import google.generativeai as genai
        key = st.secrets.get("GEMINI_API_KEY") or st.secrets.get("GOOGLE_API_KEY", "")
        if not key:
            return None
        genai.configure(api_key=key)
        return genai
    except Exception:
        return None


@st.cache_resource
def get_deepseek():
    try:
        from openai import OpenAI
        key = st.secrets.get("DEEPSEEK_API_KEY", "")
        if not key:
            return None
        return OpenAI(api_key=key, base_url="https://api.deepseek.com")
    except Exception:
        return None


# ── Modell-routing per agent ──────────────────────────────────────────────────

AGENT_MODEL_MAP = {
    # Claude — strategi, arkitektur, text, storytelling
    "Architetto":  "claude",
    "Narratrix":   "claude",
    "Codex":       "claude",   # Claude Code hanterar faktisk kod
    "Scalero":     "claude",

    # GPT-4o — eval, kommunikation, affär
    "Logica":      "openai",
    "Kontrakto":   "openai",

    # Gemini — data, analys, omvärld, minne
    "Datatjej":    "gemini",
    "Spejaren":    "gemini",
    "Memoria":     "gemini",

    # DeepSeek — adversarial, säkerhet, kritik
    "Diavolo":     "deepseek",
    "Risico":      "deepseek",
    "Guardiano":   "deepseek",
}

CLAUDE_MODEL   = "claude-sonnet-4-5"
OPENAI_MODEL   = "gpt-4o"
GEMINI_MODEL   = "gemini-1.5-pro"
DEEPSEEK_MODEL = "deepseek-reasoner"


# ── Huvud-router ──────────────────────────────────────────────────────────────

def route_message(
    agent_name: str,
    messages: list[dict],
    project_context: str = "",
    max_tokens: int = 1024,
) -> tuple[str, int, float]:
    """
    Skickar meddelanden till rätt provider baserat på agent.
    Returnerar (svar, tokens_totalt, kostnad_usd).
    Fallback till Claude om annan provider misslyckas.
    """
    agent    = AGENTS.get(agent_name, AGENTS["Architetto"])
    provider = AGENT_MODEL_MAP.get(agent_name, "claude")

    system = agent["system"]
    if project_context:
        system += f"\n\nAktivt projekt:\n{project_context}"

    try:
        if provider == "claude":
            return _call_claude(system, messages, max_tokens)
        elif provider == "openai":
            return _call_openai(system, messages, max_tokens)
        elif provider == "gemini":
            return _call_gemini(system, messages, max_tokens)
        elif provider == "deepseek":
            return _call_deepseek(system, messages, max_tokens)
        else:
            return _call_claude(system, messages, max_tokens)
    except Exception:
        # Fallback: försök med Claude
        try:
            return _call_claude(system, messages, max_tokens)
        except Exception as e2:
            return f"[{agent_name} fel: {str(e2)}]", 0, 0.0


# ── Provider-anrop ────────────────────────────────────────────────────────────

def _call_claude(system: str, messages: list[dict], max_tokens: int) -> tuple:
    client   = get_anthropic()
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=messages,
    )
    content   = response.content[0].text
    tokens_in = response.usage.input_tokens
    tokens_out = response.usage.output_tokens
    tokens    = tokens_in + tokens_out
    cost      = round((tokens_in / 1_000_000) * 3.0 + (tokens_out / 1_000_000) * 15.0, 6)
    return content, tokens, cost


def _call_openai(system: str, messages: list[dict], max_tokens: int) -> tuple:
    client = get_openai()
    if not client:
        return _call_claude(system, messages, max_tokens)
    api_msgs = [{"role": "system", "content": system}] + messages
    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        max_tokens=max_tokens,
        messages=api_msgs,
    )
    content = response.choices[0].message.content
    tokens  = response.usage.total_tokens
    cost    = round((tokens / 1_000_000) * 5.0, 6)
    return content, tokens, cost


def _call_gemini(system: str, messages: list[dict], max_tokens: int) -> tuple:
    genai = get_gemini()
    if not genai:
        return _call_claude(system, messages, max_tokens)
    model = genai.GenerativeModel(
        model_name=GEMINI_MODEL,
        system_instruction=system,
    )
    history = [
        {"role": "user" if m["role"] == "user" else "model",
         "parts": [m["content"]]}
        for m in messages[:-1]
    ]
    chat     = model.start_chat(history=history)
    response = chat.send_message(
        messages[-1]["content"],
        generation_config={"max_output_tokens": max_tokens},
    )
    content = response.text
    tokens  = getattr(response, "usage_metadata", None)
    tokens  = (tokens.total_token_count if tokens else len(content.split()) * 2)
    cost    = round((tokens / 1_000_000) * 1.25, 6)
    return content, tokens, cost


def _call_deepseek(system: str, messages: list[dict], max_tokens: int) -> tuple:
    client = get_deepseek()
    if not client:
        return _call_claude(system, messages, max_tokens)
    api_msgs = [{"role": "system", "content": system}] + messages
    response = client.chat.completions.create(
        model=DEEPSEEK_MODEL,
        max_tokens=max_tokens,
        messages=api_msgs,
    )
    content = response.choices[0].message.content
    tokens  = response.usage.total_tokens
    cost    = round((tokens / 1_000_000) * 1.0, 6)
    return content, tokens, cost


# ── Hjälpfunktioner ───────────────────────────────────────────────────────────

def detect_agent_from_message(message: str) -> str:
    msg = message.lower()
    routing = {
        "Diavolo":   ["diavolo", "red team", "säkerhet", "injection", "attack", "sårbar"],
        "Logica":    ["prompt", "variant", "eval", "testa", "precision", "svärm"],
        "Codex":     ["kod", "bygg", "streamlit", "python", "implementation", "deploy"],
        "Datatjej":  ["data", "pipeline", "databas", "supabase", "api", "integration"],
        "Narratrix": ["demo", "presentation", "kund", "pitch", "one-pager", "slides"],
        "Guardiano": ["gdpr", "compliance", "etik", "risk", "ai act", "bias"],
        "Scalero":   ["deploy", "hosting", "server", "kostnad", "skala", "produktion"],
        "Kontrakto": ["kontrakt", "affär", "offert", "budget", "förhandl"],
        "Spejaren":  ["nyhet", "omvärld", "modell", "lansering", "forskning"],
        "Memoria":   ["tidigare", "pattern", "liknande", "minns", "historia", "projekt"],
        "Risico":    ["risk", "problem", "ifrågasätt", "kritik", "alternativ"],
    }
    for agent, keywords in routing.items():
        if any(kw in msg for kw in keywords):
            return agent
    return "Architetto"


def build_project_context(project: dict) -> str:
    if not project:
        return ""
    phases = ["Brief", "Data", "Prompts", "Bygg", "Diavolo", "Demo", "Nästa steg"]
    cur    = project.get("current_phase", 1)
    pname  = phases[cur - 1] if 0 < cur <= len(phases) else "Okänd"
    return (
        f"Projekt: {project.get('name', 'Okänt')} | "
        f"Kund: {project.get('client', '—')} | "
        f"Fas {cur}/7: {pname} | "
        f"Health: {project.get('health_score', 0)}/100 | "
        f"Token: {project.get('token_used', 0):.2f}/{project.get('token_budget', 20):.0f} USD | "
        f"Deployment: {project.get('deployment_mode', 'cloud')}"
    )
