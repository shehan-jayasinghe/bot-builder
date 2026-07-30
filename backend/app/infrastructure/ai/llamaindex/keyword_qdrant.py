"""BM25 sparse-vector keyword search backed by Qdrant.

Replaces local-disk ``BM25Retriever.persist`` / ``from_persist_dir`` with
Qdrant sparse-vector upsert and search so that keyword indexes are durable
and shared across API + Celery workers.
"""

import logging
import math
import re
import uuid
from collections import Counter
from typing import Any

from qdrant_client.http.models import (
    Modifier,
    NamedSparseVector,
    PointStruct,
    SparseVector,
    SparseVectorParams,
)

from app.domain.models.source_document import ChunkDocument
from app.infrastructure.connectors.qdrant.qdrant_connector import QdrantConnector

logger = logging.getLogger(__name__)

_WORD_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> list[str]:
    return _WORD_RE.findall(text.lower())


def _term_id(term: str) -> int:
    """Deterministic 32-bit integer for a term (Qdrant sparse index)."""
    return uuid.uuid5(uuid.NAMESPACE_URL, term).int & 0x7FFFFFFF


def _build_sparse_vector(tokens: list[str]) -> SparseVector:
    """TF-log sparse vector from a bag of tokens."""
    counts = Counter(tokens)
    indices: list[int] = []
    values: list[float] = []
    for term, count in counts.items():
        indices.append(_term_id(term))
        values.append(1.0 + math.log(count))
    return SparseVector(indices=indices, values=values)


SPARSE_VECTOR_NAME = "bm25"


def ensure_sparse_collection(
    *,
    client: Any,
    collection_name: str,
) -> None:
    if client.collection_exists(collection_name):
        return
    client.create_collection(
        collection_name=collection_name,
        vectors_config={},
        sparse_vectors_config={
            SPARSE_VECTOR_NAME: SparseVectorParams(
                modifier=Modifier.IDF,
            ),
        },
    )


def upsert_keyword_chunks(
    *,
    qdrant: QdrantConnector,
    collection_name: str,
    chunks: list[ChunkDocument],
    organization_id: str,
    knowledgebase_id: str,
) -> None:
    client = qdrant._get_client()
    ensure_sparse_collection(client=client, collection_name=collection_name)

    points: list[PointStruct] = []
    for chunk in chunks:
        tokens = _tokenize(chunk.text)
        if not tokens:
            continue
        sparse = _build_sparse_vector(tokens)
        point_id = str(uuid.uuid5(uuid.NAMESPACE_URL, chunk.chunk_id))
        points.append(
            PointStruct(
                id=point_id,
                vector={SPARSE_VECTOR_NAME: sparse},
                payload={
                    "text": chunk.text,
                    "chunk_id": chunk.chunk_id,
                    "knowledgebase_id": knowledgebase_id,
                    "organization_id": organization_id,
                    "metadata": chunk.metadata,
                },
            ),
        )

    if points:
        client.upsert(collection_name=collection_name, points=points)

    logger.info(
        "Upserted %s sparse keyword points to Qdrant collection %s",
        len(points),
        collection_name,
    )


def search_keyword_sparse(
    *,
    qdrant: QdrantConnector,
    collection_name: str,
    query: str,
    top_k: int = 5,
    min_score: float = 0.0,
) -> list[dict[str, Any]]:
    client = qdrant._get_client()
    if not client.collection_exists(collection_name):
        return []

    tokens = _tokenize(query)
    if not tokens:
        return []

    sparse = _build_sparse_vector(tokens)

    raw_hits = client.query_points(
        collection_name=collection_name,
        query=sparse,
        using=SPARSE_VECTOR_NAME,
        limit=top_k,
    ).points

    hits: list[dict[str, Any]] = []
    for hit in raw_hits:
        score = float(hit.score or 0.0)
        if score < min_score:
            continue
        payload = hit.payload or {}
        text = str(payload.get("text", "")).strip()
        if not text:
            continue
        hits.append(
            {
                "text": text,
                "score": score,
                "chunk_id": payload.get("chunk_id"),
            },
        )
    return hits
