# Agentic system — overview

Migration to LLM-driven routing via **capability catalog** and **final prompt** assembly at chat time.

## Prompt layers (per orchestrator turn)

| # | Layer | Source |
|---|--------|--------|
| 1 | `system_prompt` | Base role/responsibilities on agent doc; personality/tone added at chat by `FinalPromptBuilder` |
| 2 | `guardrail_instructions` | `GuardrailRunner` |
| 3 | `capability_catalog` | `agent.capability_catalog` + live `RuntimeBundle` |
| 4 | `rag_context` | `search_knowledge` LLM tool only (Phase C **Done**) |

Built by `FinalPromptBuilder` at chat time — do not mutate `agent.system_prompt` on attach/detach.

## Phases

| Phase | Runtime change | Status |
|-------|----------------|--------|
| **A** | Catalog + `FinalPromptBuilder` + attach sync | **Done** |
| **B** | Remove auto-start workflow — LLM picks from catalog | **Done** — [runtime-migration-agentic-phase-b.md](./updets/runtime-migration-agentic-phase-b.md) |
| **C** | `search_knowledge` tool; remove always-on RAG | **Done** — [runtime-migration-agentic-phase-c.md](./updets/runtime-migration-agentic-phase-c.md) |
| **D** | Sticky sub-agent | **Planned** — [runtime-migration-agentic-phase-d.md](./updets/runtime-migration-agentic-phase-d.md) |

## Docs

| Doc | Purpose |
|-----|---------|
| [updets/api-migration-agentic.md](./updets/api-migration-agentic.md) | **All REST APIs** — Phase A catalog + `routing_hint` |
| [updets/runtime-migration-agentic.md](./updets/runtime-migration-agentic.md) | **Runtime** — Phase A `FinalPromptBuilder` (Done) |
| [updets/api-migration-agentic-phase-b.md](./updets/api-migration-agentic-phase-b.md) | **Phase B** — agentic workflow routing (Done) |
| [updets/runtime-migration-agentic-phase-b.md](./updets/runtime-migration-agentic-phase-b.md) | **Phase B runtime** — remove auto-start workflow |
| [updets/api-migration-agentic-phase-c.md](./updets/api-migration-agentic-phase-c.md) | **Phase C** — agentic RAG (`search_knowledge` tool) (**Done**) |
| [updets/runtime-migration-agentic-phase-c.md](./updets/runtime-migration-agentic-phase-c.md) | **Phase C runtime** — remove always-on RAG |
| [updets/api-migration-agentic-phase-d.md](./updets/api-migration-agentic-phase-d.md) | **Phase D** — sticky sub-agent (planned) |
| [updets/runtime-migration-agentic-phase-d.md](./updets/runtime-migration-agentic-phase-d.md) | **Phase D runtime** — persist sub-agent across turns |

## API docs by resource

| Resource | Doc |
|----------|-----|
| Agent create/get/list | [../agent/01-create-agent-diagrams.md](../agent/01-create-agent-diagrams.md) · [../agent/02-get-agent-diagrams.md](../agent/02-get-agent-diagrams.md) · [../agent/03-list-agents-diagrams.md](../agent/03-list-agents-diagrams.md) |
| Tools | [../tools/01-create-tool-diagrams.md](../tools/01-create-tool-diagrams.md) · [../tools/08-update-tool-agent-diagrams.md](../tools/08-update-tool-agent-diagrams.md) |
| Knowledge bases | [../knowledgebase/01-create-knowledgebase-diagrams.md](../knowledgebase/01-create-knowledgebase-diagrams.md) · [../knowledgebase/04-update-knowledgebase-agent-diagrams.md](../knowledgebase/04-update-knowledgebase-agent-diagrams.md) |
| Workflows | [../workflows/01-create-workflow-diagrams.md](../workflows/01-create-workflow-diagrams.md) · [../workflows/04-update-workflow-diagrams.md](../workflows/04-update-workflow-diagrams.md) |
| Sub-agents | [../sub-agents/01-create-sub-agent-diagrams.md](../sub-agents/01-create-sub-agent-diagrams.md) · [../sub-agents/04-update-sub-agent-diagrams.md](../sub-agents/04-update-sub-agent-diagrams.md) |
| Chat / preview | [../chat/01-chat-completion-diagrams.md](../chat/01-chat-completion-diagrams.md) — **no REST change** |
| Sub-agent / RAG / workflow runtime | [../chat/02-sub-agent-delegation-at-chat-diagrams.md](../chat/02-sub-agent-delegation-at-chat-diagrams.md) · [../chat/03-rag-at-chat-diagrams.md](../chat/03-rag-at-chat-diagrams.md) · [../chat/04-workflow-runtime-at-chat-diagrams.md](../chat/04-workflow-runtime-at-chat-diagrams.md) |
