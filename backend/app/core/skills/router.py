from typing import Any


class SkillRouter:
    async def route(self, *, user_message: str, skills: list[dict[str, Any]]) -> str | None:
        """
        Select and run a skill (workflow, function, or knowledge base).

        TODO:
          - LLM tool-calling to pick skill
          - execute workflow / function / kb skill
          - emit trace event: tool_start
        """
        _ = user_message, skills
        return None
