from typing import Any

from pydantic import BaseModel, Field


class CapabilityEntry(BaseModel):
    routing_hint: str | None = None


class CapabilityCatalog(BaseModel):
    tools: dict[str, CapabilityEntry] = Field(default_factory=dict)
    knowledge_bases: dict[str, CapabilityEntry] = Field(default_factory=dict)
    workflows: dict[str, CapabilityEntry] = Field(default_factory=dict)
    sub_agents: dict[str, CapabilityEntry] = Field(default_factory=dict)


def empty_capability_catalog() -> dict[str, dict[str, Any]]:
    return {
        "tools": {},
        "knowledge_bases": {},
        "workflows": {},
        "sub_agents": {},
    }


def parse_capability_catalog(raw: Any) -> CapabilityCatalog:
    if not raw or not isinstance(raw, dict):
        return CapabilityCatalog()

    def _section(name: str) -> dict[str, CapabilityEntry]:
        section_raw = raw.get(name)
        if not isinstance(section_raw, dict):
            return {}
        entries: dict[str, CapabilityEntry] = {}
        for resource_id, entry_raw in section_raw.items():
            if not isinstance(entry_raw, dict):
                entries[str(resource_id)] = CapabilityEntry()
                continue
            entries[str(resource_id)] = CapabilityEntry(
                routing_hint=entry_raw.get("routing_hint"),
            )
        return entries

    return CapabilityCatalog(
        tools=_section("tools"),
        knowledge_bases=_section("knowledge_bases"),
        workflows=_section("workflows"),
        sub_agents=_section("sub_agents"),
    )


def get_routing_hint(catalog: CapabilityCatalog, section: str, resource_id: str) -> str | None:
    section_map = {
        "tools": catalog.tools,
        "knowledge_bases": catalog.knowledge_bases,
        "workflows": catalog.workflows,
        "sub_agents": catalog.sub_agents,
    }
    entry = section_map.get(section, {}).get(resource_id)
    if entry is None:
        return None
    return entry.routing_hint


def resolve_routing_hint_for_upsert(
    *,
    hint_changed: bool,
    request_routing_hint: str | None,
    preserved_routing_hint: str | None,
) -> str | None:
    if hint_changed:
        return request_routing_hint
    return preserved_routing_hint


def should_sync_catalog_on_agent_change(
    *,
    agent_id_changed: bool,
    hint_changed: bool,
    previous_agent_id: str | None,
    new_agent_id: str | None,
) -> bool:
    if new_agent_id is None:
        return False
    if hint_changed:
        return True
    return agent_id_changed and previous_agent_id != new_agent_id
