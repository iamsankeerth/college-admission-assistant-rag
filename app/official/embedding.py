from __future__ import annotations

import hashlib
import math
from typing import Protocol

from app.config import settings


class EmbeddingModel(Protocol):
    def embed_documents(self, texts: list[str]) -> list[list[float]]: ...
    def embed_query(self, text: str) -> list[float]: ...
    def name(self) -> str: ...


class HashEmbeddingModel:
    """Deterministic fallback used for local tests or offline environments."""

    def __init__(self, dimension: int = 256) -> None:
        self.dimension = dimension

    def name(self) -> str:
        return "hash-embedding"

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._embed(text)

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimension
        for token in text.lower().split():
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            idx = int.from_bytes(digest[:4], "big") % self.dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[idx] += sign
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]


class SentenceTransformerEmbeddingModel:
    def __init__(self, model_name: str) -> None:
        from sentence_transformers import SentenceTransformer

        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def name(self) -> str:
        return self.model_name

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return [embedding.tolist() for embedding in embeddings]

    def embed_query(self, text: str) -> list[float]:
        embedding = self.model.encode([text], normalize_embeddings=True)[0]
        return embedding.tolist()


def build_embedding_model() -> EmbeddingModel:
    backend = settings.embedding_backend.lower()
    if backend == "hash":
        return HashEmbeddingModel()

    try:
        return SentenceTransformerEmbeddingModel(settings.embedding_model_name)
    except Exception:
        return HashEmbeddingModel()
