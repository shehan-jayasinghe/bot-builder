import logging
import os
import re
from typing import Any

from neo4j import GraphDatabase

logger = logging.getLogger(__name__)


def normalize_rel_type(rel_type: str) -> str:
    """Convert LLM relationship labels to valid Neo4j Cypher type identifiers."""
    cleaned = re.sub(r"[^A-Za-z0-9_]", "_", rel_type.strip().upper())
    cleaned = re.sub(r"_+", "_", cleaned).strip("_")
    if not cleaned:
        return "RELATED_TO"
    if not cleaned[0].isalpha():
        cleaned = f"REL_{cleaned}"
    return cleaned


class Neo4jConnector:
    """Graph DB connector for graph knowledge bases."""

    def __init__(
        self,
        *,
        uri: str | None = None,
        user: str | None = None,
        password: str | None = None,
        database: str | None = None,
    ) -> None:
        self._uri = uri or os.getenv("NEO4J_URI", "bolt://localhost:7687")
        self._user = user or os.getenv("NEO4J_USER", "neo4j")
        self._password = password or os.getenv("NEO4J_PASSWORD", "changeme")
        self._database = database or os.getenv("NEO4J_DATABASE", "neo4j")
        self._driver: Any = None

    @property
    def uri(self) -> str:
        return self._uri

    def _get_driver(self) -> Any:
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                self._uri,
                auth=(self._user, self._password),
            )
        return self._driver

    def close(self) -> None:
        if self._driver is not None:
            self._driver.close()
            self._driver = None

    def ping(self) -> bool:
        try:
            self._get_driver().verify_connectivity()
            return True
        except Exception:
            logger.warning("Neo4j not reachable at %s", self._uri)
            return False

    def run_write(self, *, query: str, parameters: dict[str, Any] | None = None) -> None:
        with self._get_driver().session(database=self._database) as session:
            session.execute_write(lambda tx: tx.run(query, parameters or {}))

    def run_read(self, *, query: str, parameters: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        with self._get_driver().session(database=self._database) as session:
            result = session.run(query, parameters or {})
            return [record.data() for record in result]

    def merge_node(
        self,
        *,
        label: str,
        key_property: str,
        key_value: str,
        properties: dict[str, Any] | None = None,
    ) -> None:
        props = properties or {}
        props[key_property] = key_value
        set_clause = ", ".join(f"n.{k} = ${k}" for k in props)
        query = f"MERGE (n:{label} {{{key_property}: ${key_property}}}) SET {set_clause}"
        self.run_write(query=query, parameters=props)

    def merge_relationship(
        self,
        *,
        from_label: str,
        from_key: str,
        from_value: str,
        rel_type: str,
        to_label: str,
        to_key: str,
        to_value: str,
        properties: dict[str, Any] | None = None,
    ) -> None:
        props = dict(properties or {})
        original_type = rel_type
        safe_rel_type = normalize_rel_type(rel_type)
        if original_type != safe_rel_type:
            props.setdefault("original_type", original_type)

        set_clause = " SET r += $props" if props else ""
        query = (
            f"MATCH (a:{from_label} {{{from_key}: $from_value}}), "
            f"(b:{to_label} {{{to_key}: $to_value}}) "
            f"MERGE (a)-[r:{safe_rel_type}]->(b){set_clause}"
        )
        params: dict[str, Any] = {
            "from_value": from_value,
            "to_value": to_value,
            "props": props,
        }
        self.run_write(query=query, parameters=params)
