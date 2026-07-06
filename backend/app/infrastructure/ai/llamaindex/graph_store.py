from llama_index.graph_stores.neo4j import Neo4jPropertyGraphStore

from app.config import settings


def build_neo4j_property_graph_store() -> Neo4jPropertyGraphStore:
    return Neo4jPropertyGraphStore(
        username=settings.neo4j_user,
        password=settings.neo4j_password,
        url=settings.neo4j_uri,
        database=settings.neo4j_database,
    )
