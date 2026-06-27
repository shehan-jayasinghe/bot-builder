from langchain_core.prompts import ChatPromptTemplate

from app.domain.constants.agent_defaults import get_responsibilities


def _format_responsibilities(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def build_system_prompt(
    *,
    name: str,
    description: str | None,
    industry: str,
    agent_type: str | None,
) -> str:
    """Build layer-[1] base prompt only.

    Personality, tone, and guardrails are applied at chat runtime via
    FinalPromptBuilder so they are not duplicated in stored system_prompt.
    """
    responsibilities = _format_responsibilities(
        get_responsibilities(industry=industry, agent_type=agent_type),
    )
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
        ],
    )

    messages = template.format_messages(
        role_label=role_label,
        company_name=name,
        description=description_text,
        responsibilities=responsibilities,
    )
    return "\n\n".join(str(message.content) for message in messages if message.content)
