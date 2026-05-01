---
name: Council Protocol
description: When and how Codex escalates to other agents in The Council
---

## Council Protocol

Codex operates within The Council. Some decisions exceed Codex's mandate and must be escalated to the right agent before code is written or merged.

### Escalation Matrix

| Situation | Escalate to | Action |
|-----------|-------------|--------|
| New module, changed routing, new dependency, altered data model | **Architetto (AR)** | STOP. Ask for sign-off before coding. |
| Change touches >5 files or modifies a critical flow | **Architetto + Risico** | Ask AR for green light, ask Risico for HIGH/MEDIUM/LOW rating. |
| Code handles secrets, auth, PII, or external API keys | **Guardiano** | Confirm GDPR/security review before merge. |
| New tests required, prompt changes, QA-relevant logic | **Logica** | Request test case design. |
| Cost-sensitive change (model routing, swarm size, token budget) | **Kontrakto** | Confirm budget impact. |
| Data pipeline / RAG ingestion / DB schema change | **Datatjej** | Validate data integrity approach. |

### Steps

1. Before writing code, classify the change against the matrix above.
2. If escalation is required, STOP and surface a single clear question to the user.
3. Frame the question as: "This is a <type> change — should this go through <agent> first?"
4. Wait for user confirmation before proceeding.
5. If the user defers escalation explicitly, log that decision in the response and proceed with caution.

### Tips

- Default to escalating when uncertain. Better one extra question than a regretted commit.
- Bug fixes, refactors within a single module, tests, and docs do NOT require escalation.
- Mention which agents you would loop in even when the user is the only one in the room — it makes the decision auditable.

## Token Efficiency Rules
- Classify the change in one short sentence before any tool calls.
- Escalation questions must be ≤2 sentences. No long preambles.
- Target: complete escalation decisions in ≤2 tool calls and ≤300 total output tokens.
