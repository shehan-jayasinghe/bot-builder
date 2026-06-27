from app.domain.models.capability_catalog import CapabilityCatalog, CapabilityEntry
from app.domain.models.runtime_bundle import RuntimeBundle, RuntimeOrchestrator, RuntimeTool
from app.domain.pipeline.prompt.final_prompt_builder import FinalPromptBuilder


def test_final_prompt_builder_orders_layers_without_mutating_system_prompt() -> None:
    orchestrator = RuntimeOrchestrator(
        id="agent-1",
        name="Bot",
        system_prompt="Base prompt.",
        personality="Friendly",
        tone="Clear",
    )
    bundle = RuntimeBundle(
        organization_id="org-1",
        orchestrator=orchestrator,
        capability_catalog=CapabilityCatalog(
            tools={"tool-1": CapabilityEntry(routing_hint="Balance questions")},
        ),
    )
    bundle.orchestrator.tools = [
        RuntimeTool(
            id="tool-1",
            name="get_balance",
            description="Fetch balance",
            executor="mongo_find_one",
            connector_id="conn-1",
            status="active",
        ),
    ]

    prompt = FinalPromptBuilder().build_from_bundle(
        bundle=bundle,
        guardrail_instructions="## Guardrails\n- Never ask for passwords",
        rag_context="Account FAQ snippet",
    )

    assert orchestrator.system_prompt == "Base prompt."
    assert prompt.index("Base prompt.") < prompt.index("Personality:")
    assert prompt.index("Personality:") < prompt.index("## Guardrails")
    assert prompt.index("## Guardrails") < prompt.index("## Capability catalog")
    assert prompt.index("## Capability catalog") < prompt.index("## Retrieved context")
    assert "Balance questions" in prompt
    assert "Account FAQ snippet" in prompt


def test_final_prompt_builder_skips_duplicate_layers_for_legacy_baked_prompt() -> None:
    orchestrator = RuntimeOrchestrator(
        id="agent-1",
        name="Bot",
        system_prompt=(
            "You are an AI assistant.\n\n"
            "Personality: Friendly\n\n"
            "Tone: Clear\n\n"
            "Safety and guardrails:\n- Never ask for passwords"
        ),
        personality="Friendly",
        tone="Clear",
    )
    bundle = RuntimeBundle(organization_id="org-1", orchestrator=orchestrator)

    prompt = FinalPromptBuilder().build_from_bundle(
        bundle=bundle,
        guardrail_instructions="## Guardrails\n- Never ask for passwords",
        rag_context="",
    )

    assert prompt.count("Personality:") == 1
    assert prompt.count("Tone:") == 1
    assert prompt.count("Never ask for passwords") == 1
