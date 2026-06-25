import json
import logging
import re
from typing import Any

from app.config import settings
from app.domain.models.source_document import ChunkDocument
from app.infrastructure.connectors.aws.bedrock_connector import BedrockConnector
from app.infrastructure.connectors.neo4j.neo4j_connector import Neo4jConnector

logger = logging.getLogger(__name__)


class Neo4jGraphIndex:
    def __init__(
        self,
        *,
        neo4j: Neo4jConnector | None = None,
        bedrock: BedrockConnector | None = None,
    ) -> None:
        self._neo4j = neo4j or Neo4jConnector(
            uri=settings.neo4j_uri,
            user=settings.neo4j_user,
            password=settings.neo4j_password,
            database=settings.neo4j_database,
        )
        self._bedrock = bedrock or BedrockConnector(
            region=settings.aws_region,
            llm_model_id=settings.bedrock_model_id,
            embed_model_id=settings.bedrock_embed_model_id,
        )

    def index_chunks(
        self,
        *,
        organization_id: str,
        knowledgebase_id: str,
        chunks: list[ChunkDocument],
    ) -> None:
        for chunk in chunks[:20]:
            entities, relationships = self._extract_graph(chunk.text)
            for entity in entities:
                self._neo4j.merge_node(
                    label="Entity",
                    key_property="id",
                    key_value=entity["id"],
                    properties={
                        "name": entity["name"],
                        "type": entity.get("type", "Concept"),
                        "organization_id": organization_id,
                        "knowledgebase_id": knowledgebase_id,
                        "chunk_id": chunk.chunk_id,
                    },
                )
            for relationship in relationships:
                self._neo4j.merge_relationship(
                    from_label="Entity",
                    from_key="id",
                    from_value=relationship["from_id"],
                    rel_type=relationship.get("type", "RELATED_TO"),
                    to_label="Entity",
                    to_key="id",
                    to_value=relationship["to_id"],
                    properties={
                        "organization_id": organization_id,
                        "knowledgebase_id": knowledgebase_id,
                    },
                )

        logger.info(
            "Indexed graph entities for knowledgebase_id=%s organization_id=%s",
            knowledgebase_id,
            organization_id,
        )

    def _extract_graph(self, text: str) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
        prompt = (
            "Extract entities and relationships from the text. "
            "Return strict JSON only with keys entities and relationships. "
            "Each entity needs id and name. "
            "Each relationship needs from_id, to_id, and type. "
            "Relationship type must be SCREAMING_SNAKE_CASE with no spaces "
            "(examples: PART_OF, LOCATED_IN, RELATED_TO).\n\n"
            f"Text:\n{text[:4000]}"
        )
        raw = self._bedrock.invoke_llm(prompt=prompt, max_tokens=1024, temperature=0.0)
        payload = self._parse_json(raw)
        entities = payload.get("entities") or []
        relationships = payload.get("relationships") or []
        return entities, relationships

    @staticmethod
    def _parse_json(raw: str) -> dict[str, Any]:
        match = re.search(r"\{.*\}", raw, flags=re.DOTALL)
        if not match:
            return {"entities": [], "relationships": []}
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            logger.warning("Failed to parse graph extraction JSON")
            return {"entities": [], "relationships": []}
