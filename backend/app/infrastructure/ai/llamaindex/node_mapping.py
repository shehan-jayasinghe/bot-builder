from typing import Any

from llama_index.core.schema import MetadataMode, NodeWithScore


def hits_from_nodes(
    nodes: list[NodeWithScore],
    *,
    min_score: float = 0.0,
) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for item in nodes:
        score = float(item.score or 0.0)
        if score < min_score:
            continue
        node = item.node
        text = node.get_content(metadata_mode=MetadataMode.NONE).strip()
        if not text:
            text = str(node.metadata.get("text", "")).strip()
        if not text:
            continue
        chunk_id = node.metadata.get("chunk_id")
        if chunk_id is not None:
            chunk_id = str(chunk_id)
        hits.append(
            {
                "text": text,
                "score": score,
                "chunk_id": chunk_id,
            },
        )
    return hits
