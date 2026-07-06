# NeMo Guardrails migration

Intent gate before the main orchestrator LLM — refuse off-topic/jailbreak, scripted greeting/help/bye without a full LLM call.

## Architecture

```
User Message
    → NeMo Intent Gate (cheap; feature-flagged)
        → refuse (off-topic | jailbreak | sensitive)
        → scripted (greeting | help | bye) — no orchestrator LLM
        → proceed → ChatGraph → create_agent() — main LLM
            → LangChain PIIMiddleware (input + output)
    → NeMo Output Gate (self-check output; feature-flagged)
        → replace blocked reply with refusal
        → Bot Response
```

| Layer | Owner | Notes |
|-------|-------|-------|
| PII redaction | LangChain `PIIMiddleware` | email, credit_card, ip, url; block api_key/password/otp |
| Intent / input policy | NeMo Guardrails | input self-check; scripted replies from `scripted_intents.yml` |
| Output policy | NeMo Guardrails | `self check output` after graph turn |
| Orchestrator | LangGraph + `create_agent()` | unchanged |

## Phases

| Phase | Scope | Status |
|-------|-------|--------|
| **0** | Dependency spike, default profile, intent gate module, feature flag (default off), tests | **Done** |
| **1** | Structured gate result, agent context, single-source `scripted_intents.yml` | **Done** (buckets 1–2) |
| 1b | Input rail tuning, staging rollout, integration tests | Planned |
| **2** | LangChain `PIIMiddleware` expand (ip, url, api_key, password, otp) | **Done** |
| 3 | Output rails (self-check output) | **Done** |
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

Default profile (`config/nemo/profiles/default/`):

- `config.yml` — Bedrock Haiku + `self check input`
- `scripted_intents.yml` — greeting / help / goodbye phrases + reply templates

Set `NEMOGUARDRAILS_LLM_FRAMEWORK=langchain` (done in `nemo_runtime.py`).

### Code

| File | Role |
|------|------|
| `domain/pipeline/guardrails/nemo_gate_models.py` | `NeMoGateIntent`, `NeMoGateContext`, `GuardrailCheckResult` |
| `domain/pipeline/guardrails/nemo_paths.py` | Resolve config directory |
| `domain/pipeline/guardrails/nemo_runtime.py` | Lazy `LLMRails` singleton |
| `domain/pipeline/guardrails/scripted_intents.py` | Load `scripted_intents.yml`, `match_scripted_intent()` |
| `domain/pipeline/guardrails/nemo_intent_gate.py` | `evaluate_nemo_intent()`, `build_gate_context()` |
| `domain/pipeline/guardrails/nemo_output_gate.py` | `evaluate_nemo_output()`, `apply_nemo_output_gate()` |
| `domain/pipeline/guardrails/runner.py` | Delegates `check()` when flag on |
| `services/chat_completion_service.py` | Scripted + blocked early return; skip input gate in workflow; output gate after graph |

### Trace events

| Event | When |
|-------|------|
| `nemo_scripted_reply` | `scripted_intents.yml` match (greeting/help/bye) |
| `nemo_intent_blocked` | NeMo input rail blocked |
| `nemo_output_complete` | Output self-check passed (NeMo on) |
| `nemo_output_blocked` | Output rail blocked (NeMo on) |
| `guardrail_complete` | Check passed (`gate: proceed` when NeMo on) |

Workflow turns (`tracker.active_flow_state` set) skip the NeMo gate.

### Enable locally

```bash
export NEMO_GUARDRAILS_ENABLED=true
# AWS credentials for Bedrock Haiku (self-check input)
poetry run uvicorn app.main:app --reload
```

### Tests

```bash
poetry run pytest tests/test_nemo_output_gate.py tests/test_nemo_intent_gate.py tests/test_guardrail_runner.py -q
```

Unit tests mock `LLMRails.check_async` for jailbreak blocking. Config load test does not call Bedrock.

### Manual spike (optional)

With flag on and AWS creds:

1. `hello` → scripted reply, no orchestrator LLM in trace
2. Jailbreak prompt → `nemo_intent_blocked` + refusal
3. Normal business question → `guardrail_complete` with `gate: proceed` → full graph

## Phase 1 (buckets 1–2 — implemented)

### Structured gate result

`GuardrailCheckResult` (`nemo_gate_models.py`):

| Field | Values |
|-------|--------|
| `intent` | `proceed` \| `greeting` \| `help` \| `bye` \| `blocked` |
| `matched_phrase` | Scripted phrase hit (e.g. `hello`) |
| `rail` | NeMo rail name when blocked (e.g. `self check input`) |

`NeMoGateContext` passed from chat: `agent_name`, `industry`, `description`.

### Single-source scripted config

`config/nemo/profiles/default/scripted_intents.yml` — phrases + reply templates (`{agent_name}`, `{industry}`).

Runtime: `scripted_intents.py` → `match_scripted_intent()` (zero LLM). NeMo colang dialog rails can be added later per profile if needed.

### Trace payloads

| Event | Payload |
|-------|---------|
| `nemo_scripted_reply` | `intent`, `matched_phrase` |
| `nemo_intent_blocked` | `intent`, `rail` |
| `guardrail_complete` | `gate: proceed` when NeMo on |

## Phase 2 — LangChain PII expand (Done)

Orchestrator/sub-agent `create_agent()` via `pii_middleware.py`:

| Type | Strategy | Scope |
|------|----------|-------|
| `email` | redact | input + output |
| `credit_card` | mask | input + output |
| `ip` | redact | input + output |
| `url` | redact | input + output |
| `api_key` | block (regex) | input + output |
| `password` | block (regex) | input + output |
| `otp` | block (regex) | input + output |

`PIIDetectionError` from `block` → friendly `PII_BLOCKED_USER_MESSAGE` in `orchestrator_agent.py`.

**Not covered:** tool-less `_simple_chat` path; workflow slot capture (no `create_agent()`).

## Phase 3 — Output rails (Done)

After `ChatGraph.run_turn()` returns replies (orchestrator, sub-agent, or workflow), NeMo runs `self check output` on each reply with text when `NEMO_GUARDRAILS_ENABLED=true`. Blocked replies are replaced with `GUARDRAIL_REFUSAL_MESSAGE` (or NeMo-provided refusal). Fail-open on runtime errors (same as input gate).

Scripted and input-blocked early returns skip the output gate (no graph reply to check).

### Configuration

`config.yml` — `rails.output.flows: [self check output]` + `self_check_output` prompt (`user_input`, `bot_response`).

### Code

| File | Role |
|------|------|
| `nemo_gate_models.py` | `NeMoOutputCheckResult` |
| `nemo_output_gate.py` | `evaluate_nemo_output()`, `apply_nemo_output_gate()` |
| `services/chat_completion_service.py` | Output gate after graph turn; trace events |

### Trace events

| Event | When |
|-------|------|
| `nemo_output_complete` | Output check passed (NeMo on) |
| `nemo_output_blocked` | Output rail blocked (`rail` in payload) |

### Tests

```bash
poetry run pytest tests/test_nemo_output_gate.py tests/test_nemo_intent_gate.py -q
```

## Related docs

- [migration-langchain-proper.md](./migration-langchain-proper.md) — LangChain/LangGraph runtime
- [01-chat-completion-diagrams.md](../../chat/01-chat-completion-diagrams.md) — chat flow traces
