from llama_index.core.schema import TextNode

from app.domain.models.source_document import ChunkDocument


def chunks_to_text_nodes(
    *,
    chunks: list[ChunkDocument],
    organization_id: str,
    knowledgebase_id: str,
) -> list[TextNode]:
    nodes: list[TextNode] = []
    for chunk in chunks:
        text = chunk.text.strip()
        if not text:
            continue
        nodes.append(
            TextNode(
                id_=chunk.chunk_id,
                text=text,
                metadata={
                    "chunk_id": chunk.chunk_id,
                    "knowledgebase_id": knowledgebase_id,
                    "organization_id": organization_id,
                    "text": text,
                    **chunk.metadata,
                },
            ),
        )
    return nodes
