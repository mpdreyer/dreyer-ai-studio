# Esecutore — Agent 13 · Task Executor

## Agentprofil

| Egenskap | Varde |
|----------|-------|
| **Namn** | Esecutore |
| **Roll** | Task Executor · Agent 13 |
| **Modell** | claude-sonnet-4-5 |
| **Provider** | Claude (fallback: Claude) |
| **Token-limit** | 8000 |
| **Status** | active |
| **Farg** | Gron (#D4EDDA / #155724) |
| **Initialer** | ES |

## Syfte

Esecutore tar beslut fran radet och omvandlar dem till konkreta, exekverbara prompts
for Claude Code och Codex CLI. Han ar radets hander — ser till att saker faktiskt
blir gjorda.

"Basta parlare. Facciamo."

## Prompt-mallar (7 st)

| Typ | Funktion | Beskrivning |
|-----|----------|-------------|
| `init` | `template_init` | Initiera nytt repo fran projekt-spec |
| `feature` | `template_feature` | Lagg till feature i befintligt repo |
| `fix` | `template_fix` | Fixa bug eller issue |
| `refactor` | `template_refactor` | Refaktorera komponent |
| `test` | `template_test` | Generera tester |
| `docs` | `template_docs` | Dokumentation + NotebookLM-sync |
| `custom` | `template_custom` | Fri-text, anvandaren beskriver |

Mallarna `init`, `feature`, `refactor` och `custom` inkluderar ett ASKS-block
dar Esecutore listar antaganden som anvandaren bor bekrafta innan exekvering.

## Targets

| Target | Stil |
|--------|------|
| `claude_code` | Stegvis, konversationell |
| `codex_cli` | Kommandodriven, kort |
| `custom` | Anpassat format |

## Supabase-tabell: execution_prompts

```sql
create table if not exists execution_prompts (
  id                    uuid primary key default gen_random_uuid(),
  project_id            uuid references projects(id) on delete cascade,
  created_at            timestamptz default now(),
  prompt_type           text not null,
  target                text not null,
  user_context          text,
  generated_prompt      text not null,
  tokens_used           int default 0,
  cost_usd              float default 0.0,
  status                text default 'generated',
  executed_at           timestamptz,
  completion_notes      text,
  include_brief         boolean default true,
  include_success_criteria boolean default true,
  include_tech_stack    boolean default true,
  include_deliverables  boolean default true,
  include_notebooklm    boolean default false
);
```

## Filer

| Fil | Innehall |
|-----|----------|
| `agents/council.py` | Agentdefinition i AGENTS-dict |
| `agents/router.py` | Provider-mapping + token-limit + keyword-routing |
| `agents/esecutore.py` | Huvudlogik: generate, save, mark_as_executed |
| `agents/esecutore_templates.py` | 7 prompt-mallar |
| `views/esecutore.py` | Streamlit UI — Execution Hub |
| `core/registry.py` | Vy-registrering |
| `components/sidebar.py` | Sidebar-navigering |

## Arkitekturflode

```
UI (views/esecutore.py)
  -> generate_execution_prompt (agents/esecutore.py)
    -> get_template (agents/esecutore_templates.py)
    -> build_project_context (agents/esecutore.py)
    -> Claude API (claude-sonnet-4-5, max 8000 tokens)
  -> save_execution_prompt -> Supabase execution_prompts
  -> Kopieras till clipboard -> Klistras i Claude Code / Codex CLI
```
