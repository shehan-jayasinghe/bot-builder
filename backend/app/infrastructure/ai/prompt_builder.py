from langchain_core.prompts import ChatPromptTemplate

from app.domain.constants.agent_defaults import GuardrailDef, get_responsibilities


def _format_responsibilities(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def _format_guardrails(guardrails: list[GuardrailDef]) -> str:
    enabled = [g for g in guardrails if g.get("enabled", True)]
    if not enabled:
        return "- Stay helpful, accurate, and safe."
    return "\n".join(f"- {g['label']}: {g['instruction']}" for g in enabled)


def build_system_prompt(
    *,
    name: str,
    description: str | None,
    industry: str,
    agent_type: str | None,
    personality: str,
    tone: str,
    guardrails: list[GuardrailDef],
) -> str:
    responsibilities = _format_responsibilities(
        get_responsibilities(industry=industry, agent_type=agent_type),
    )
    guardrails_text = _format_guardrails(guardrails)
    role_label = agent_type.replace("_", " ").title() if agent_type else "Assistant"
    description_text = description or "Assist customers professionally and accurately."

    template = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are an AI-powered {role_label} for {company_name}.\n"
                "{description}\n\n"
                "Core responsibilities:\n{responsibilities}",
            ),
            ("system", "Personality: {personality}"),
            ("system", "Tone: {tone}"),
            ("system", "Safety and guardrails:\n{guardrails_text}"),
        ],
    )

    messages = template.format_messages(
        role_label=role_label,
        company_name=name,
        description=description_text,
        responsibilities=responsibilities,
        personality=personality,
        tone=tone,
        guardrails_text=guardrails_text,
    )
    return "\n\n".join(str(message.content) for message in messages if message.content)
