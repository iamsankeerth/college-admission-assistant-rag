from __future__ import annotations

from app.generation import AnswerGenerator, build_answer_generator
from app.models import (
    AnswerCitation,
    OfficialAnswer,
    OfficialIngestResponse,
    OfficialSource,
    QueryStatus,
    RetrievalTrace,
    RetrievedChunk,
)
from app.official.cache import RetrievalCache
from app.official.corpus import OfficialCorpus
from app.official.corpus_manager import CorpusManager
from app.official.ingestion import OfficialIngestionService
from app.official.retrieval import HybridRetriever
from app.official.vector_store import OfficialVectorStore


class OfficialEvidenceService:
    """Production-shaped RAG service over the seeded official corpus."""

    def __init__(
        self,
        corpus: OfficialCorpus | None = None,
        retriever: HybridRetriever | None = None,
        vector_store: OfficialVectorStore | None = None,
        ingestion_service: OfficialIngestionService | None = None,
        answer_generator: AnswerGenerator | None = None,
        cache: RetrievalCache | None = None,
        corpus_manager: CorpusManager | None = None,
    ) -> None:
        self.corpus = corpus or OfficialCorpus()
        self.vector_store = vector_store or OfficialVectorStore()
        self.vector_store.upsert_chunks(self.corpus.chunks)
        self.cache = cache or RetrievalCache()
        self.corpus_manager = corpus_manager or CorpusManager()
        self.retriever = retriever or HybridRetriever(
            self.corpus,
            self.vector_store,
            cache=self.cache,
        )
        self.ingestion_service = ingestion_service or OfficialIngestionService(
            self.corpus, self.vector_store
        )
        self.answer_generator = answer_generator or build_answer_generator()
        self._init_corpus_version()

    def answer_question(
        self,
        question: str,
        college_name: str | None,
        *,
        provided: OfficialAnswer | None = None,
        top_k: int | None = None,
    ) -> tuple[QueryStatus, str, list[AnswerCitation], OfficialAnswer, RetrievalTrace]:
        if provided is not None:
            citations = [
                AnswerCitation(
                    chunk_id=source.chunk_id or f"provided::{idx}",
                    title=source.title,
                    url=source.url,
                    supporting_text=source.snippet,
                )
                for idx, source in enumerate(provided.sources)
            ]
            trace = RetrievalTrace()
            return QueryStatus.answered, provided.summary, citations, provided, trace

        retrieved, trace = self.retriever.retrieve(question, college_name, limit=top_k)
        trace.decision = self.retriever.make_decision(retrieved)
        if not trace.decision.answerable:
            official_answer = OfficialAnswer(
                summary="I do not have enough official evidence in the current corpus to answer that reliably.",
                note=(
                    "The system abstained because the retrieved official evidence did not clear "
                    "the minimum reranking threshold."
                ),
                retrieved_chunks=retrieved,
            )
            return (
                QueryStatus.insufficient_evidence,
                official_answer.summary,
                [],
                official_answer,
                trace,
            )

        payload, generation_trace = self.answer_generator.generate(
            question=question,
            college_name=college_name,
            chunks=retrieved,
        )
        trace.generation = generation_trace
        citations = self._validate_citations(payload.citations, retrieved)
        if payload.status == QueryStatus.answered and not citations:
            payload = payload.model_copy(
                update={
                    "status": QueryStatus.insufficient_evidence,
                    "answer": "I could not verify chunk-backed citations for a reliable answer.",
                }
            )

        sources = [
            OfficialSource(
                title=chunk.title,
                url=chunk.url,
                snippet=chunk.content,
                chunk_id=chunk.chunk_id,
            )
            for chunk in retrieved[:4]
        ]
        official_answer = OfficialAnswer(
            summary=payload.answer,
            sources=sources,
            note=(
                "Answer generated from official retrieved chunks with hybrid retrieval, reranking, "
                "and citation validation."
            ),
            retrieved_chunks=retrieved,
        )
        return payload.status, payload.answer, citations, official_answer, trace

    def _validate_citations(
        self,
        citation_ids: list[str],
        retrieved: list[RetrievedChunk],
    ) -> list[AnswerCitation]:
        by_id = {chunk.chunk_id: chunk for chunk in retrieved}
        citations: list[AnswerCitation] = []
        for citation_id in citation_ids:
            chunk = by_id.get(citation_id)
            if chunk is None:
                continue
            citations.append(
                AnswerCitation(
                    chunk_id=chunk.chunk_id,
                    title=chunk.title,
                    url=chunk.url,
                    supporting_text=chunk.content,
                )
            )
        return citations

    async def ingest_sources(
        self,
        *,
        college_name: str,
        urls: list[str],
        file_paths: list[str],
        title: str | None = None,
        source_kind: str = "official",
    ) -> OfficialIngestResponse:
        ingested, errors = await self.ingestion_service.ingest(
            college_name=college_name,
            urls=urls,
            file_paths=file_paths,
            title=title,
            source_kind=source_kind,
        )
        self.retriever.refresh()
        self._update_corpus_version()
        return OfficialIngestResponse(ingested=ingested, errors=errors)

    def _init_corpus_version(self) -> None:
        existing = self.corpus_manager.get_version()
        if existing is None:
            college_names = {chunk.college_name for chunk in self.corpus.chunks}
            self.corpus_manager.update_from_corpus(self.corpus, len(college_names))

    def _update_corpus_version(self) -> None:
        college_names = {chunk.college_name for chunk in self.corpus.chunks}
        self.corpus_manager.update_from_corpus(self.corpus, len(college_names))
