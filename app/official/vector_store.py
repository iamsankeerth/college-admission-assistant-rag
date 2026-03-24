from __future__ import annotations

from pathlib import Path

import chromadb

from app.models import RetrievedChunk, SourceTrustLabel
from app.official.corpus import OfficialChunk
from app.official.embedding import HashEmbeddingFunction


class OfficialVectorStore:
    def __init__(self, persist_dir: str | Path | None = None) -> None:
        base_dir = Path(__file__).resolve().parents[2] / "data" / "chroma"
        self.persist_dir = Path(persist_dir) if persist_dir else base_dir
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.client = chromadb.PersistentClient(path=str(self.persist_dir))
        self.collection = self.client.get_or_create_collection(
            name="official_documents",
            embedding_function=HashEmbeddingFunction(),
            metadata={"hnsw:space": "cosine"},
        )

    def upsert_chunks(self, chunks: list[OfficialChunk]) -> None:
        if not chunks:
            return
        self.collection.upsert(
            ids=[chunk.chunk_id for chunk in chunks],
            documents=[chunk.content for chunk in chunks],
            metadatas=[
                {
                    "doc_id": chunk.doc_id,
                    "college_name": chunk.college_name,
                    "title": chunk.title,
                    "url": chunk.url,
                    "source_kind": chunk.source_kind,
                }
                for chunk in chunks
            ],
        )

    def query(
        self, question: str, college_name: str | None = None, limit: int = 8
    ) -> list[RetrievedChunk]:
        where = {"college_name": college_name} if college_name else None
        result = self.collection.query(query_texts=[question], n_results=limit, where=where)
        ids = result.get("ids", [[]])[0]
        docs = result.get("documents", [[]])[0]
        metadatas = result.get("metadatas", [[]])[0]
        distances = result.get("distances", [[]])[0]
        retrieved: list[RetrievedChunk] = []
        for idx, chunk_id in enumerate(ids):
            metadata = metadatas[idx] if idx < len(metadatas) else {}
            distance = distances[idx] if idx < len(distances) else 1.0
            vector_score = max(0.0, 1.0 - float(distance))
            retrieved.append(
                RetrievedChunk(
                    chunk_id=chunk_id,
                    title=metadata.get("title", ""),
                    url=metadata.get("url", ""),
                    content=docs[idx] if idx < len(docs) else "",
                    vector_score=round(vector_score, 4),
                    combined_score=round(vector_score, 4),
                    trust_label=SourceTrustLabel.official_verified,
                )
            )
        return retrieved
