from __future__ import annotations

from pathlib import Path

import chromadb
from chromadb.errors import InvalidArgumentError

from app.config import settings
from app.models import RetrievedChunk, SourceTrustLabel
from app.official.corpus import OfficialChunk
from app.official.embedding import EmbeddingModel, build_embedding_model


class OfficialVectorStore:
    def __init__(
        self,
        persist_dir: str | Path | None = None,
        embedding_model: EmbeddingModel | None = None,
    ) -> None:
        base_dir = Path(__file__).resolve().parents[2] / settings.chroma_persist_dir
        self.persist_dir = Path(persist_dir) if persist_dir else base_dir
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.embedding_model = embedding_model or build_embedding_model()
        model_suffix = (
            self.embedding_model.name()
            .replace("/", "_")
            .replace("-", "_")
            .replace(".", "_")
            .lower()
        )
        self.collection_name = f"{settings.chroma_collection_name}_{model_suffix[:48]}"
        self.client = chromadb.PersistentClient(path=str(self.persist_dir))
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"hnsw:space": "cosine"},
        )

    def upsert_chunks(self, chunks: list[OfficialChunk]) -> None:
        if not chunks:
            return
        embeddings = self.embedding_model.embed_documents([chunk.content for chunk in chunks])
        try:
            self.collection.upsert(
                ids=[chunk.chunk_id for chunk in chunks],
                embeddings=embeddings,
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
        except InvalidArgumentError:
            self.client.delete_collection(self.collection_name)
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"},
            )
            self.collection.upsert(
                ids=[chunk.chunk_id for chunk in chunks],
                embeddings=embeddings,
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
        self, question: str, college_name: str | None = None, limit: int | None = None
    ) -> list[RetrievedChunk]:
        n_results = limit or settings.retrieval_top_k_vector
        where = {"college_name": college_name} if college_name else None
        query_embedding = self.embedding_model.embed_query(question)
        result = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=where,
        )
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
                    doc_id=metadata.get("doc_id", ""),
                    college_name=metadata.get("college_name", ""),
                    title=metadata.get("title", ""),
                    url=metadata.get("url", ""),
                    content=docs[idx] if idx < len(docs) else "",
                    source_kind=metadata.get("source_kind", "official"),
                    vector_score=round(vector_score, 4),
                    combined_score=round(vector_score, 4),
                    retrieval_stage="vector",
                    trust_label=SourceTrustLabel.official_verified,
                )
            )
        return retrieved
