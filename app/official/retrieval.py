from __future__ import annotations

import math
from collections import Counter

from app.models import RetrievedChunk, SourceTrustLabel
from app.official.corpus import OfficialChunk, OfficialCorpus, tokenize
from app.official.vector_store import OfficialVectorStore


class HybridRetriever:
    def __init__(self, corpus: OfficialCorpus, vector_store: OfficialVectorStore) -> None:
        self.corpus = corpus
        self.vector_store = vector_store
        self._refresh_stats()

    def refresh(self) -> None:
        self.corpus.refresh()
        self._refresh_stats()

    def retrieve(
        self, question: str, college_name: str | None = None, limit: int = 6
    ) -> list[RetrievedChunk]:
        query_tokens = tokenize(question)
        lexical_candidates = self._lexical_candidates(query_tokens, college_name, limit * 3)
        vector_candidates = self.vector_store.query(question, college_name, limit * 3)

        merged: dict[str, RetrievedChunk] = {}
        for candidate in lexical_candidates:
            merged[candidate.chunk_id] = candidate

        for candidate in vector_candidates:
            existing = merged.get(candidate.chunk_id)
            if existing is None:
                merged[candidate.chunk_id] = candidate
                continue
            existing.vector_score = max(existing.vector_score, candidate.vector_score)
            existing.combined_score = round(
                existing.lexical_score * 0.55 + existing.vector_score * 0.45, 4
            )

        for candidate in merged.values():
            candidate.combined_score = round(
                candidate.lexical_score * 0.55 + candidate.vector_score * 0.45, 4
            )

        ranked = sorted(merged.values(), key=lambda item: item.combined_score, reverse=True)
        return ranked[:limit]

    def _refresh_stats(self) -> None:
        self.doc_freq = self._build_document_frequency(self.corpus.chunks)
        self.chunk_count = max(len(self.corpus.chunks), 1)
        self.avg_chunk_length = (
            sum(len(chunk.tokens) for chunk in self.corpus.chunks) / self.chunk_count
            if self.corpus.chunks
            else 1.0
        )

    def _lexical_candidates(
        self, query_tokens: list[str], college_name: str | None, limit: int
    ) -> list[RetrievedChunk]:
        candidate_chunks = [
            chunk
            for chunk in self.corpus.chunks
            if not college_name or chunk.college_name.lower() == college_name.lower()
        ]
        if not candidate_chunks:
            candidate_chunks = self.corpus.chunks

        scored: list[RetrievedChunk] = []
        for chunk in candidate_chunks:
            lexical = self._bm25_score(query_tokens, chunk)
            vector_like = self._tfidf_cosine(query_tokens, chunk)
            combined = lexical * 0.55 + vector_like * 0.45
            if combined <= 0:
                continue
            scored.append(
                RetrievedChunk(
                    chunk_id=chunk.chunk_id,
                    title=chunk.title,
                    url=chunk.url,
                    content=chunk.content,
                    lexical_score=round(lexical, 4),
                    vector_score=0.0,
                    combined_score=round(combined, 4),
                    trust_label=SourceTrustLabel.official_verified,
                )
            )

        scored.sort(key=lambda item: item.combined_score, reverse=True)
        return scored[:limit]

    def _build_document_frequency(self, chunks: list[OfficialChunk]) -> dict[str, int]:
        doc_freq: dict[str, int] = {}
        for chunk in chunks:
            for token in set(chunk.tokens):
                doc_freq[token] = doc_freq.get(token, 0) + 1
        return doc_freq

    def _idf(self, token: str) -> float:
        df = self.doc_freq.get(token, 0)
        return math.log((self.chunk_count - df + 0.5) / (df + 0.5) + 1.0)

    def _bm25_score(self, query_tokens: list[str], chunk: OfficialChunk) -> float:
        if not query_tokens or not chunk.tokens:
            return 0.0
        k1 = 1.5
        b = 0.75
        frequencies = Counter(chunk.tokens)
        score = 0.0
        for token in query_tokens:
            tf = frequencies.get(token, 0)
            if tf == 0:
                continue
            idf = self._idf(token)
            numerator = tf * (k1 + 1)
            denominator = tf + k1 * (1 - b + b * len(chunk.tokens) / self.avg_chunk_length)
            score += idf * numerator / denominator
        return score

    def _tfidf_cosine(self, query_tokens: list[str], chunk: OfficialChunk) -> float:
        if not query_tokens or not chunk.tokens:
            return 0.0
        query_counts = Counter(query_tokens)
        chunk_counts = Counter(chunk.tokens)
        shared_tokens = set(query_counts) | set(chunk_counts)
        numerator = 0.0
        query_norm = 0.0
        chunk_norm = 0.0
        for token in shared_tokens:
            idf = self._idf(token)
            q = query_counts.get(token, 0) * idf
            c = chunk_counts.get(token, 0) * idf
            numerator += q * c
            query_norm += q * q
            chunk_norm += c * c
        if query_norm == 0 or chunk_norm == 0:
            return 0.0
        return numerator / math.sqrt(query_norm * chunk_norm)
