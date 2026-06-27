from app.domain.models.runtime_bundle import RuntimeBundle, RuntimeOrchestrator
from app.domain.pipeline.prompt.capability_catalog_builder import CapabilityCatalogBuilder


def _has_baked_personality(system_prompt: str) -> bool:
    return "Personality:" in system_prompt


def _has_baked_tone(system_prompt: str) -> bool:
    return "Tone:" in system_prompt


def _has_baked_guardrails(system_prompt: str) -> bool:
    return "Safety and guardrails:" in system_prompt or "## Guardrails" in system_prompt


class FinalPromptBuilder:
    def __init__(self, *, catalog_builder: CapabilityCatalogBuilder | None = None) -> None:
        self._catalog_builder = catalog_builder or CapabilityCatalogBuilder()

    def build(
        self,
        *,
        orchestrator: RuntimeOrchestrator,
        guardrail_instructions: str,
        capability_catalog_text: str,
        rag_context: str = "",
    ) -> str:
        parts: list[str] = [orchestrator.system_prompt]
        system_prompt = orchestrator.system_prompt

        if orchestrator.personality and not _has_baked_personality(system_prompt):
            parts.append(f"Personality: {orchestrator.personality}")
        if orchestrator.tone and not _has_baked_tone(system_prompt):
            parts.append(f"Tone: {orchestrator.tone}")

        if guardrail_instructions and not _has_baked_guardrails(system_prompt):
            parts.append(guardrail_instructions)

        if capability_catalog_text:
            parts.append(capability_catalog_text)

        if rag_context:
            parts.append("## Retrieved context\n" + rag_context)

        return "\n\n".join(part for part in parts if part)

    def build_from_bundle(
        self,
        *,
        bundle: RuntimeBundle,
        guardrail_instructions: str,
        rag_context: str = "",
    ) -> str:
        capability_catalog_text = self._catalog_builder.build(bundle=bundle)
        return self.build(
            orchestrator=bundle.orchestrator,
            guardrail_instructions=guardrail_instructions,
            capability_catalog_text=capability_catalog_text,
            rag_context=rag_context,
        )
