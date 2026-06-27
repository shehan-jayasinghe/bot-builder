from app.domain.models.capability_catalog import CapabilityCatalog, CapabilityEntry
from app.domain.models.runtime_bundle import RuntimeBundle, RuntimeOrchestrator, RuntimeTool
from app.domain.pipeline.prompt.capability_catalog_builder import CapabilityCatalogBuilder


def test_capability_catalog_builder_includes_routing_hints() -> None:
    bundle = RuntimeBundle(
        organization_id="org-1",
        orchestrator=RuntimeOrchestrator(
            id="agent-1",
            name="Bot",
            system_prompt="Help users.",
            tools=[
                RuntimeTool(
                    id="tool-1",
                    name="get_balance",
                    description="Fetch balance",
                    executor="mongo_find_one",
                    connector_id="conn-1",
                    status="active",
                ),
            ],
        ),
        capability_catalog=CapabilityCatalog(
            tools={"tool-1": CapabilityEntry(routing_hint="Use when user asks about balance")},
        ),
    )

    text = CapabilityCatalogBuilder().build(bundle=bundle)

    assert "## Capability catalog" in text
    assert "get_balance" in text
    assert "Use when user asks about balance" in text


def test_capability_catalog_builder_returns_empty_when_no_capabilities() -> None:
    bundle = RuntimeBundle(
        organization_id="org-1",
        orchestrator=RuntimeOrchestrator(
            id="agent-1",
            name="Bot",
            system_prompt="Help users.",
        ),
    )

    assert CapabilityCatalogBuilder().build(bundle=bundle) == ""
