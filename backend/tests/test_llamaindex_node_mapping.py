from llama_index.core.schema import NodeWithScore, TextNode

from app.infrastructure.ai.llamaindex.node_mapping import hits_from_nodes


def test_hits_from_nodes_filters_by_min_score() -> None:
    nodes = [
        NodeWithScore(
            node=TextNode(text="high", metadata={"chunk_id": "c1"}),
            score=0.91,
        ),
        NodeWithScore(
            node=TextNode(text="low", metadata={"chunk_id": "c2"}),
            score=0.4,
        ),
    ]

    hits = hits_from_nodes(nodes, min_score=0.7)

    assert len(hits) == 1
    assert hits[0]["text"] == "high"
    assert hits[0]["chunk_id"] == "c1"
    assert hits[0]["score"] == 0.91


def test_hits_from_nodes_uses_metadata_text_fallback() -> None:
    nodes = [
        NodeWithScore(
            node=TextNode(text="", metadata={"chunk_id": "c1", "text": "from metadata"}),
            score=0.8,
        ),
    ]

    hits = hits_from_nodes(nodes, min_score=0.0)

    assert hits[0]["text"] == "from metadata"
