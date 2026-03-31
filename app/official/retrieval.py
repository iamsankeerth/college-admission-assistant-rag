from __future__ import annotations

import math
from collections import Counter
from typing import Protocol

from app.config import settings
from app.models import EvidenceDecision, RetrievalTrace, RetrievedChunk, SourceTrustLabel
from app.official.cache import RetrievalCache
from app.official.corpus import OfficialChunk, OfficialCorpus, tokenize
from app.official.query_normalizer import (
    expand_query,
    extract_query_terms,
    normalize_college_name,
    normalize_query,
    normalize_for_cache,
)
from app.official.reranker import Reranker, build_reranker
from app.official.vector_store import OfficialVectorStore


STOPWORDS = {
    "a", "an", "and", "are", "at", "do", "does", "exact", "for", "how",
    "in", "is", "look", "of", "official", "say", "should", "sources",
    "the", "what", "where",
}


class QueryNormalizer(Protocol):
    def normalize(self, query: str) -> str: ...
    def expand(self, query: str) -> str: ...
    def extract_terms(self, query: str) -> list[str]: ...


class DefaultQueryNormalizer:
    def normalize(self, query: str) -> str:
        return normalize_query(query)

    def expand(self, query: str) -> str:
        if not settings.query_normalization_enabled:
            return query
        return expand_query(query)

    def extract_terms(self, query: str) -> list[str]:
        return extract_query_terms(query)


class HybridRetriever:
    def __init__(
        self,
        corpus: OfficialCorpus,
        vector_store: OfficialVectorStore,
        reranker: Reranker | None = None,
        cache: RetrievalCache | None = None,
        query_normalizer: QueryNormalizer | None = None,
    ) -> None:
        self.corpus = corpus
        self.vector_store = vector_store
        self.reranker = reranker or build_reranker()
        self.cache = cache or RetrievalCache()
        self.query_normalizer = query_normalizer or DefaultQueryNormalizer()
        self._refresh_stats()

    def refresh(self) -> None:
        self.corpus.refresh()
        self._refresh_stats()
        self.vector_store.upsert_chunks(self.corpus.chunks)
        if settings.result_cache_enabled:
            self.cache.invalidate()

    def retrieve(
        self, question: str, college_name: str | None = None, limit: int | None = None
    ) -> tuple[list[RetrievedChunk], RetrievalTrace]:
        final_limit = limit or settings.retrieval_top_k_rerank

        original_question = question
        question = self.query_normalizer.normalize(question)
        question = self.query_normalizer.expand(question)

        normalized_college = normalize_college_name(college_name) if college_name else None
        cache_key = normalize_for_cache(question, normalized_college or college_name)

        if settings.result_cache_enabled:
            cached = self.cache.get(cache_key, normalized_college or college_name)
            if cached is not None:
                reranked = self._apply_mmr(question, cached[:final_limit])
                decision = self.make_decision(reranked)
                trace = RetrievalTrace(
                    lexical_candidates=[],
                    vector_candidates=[],
                    reranked_candidates=reranked,
                    decision=decision,
                )
                return reranked, trace

        query_tokens = tokenize(question)
        self._active_query_tokens = query_tokens

        lexical_candidates = self._lexical_candidates(
            query_tokens,
            normalized_college or college_name,
            settings.retrieval_top_k_lexical,
        )
        vector_candidates = self.vector_store.query(
            original_question,
            normalized_college or college_name,
            settings.retrieval_top_k_vector,
        )

        merged: dict[str, RetrievedChunk] = {}
        for candidate in lexical_candidates + vector_candidates:
            existing = merged.get(candidate.chunk_id)
            if existing is None:
                merged[candidate.chunk_id] = candidate
                continue
            merged[candidate.chunk_id] = existing.model_copy(
                update={
                    "lexical_score": max(existing.lexical_score, candidate.lexical_score),
                    "vector_score": max(existing.vector_score, candidate.vector_score),
                    "combined_score": round(
                        max(existing.lexical_score, candidate.lexical_score) * 0.5
                        + max(existing.vector_score, candidate.vector_score) * 0.5,
                        4,
                    ),
                    "retrieval_stage": "hybrid",
                }
            )

        hybrid_candidates = list(merged.values())
        for candidate in hybrid_candidates:
            candidate.combined_score = round(
                candidate.lexical_score * 0.5 + candidate.vector_score * 0.5,
                4,
            )
            if candidate.retrieval_stage == "unknown":
                candidate.retrieval_stage = "hybrid"

        reranked = self.reranker.rerank(question, hybrid_candidates)
        reranked = self._apply_mmr(question, reranked)

        if settings.result_cache_enabled:
            self.cache.set(cache_key, normalized_college or college_name, reranked)

        reranked = reranked[:final_limit]
        decision = self.make_decision(reranked)
        trace = RetrievalTrace(
            lexical_candidates=lexical_candidates,
            vector_candidates=vector_candidates,
            reranked_candidates=reranked,
            decision=decision,
        )
        return reranked, trace

    def _apply_mmr(
        self, query: str, chunks: list[RetrievedChunk]
    ) -> list[RetrievedChunk]:
        if not chunks or settings.mmr_diversity_factor <= 0:
            return chunks

        try:
            import numpy as np
        except ImportError:
            return chunks

        lambda_param = settings.mmr_diversity_factor
        try:
            query_embedding = self.vector_store.embedding_model.embed_query(query)
            doc_embeddings = self.vector_store.embedding_model.embed_documents(
                [c.content for c in chunks]
            )
        except Exception:
            return chunks

        query_vec = np.array(query_embedding, dtype=np.float32)
        q_norm = np.linalg.norm(query_vec)
        if q_norm > 0:
            query_vec = query_vec / q_norm

        doc_vecs = []
        for emb in doc_embeddings:
            v = np.array(emb, dtype=np.float32)
            n = np.linalg.norm(v)
            doc_vecs.append(v / n if n > 0 else v)

        selected: list[RetrievedChunk] = []
        remaining_indices = list(range(len(chunks)))

        while remaining_indices:
            if not selected:
                idx = remaining_indices.pop(0)
                selected.append(chunks[idx])
                continue

            best_score = float("-inf")
            best_pos = 0

            for pos, idx in enumerate(remaining_indices):
                relevance = chunks[idx].rerank_score or chunks[idx].combined_score
                similarity = float(np.dot(query_vec, doc_vecs[idx]))
                mmr_score = lambda_param * similarity + (1 - lambda_param) * relevance
                if mmr_score > best_score:
                    best_score = mmr_score
                    best_pos = pos

            chosen_idx = remaining_indices.pop(best_pos)
            selected.append(chunks[chosen_idx])

        for i, chunk in enumerate(selected):
            chunk.rank = i + 1
        return selected

    def make_decision(self, chunks: list[RetrievedChunk]) -> EvidenceDecision:
        if not chunks:
            return EvidenceDecision(
                answerable=False,
                reason="no_retrieved_chunks",
                top_score=0.0,
                threshold=settings.min_rerank_score_to_answer,
            )
        top_rerank = chunks[0].rerank_score
        top_score = (
            top_rerank
            if top_rerank is not None and top_rerank >= 0
            else chunks[0].combined_score
        )
        coverage = self._salient_query_coverage(chunks)
        if top_score < settings.min_rerank_score_to_answer:
            return EvidenceDecision(
                answerable=False,
                reason="top_evidence_score_below_threshold",
                top_score=top_score,
                threshold=settings.min_rerank_score_to_answer,
            )
        if coverage < 0.35:
            return EvidenceDecision(
                answerable=False,
                reason="insufficient_query_token_support",
                top_score=coverage,
                threshold=0.35,
            )
        return EvidenceDecision(
            answerable=True,
            reason="sufficient_evidence",
            top_score=top_score,
            threshold=settings.min_rerank_score_to_answer,
        )

    def _salient_query_coverage(self, chunks: list[RetrievedChunk]) -> float:
        question_tokens = getattr(self, "_active_query_tokens", [])
        if not question_tokens:
            return 0.0
        evidence_tokens: set[str] = set()
        for chunk in chunks[:3]:
            evidence_tokens.update(tokenize(chunk.content))
            evidence_tokens.update(tokenize(chunk.title))
        salient_tokens = [
            token
            for token in question_tokens
            if token not in STOPWORDS and (len(token) > 2 or token.isdigit())
        ]
        if not salient_tokens:
            return 1.0
        hits = sum(1 for token in salient_tokens if token in evidence_tokens)
        return hits / len(salient_tokens)

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
                    doc_id=chunk.doc_id,
                    college_name=chunk.college_name,
                    title=chunk.title,
                    url=chunk.url,
                    content=chunk.content,
                    source_kind=chunk.source_kind,
                    lexical_score=round(lexical, 4),
                    vector_score=round(vector_like, 4),
                    combined_score=round(combined, 4),
                    retrieval_stage="lexical",
                    trust_label=SourceTrustLabel.official_verified,
                )
            )

        scored.sort(key=lambda item: item.combined_score, reverse=True)
        for idx, item in enumerate(scored[:limit]):
            item.rank = idx + 1
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
