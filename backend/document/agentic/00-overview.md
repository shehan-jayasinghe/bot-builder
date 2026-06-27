# Agentic system — overview

Migration to LLM-driven routing via **capability catalog** and **final prompt** assembly at chat time.

## Prompt layers (per orchestrator turn)

| # | Layer | Source |
|---|--------|--------|
| 1 | `system_prompt` | User-owned agent config |
| 2 | `guardrail_instructions` | `GuardrailRunner` |
| 3 | `capability_catalog` | `agent.capability_catalog` + live `RuntimeBundle` |
| 4 | `rag_context` | Phase C — only after `search_knowledge` LLM tool |

Built by `FinalPromptBuilder` at chat time — do not mutate `agent.system_prompt` on attach/detach.

## Docs

| Doc | Purpose |
|-----|---------|
| [updets/api-migration-agentic.md](./updets/api-migration-agentic.md) | **All REST APIs** — endpoints, `routing_hint`, `capability_catalog` sync |
| [updets/runtime-migration-agentic.md](./updets/runtime-migration-agentic.md) | **Runtime code** — FinalPromptBuilder, chat graph, Phase C RAG |

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
