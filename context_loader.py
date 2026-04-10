"""
Dreyer AI Studio — context_loader
Laddar persistent projektkontext för rådsagenter.

Användning:
    from context_loader import load_project_context, build_agent_system_prompt

    ctx = load_project_context("epai")
    prompt = build_agent_system_prompt("Architetto", base_prompt, ctx)
"""

from __future__ import annotations

import os
from pathlib import Path

_STUDIO_ROOT = Path(__file__).parent


def load_project_context(project_name: str) -> str:
    """
    Laddar PROJECT_BRIEF.md för angivet projekt.

    Args:
        project_name: Katalognamn under studio-roten (t.ex. "epai").

    Returns:
        Filinnehållet som sträng, eller ett tydligt felmeddelande om
        filen saknas — aldrig tom sträng (agents ska inte gissa).
    """
    path = _STUDIO_ROOT / project_name / "PROJECT_BRIEF.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return f"[Ingen PROJECT_BRIEF.md hittad för projekt '{project_name}' — fråga Mattias]"


def build_agent_system_prompt(
    agent_name: str,
    base_prompt: str,
    project_context: str,
    project_name: str = "EPAi",
) -> str:
    """
    Injicerar projektkontext i slutet av en agents befintliga systemprompt.

    Args:
        agent_name:      Agentens namn (för loggning).
        base_prompt:     Agentens ursprungliga systemprompt.
        project_context: Innehållet från load_project_context().
        project_name:    Visningsnamn för projektet.

    Returns:
        Komplett systemprompt med kontext injicerad.
    """
    return f"""{base_prompt}

---
## Aktivt kundprojekt: {project_name}

Du har tillgång till fullständig, beslutad projektinformation nedan.
Använd den som primär källa. Gissa ALDRIG — saknas info, fråga Mattias.

{project_context}
---"""


# ── Förladda kontexter (körs vid import) ─────────────────────────────────────

EPAI_CONTEXT = load_project_context("epai")
