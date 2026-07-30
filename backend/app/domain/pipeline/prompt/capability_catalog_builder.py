from app.domain.models.capability_catalog import CapabilityCatalog, get_routing_hint
from app.domain.models.runtime_bundle import (
    RuntimeBundle,
    RuntimeKnowledgeBase,
    RuntimeSubAgent,
    RuntimeTool,
    RuntimeWorkflow,
)


class CapabilityCatalogBuilder:
    def build(self, *, bundle: RuntimeBundle) -> str:
        catalog = bundle.capability_catalog
        orchestrator = bundle.orchestrator
        sections: list[str] = []

        tool_lines = self._tool_lines(orchestrator.tools, catalog, "tools")
        if tool_lines:
            sections.append("### Tools\n" + "\n".join(tool_lines))

        kb_lines = self._kb_lines(orchestrator.knowledge_bases, catalog, "knowledge_bases")
        if kb_lines:
            sections.append("### Knowledge bases\n" + "\n".join(kb_lines))

        workflow_lines = self._workflow_lines(orchestrator.workflows, catalog, "workflows")
        if workflow_lines:
            sections.append("### Workflows\n" + "\n".join(workflow_lines))

        sub_agent_lines = self._sub_agent_lines(orchestrator.sub_agents, catalog, "sub_agents")
        if sub_agent_lines:
            sections.append("### Sub-agents\n" + "\n".join(sub_agent_lines))

        if not sections:
            return ""
        return "## Capability catalog\n" + "\n\n".join(sections)

    @staticmethod
    def _tool_lines(
        tools: list[RuntimeTool],
        catalog: CapabilityCatalog,
        section: str,
    ) -> list[str]:
        lines: list[str] = []
        for tool in tools:
            hint = get_routing_hint(catalog, section, tool.id)
            detail = tool.description or tool.name
            if hint:
                lines.append(f"- {tool.name}: {hint} ({detail})")
            else:
                lines.append(f"- {tool.name}: {detail}")
        return lines

    @staticmethod
    def _kb_lines(
        knowledge_bases: list[RuntimeKnowledgeBase],
        catalog: CapabilityCatalog,
        section: str,
    ) -> list[str]:
        lines: list[str] = []
        for kb in knowledge_bases:
            hint = get_routing_hint(catalog, section, kb.id)
            detail = kb.description or kb.name
            if hint:
                lines.append(f"- {kb.name}: {hint} ({detail})")
            else:
                lines.append(f"- {kb.name}: {detail}")
        return lines

    @staticmethod
    def _workflow_lines(
        workflows: list[RuntimeWorkflow],
        catalog: CapabilityCatalog,
        section: str,
    ) -> list[str]:
        lines: list[str] = []
        for workflow in workflows:
            hint = get_routing_hint(catalog, section, workflow.id)
            detail = workflow.description or workflow.name
            if hint:
                lines.append(f"- {workflow.name}: {hint} ({detail})")
            else:
                lines.append(f"- {workflow.name}: {detail}")
        return lines

    @staticmethod
    def _sub_agent_lines(
        sub_agents: list[RuntimeSubAgent],
        catalog: CapabilityCatalog,
        section: str,
    ) -> list[str]:
        lines: list[str] = []
        for sub_agent in sub_agents:
            hint = get_routing_hint(catalog, section, sub_agent.id)
            detail = sub_agent.description or sub_agent.name
            if hint:
                lines.append(f"- {sub_agent.name}: {hint} ({detail})")
            else:
                lines.append(f"- {sub_agent.name}: {detail}")
        return lines
