---
name: Dreyer Patterns
description: Code conventions and required patterns for Dreyer AI Studio
---

## Dreyer Patterns

When writing or modifying code in Dreyer AI Studio, follow the platform's established patterns. Breaking these patterns is an architectural change and triggers Council Protocol.

### Required Patterns

1. **State access** — Never use `st.session_state` directly. Always go through `StateManager` from `core/state_manager.py`.
2. **Error handling** — Wrap any external call (DB, API, LLM, file I/O) with the `@handle_error` decorator from `utils/exceptions.py`.
3. **Token tracking** — Every LLM call must register with `TokenBudgetManager` from `utils/token_budget.py`. No silent token spend.
4. **Agent prompts** — Build agent system prompts via `context_loader.build_agent_system_prompt()`. Never inline raw prompts in agent logic.
5. **Multi-model routing** — Model selection happens in `router.py`. Do not hardcode model names in agent files.
6. **DB access** — Use the repository pattern in `db/`. Streamlit views never call `supabase_client` directly.
7. **Async swarm work** — Use `asyncio.gather` via `agents/swarm_runner.py`. New parallel logic goes there, not into views.

### Steps

1. Before writing code, identify which patterns apply to the change.
2. Use `semantic_search_nodes` to find existing examples of the pattern in the codebase.
3. Mirror the existing style — naming, docstrings, type hints — exactly.
4. After writing, verify the change does not introduce a new pattern variant.
5. If a new pattern is genuinely needed, this is an architectural change → Council Protocol.

### Tips

- StateManager and @handle_error are the most commonly skipped — double-check both.
- If you are tempted to write a try/except block, ask if @handle_error already covers it.
- New dependencies in `requirements.txt` always trigger Architetto sign-off.
- Test files live in `tests/` and follow `test_<module>.py` naming.

## Token Efficiency Rules
- ALWAYS start with `get_minimal_context(task="<your task>")` before any other graph tool.
- Use `detail_level="minimal"` on all calls. Only escalate to "standard" when minimal is insufficient.
- Target: complete any pattern-application task in ≤5 tool calls and ≤800 total output tokens.
