from bson import ObjectId

from app.domain.models.assistant import LLMConfig
from app.services.assistant_loader import AssistantLoader


def test_to_dialogue_assistant_maps_mongo_document() -> None:
    agent_id = ObjectId()
    agent_doc = {
        "_id": agent_id,
        "name": "abc bank",
        "system_prompt": "You are a support agent.",
        "personality": "Professional",
        "tone": "Friendly",
        "llm_config": {
            "model_id": "anthropic.claude-3-5-sonnet-20241022-v2:0",
            "temperature": 0.5,
            "max_output_tokens": 512,
        },
        "skill_ids": ["transactions_analysis"],
        "workflow_ids": ["dispute_process"],
        "knowledge_base_ids": ["kb_001"],
        "status": "published",
    }

    assistant = AssistantLoader._to_dialogue_assistant(
        agent_doc=agent_doc,
        webhook_id="demo-webhook-id",
    )

    assert assistant.id == str(agent_id)
    assert assistant.name == "abc bank"
    assert assistant.webhook_id == "demo-webhook-id"
    assert assistant.llm_config == LLMConfig(
        model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
        temperature=0.5,
        max_output_tokens=512,
    )
    assert assistant.skill_ids == ["transactions_analysis"]
    assert assistant.workflow_ids == ["dispute_process"]
    assert assistant.knowledge_base_ids == ["kb_001"]
    assert "Personality: Professional" in assistant.build_system_prompt()


def test_build_system_prompt_without_personality_or_tone() -> None:
    assistant = AssistantLoader._to_dialogue_assistant(
        agent_doc={
            "_id": ObjectId(),
            "name": "Demo",
            "system_prompt": "Base prompt.",
            "status": "published",
        },
        webhook_id="wh-1",
    )

    assert assistant.build_system_prompt() == "Base prompt."
