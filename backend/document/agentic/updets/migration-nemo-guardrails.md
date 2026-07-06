# NeMo Guardrails migration

Intent gate before the main orchestrator LLM — refuse off-topic/jailbreak, scripted greeting/help/bye without a full LLM call.

## Architecture

```
User Message
    → NeMo Intent Gate (cheap; feature-flagged)
        → refuse (off-topic | jailbreak | sensitive)
        → scripted (greeting | help | bye) — no orchestrator LLM
        → proceed → ChatGraph → create_agent() — main LLM
```

| Layer | Owner | Notes |
|-------|-------|-------|
| PII redaction | LangChain `PIIMiddleware` | email redact, credit_card mask |
| Intent / policy | NeMo Guardrails | input self-check + dialog rails |
| Orchestrator | LangGraph + `create_agent()` | unchanged |

## Phases

| Phase | Scope | Status |
|-------|-------|--------|
| **0** | Dependency spike, default profile, intent gate module, feature flag (default off), tests | **Done** |
| 1 | Production intent gate tuning, colang parity with local scripted | Planned |
| 2 | Expand PII detectors (password/secret) | Planned |
| 3 | Output rails (self-check output) | Planned |
| 4 | Per-agent NeMo profiles (industry / agent_type) | Planned |

## Phase 0 (implemented)

### Dependencies

- `nemoguardrails ^0.23.0` in `pyproject.toml`
- Python constrained to `>=3.11,<3.14` (NeMo does not support 3.14 yet)

### Configuration

| Setting | Env | Default |
|---------|-----|---------|
| `nemo_guardrails_enabled` | `NEMO_GUARDRAILS_ENABLED` | `false` |
| `nemo_config_path` | `NEMO_CONFIG_PATH` | `backend/config/nemo/profiles/default` |

Default profile:

- `config/nemo/profiles/default/config.yml` — Bedrock Haiku + `self check input`
- `config/nemo/profiles/default/rails.co` — greeting / help / goodbye dialog flows

Set `NEMOGUARDRAILS_LLM_FRAMEWORK=langchain` (done in `nemo_runtime.py`).

### Code

| File | Role |
|------|------|
| `domain/pipeline/guardrails/nemo_paths.py` | Resolve config directory |
| `domain/pipeline/guardrails/nemo_runtime.py` | Lazy `LLMRails` singleton |
| `domain/pipeline/guardrails/nemo_intent_gate.py` | `evaluate_nemo_intent()` |
| `domain/pipeline/guardrails/runner.py` | Delegates `check()` when flag on |
| `services/chat_completion_service.py` | Scripted + blocked early return; skip gate in workflow |

### Trace events

| Event | When |
|-------|------|
| `nemo_scripted_reply` | Local scripted intent (greeting/help/bye) |
| `nemo_intent_blocked` | NeMo input rail blocked |
| `guardrail_blocked` | Generic block when NeMo off (reserved) |

Workflow turns (`tracker.active_flow_state` set) skip the NeMo gate.

### Enable locally

```bash
export NEMO_GUARDRAILS_ENABLED=true
# AWS credentials for Bedrock Haiku (self-check input)
poetry run uvicorn app.main:app --reload
```

### Tests

```bash
poetry run pytest tests/test_nemo_intent_gate.py tests/test_guardrail_runner.py -q
```

Unit tests mock `LLMRails.check_async` for jailbreak blocking. Config load test does not call Bedrock.

### Manual spike (optional)

With flag on and AWS creds:

1. `hello` → scripted reply, no orchestrator LLM in trace
2. Jailbreak prompt → `nemo_intent_blocked` + refusal
3. Normal business question → `guardrail_complete` → full graph

## Related docs

- [migration-langchain-proper.md](./migration-langchain-proper.md) — LangChain/LangGraph runtime
- [01-chat-completion-diagrams.md](../../chat/01-chat-completion-diagrams.md) — chat flow traces
