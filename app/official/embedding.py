from __future__ import annotations

import hashlib
import math


class HashEmbeddingFunction:
    """Deterministic lightweight embedding fallback for local development.

    This keeps the vector store fully operational without requiring a large
    transformer model download. The interface is compatible with Chroma.
    """

    def __init__(self, dimension: int = 256) -> None:
        self.dimension = dimension

    def __call__(self, input: list[str]) -> list[list[float]]:
        return [self._embed(text) for text in input]

    def name(self=None) -> str:
        return "hash-embedding"

    def embed_documents(self, input: list[str]) -> list[list[float]]:
        return self.__call__(input)

    def embed_query(self, input: list[str]) -> list[list[float]]:
        return self.__call__(input)

    def is_legacy(self) -> bool:
        return False

    def supported_spaces(self) -> list[str]:
        return ["cosine", "l2", "ip"]

    def get_config(self) -> dict[str, int | str]:
        return {"name": self.name(), "dimension": self.dimension}

    @classmethod
    def build_from_config(cls, config: dict) -> "HashEmbeddingFunction":
        return cls(dimension=int(config.get("dimension", 256)))

    def _embed(self, text: str) -> list[float]:
        vector = [0.0] * self.dimension
        for token in text.lower().split():
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            idx = int.from_bytes(digest[:4], "big") % self.dimension
            sign = 1.0 if digest[4] % 2 == 0 else -1.0
            vector[idx] += sign
        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]
