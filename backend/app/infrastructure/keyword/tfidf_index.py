import logging
from pathlib import Path
from typing import Any

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer

from app.config import settings
from app.domain.models.source_document import ChunkDocument

logger = logging.getLogger(__name__)


class TfidfIndex:
    def __init__(self, *, base_dir: str | None = None) -> None:
        self._base_dir = Path(base_dir or settings.tfidf_index_dir)

    def save(
        self,
        *,
        organization_id: str,
        knowledgebase_id: str,
        chunks: list[ChunkDocument],
    ) -> str:
        texts = [chunk.text for chunk in chunks]
        vectorizer = TfidfVectorizer(stop_words="english", max_features=50000)
        matrix = vectorizer.fit_transform(texts)

        target_dir = self._base_dir / organization_id
        target_dir.mkdir(parents=True, exist_ok=True)
        index_path = target_dir / f"{knowledgebase_id}.joblib"

        payload = {
            "vectorizer": vectorizer,
            "matrix": matrix,
            "chunk_ids": [chunk.chunk_id for chunk in chunks],
            "texts": texts,
        }
        joblib.dump(payload, index_path)
        logger.info("Saved TF-IDF index to %s", index_path)
        return str(index_path)

    def load(self, *, organization_id: str, knowledgebase_id: str) -> dict[str, Any]:
        index_path = self._base_dir / organization_id / f"{knowledgebase_id}.joblib"
        if not index_path.exists():
            raise FileNotFoundError(f"TF-IDF index not found: {index_path}")
        return joblib.load(index_path)

    def search(
        self,
        *,
        organization_id: str,
        knowledgebase_id: str,
        query: str,
        top_k: int = 5,
    ) -> list[dict[str, Any]]:
        index = self.load(
            organization_id=organization_id,
            knowledgebase_id=knowledgebase_id,
        )
        vectorizer: TfidfVectorizer = index["vectorizer"]
        matrix = index["matrix"]
        texts: list[str] = index["texts"]
        chunk_ids: list[str] = index.get("chunk_ids") or []

        if not texts:
            return []

        query_vec = vectorizer.transform([query])
        scores = (matrix * query_vec.T).toarray().flatten()
        ranked_indices = scores.argsort()[::-1][:top_k]

        hits: list[dict[str, Any]] = []
        for idx in ranked_indices:
            score = float(scores[idx])
            if score <= 0:
                continue
            text = str(texts[idx]).strip()
            if not text:
                continue
            chunk_id = chunk_ids[idx] if idx < len(chunk_ids) else None
            hits.append({"text": text, "score": score, "chunk_id": chunk_id})
        return hits
