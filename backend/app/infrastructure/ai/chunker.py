import uuid

from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.domain.constants.knowledgebase_constants import DEFAULT_CHUNK_OVERLAP, DEFAULT_CHUNK_SIZE
from app.domain.models.source_document import ChunkDocument, SourceDocument

_CHARS_PER_TOKEN = 4


def chunk_documents(*, documents: list[SourceDocument]) -> list[ChunkDocument]:
    paragraph_splitter = RecursiveCharacterTextSplitter(
        chunk_size=4000,
        chunk_overlap=200,
        separators=["\n\n", "\n", " "],
    )
    token_splitter = RecursiveCharacterTextSplitter(
        chunk_size=DEFAULT_CHUNK_SIZE * _CHARS_PER_TOKEN,
        chunk_overlap=DEFAULT_CHUNK_OVERLAP * _CHARS_PER_TOKEN,
        separators=["\n", " ", ""],
    )

    chunks: list[ChunkDocument] = []
    for document in documents:
        paragraphs = paragraph_splitter.split_text(document.text)
        for paragraph_index, paragraph in enumerate(paragraphs):
            for piece in token_splitter.split_text(paragraph):
                text = piece.strip()
                if not text:
                    continue
                metadata = dict(document.metadata)
                metadata["paragraph_index"] = paragraph_index
                chunks.append(
                    ChunkDocument(
                        chunk_id=str(uuid.uuid4()),
                        text=text,
                        token_count=max(1, len(text) // _CHARS_PER_TOKEN),
                        metadata=metadata,
                    )
                )

    if not chunks:
        raise ValueError("No chunks produced from source documents")
    return chunks
