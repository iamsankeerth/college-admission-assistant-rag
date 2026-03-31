from __future__ import annotations

from typing import Protocol

from app.config import settings
from app.models import RetrievedChunk


class Reranker(Protocol):
    def rerank(self, query: str, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]: ...
    def name(self) -> str: ...


class HeuristicReranker:
    def name(self) -> str:
        return "heuristic-reranker"

    def rerank(self, query: str, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        query_terms = set(query.lower().split())
        rescored: list[RetrievedChunk] = []
        for idx, chunk in enumerate(chunks):
            overlap = len(query_terms & set(chunk.content.lower().split()))
            score = chunk.combined_score + overlap * 0.02
            rescored.append(
                chunk.model_copy(
                    update={
                        "rerank_score": round(score, 4),
                        "retrieval_stage": "reranked",
                        "rank": idx + 1,
                    }
                )
            )
        rescored.sort(key=lambda item: item.rerank_score or 0.0, reverse=True)
        for idx, chunk in enumerate(rescored):
            chunk.rank = idx + 1
        return rescored


class CrossEncoderReranker:
    def __init__(self, model_name: str) -> None:
        from sentence_transformers import CrossEncoder

        self.model_name = model_name
        self.model = CrossEncoder(model_name)

    def name(self) -> str:
        return self.model_name

    def rerank(self, query: str, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        if not chunks:
            return []
        pairs = [(query, chunk.content) for chunk in chunks]
        scores = self.model.predict(pairs)
        rescored: list[RetrievedChunk] = []
        for idx, (chunk, score) in enumerate(zip(chunks, scores, strict=True)):
            rescored.append(
                chunk.model_copy(
                    update={
                        "rerank_score": round(float(score), 4),
                        "retrieval_stage": "reranked",
                        "rank": idx + 1,
                    }
                )
            )
        rescored.sort(key=lambda item: item.rerank_score or 0.0, reverse=True)
        for idx, chunk in enumerate(rescored):
            chunk.rank = idx + 1
        return rescored


def build_reranker() -> Reranker:
    backend = settings.reranker_backend.lower()
    if backend == "heuristic":
        return HeuristicReranker()

    try:
        return CrossEncoderReranker(settings.reranker_model_name)
    except Exception:
        return HeuristicReranker()
