from __future__ import annotations

import math
from collections import Counter

from app.config import settings
from app.models import EvidenceDecision, RetrievalTrace, RetrievedChunk, SourceTrustLabel
from app.official.corpus import OfficialChunk, OfficialCorpus, tokenize
from app.official.reranker import Reranker, build_reranker
from app.official.vector_store import OfficialVectorStore


STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "at",
    "do",
    "does",
    "exact",
    "for",
    "how",
    "in",
    "is",
    "look",
    "of",
    "official",
    "say",
    "should",
    "sources",
    "the",
    "what",
    "where",
}


class HybridRetriever:
    def __init__(
        self,
        corpus: OfficialCorpus,
        vector_store: OfficialVectorStore,
        reranker: Reranker | None = None,
    ) -> None:
        self.corpus = corpus
        self.vector_store = vector_store
        self.reranker = reranker or build_reranker()
        self._refresh_stats()

    def refresh(self) -> None:
        self.corpus.refresh()
        self._refresh_stats()
        self.vector_store.upsert_chunks(self.corpus.chunks)

    def retrieve(
        self, question: str, college_name: str | None = None, limit: int | None = None
    ) -> tuple[list[RetrievedChunk], RetrievalTrace]:
        final_limit = limit or settings.retrieval_top_k_rerank
        query_tokens = tokenize(question)
        self._active_query_tokens = query_tokens
        lexical_candidates = self._lexical_candidates(
            query_tokens,
            college_name,
            settings.retrieval_top_k_lexical,
        )
        vector_candidates = self.vector_store.query(
            question,
            college_name,
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

        reranked = self.reranker.rerank(question, hybrid_candidates)[:final_limit]
        decision = self.make_decision(reranked)
        trace = RetrievalTrace(
            lexical_candidates=lexical_candidates,
            vector_candidates=vector_candidates,
            reranked_candidates=reranked,
            decision=decision,
        )
        return reranked, trace

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
