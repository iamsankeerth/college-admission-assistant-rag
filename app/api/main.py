from __future__ import annotations

from fastapi import FastAPI

from app.config import settings
from app.models import (
    CollegeSignalsRequest,
    OfficialIngestRequest,
    QueryRequest,
    QueryResponse,
    RecommendationRequest,
    RecommendationResponse,
    StudentPreferenceGuide,
)
from app.official.service import OfficialEvidenceService
from app.public_signals.router import detect_college_name
from app.public_signals.service import PublicSignalsService
from app.recommendation import RecommendationService, build_preference_guide
from app.verification.service import FinalAnswerVerifier


app = FastAPI(title="College Admission Assistant RAG")

official_service = OfficialEvidenceService()
public_signals_service = PublicSignalsService()
verifier = FinalAnswerVerifier()
recommendation_service = RecommendationService(
    official_service=official_service,
    public_signals_service=public_signals_service,
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/query/college-signals")
async def query_college_signals(request: CollegeSignalsRequest):
    return await public_signals_service.analyze(request.college_name, request.focus)


@app.get("/guide/preferences", response_model=StudentPreferenceGuide)
async def preference_guide() -> StudentPreferenceGuide:
    return build_preference_guide()


@app.post("/recommend", response_model=RecommendationResponse)
async def recommend(request: RecommendationRequest) -> RecommendationResponse:
    return await recommendation_service.recommend(request)


@app.post("/admin/ingest")
async def admin_ingest(request: OfficialIngestRequest):
    return await official_service.ingest_sources(
        college_name=request.college_name,
        urls=request.urls,
        file_paths=request.file_paths,
        title=request.title,
        source_kind=request.source_kind,
    )


@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest) -> QueryResponse:
    college_name = request.college_name or detect_college_name(request.question)
    status, answer, citations, official_answer, trace = official_service.answer_question(
        request.question,
        college_name,
        provided=request.official_answer,
        top_k=request.top_k,
    )

    report = None
    if request.include_public_signals and settings.public_signals_enabled and college_name:
        report = await public_signals_service.analyze(college_name, request.question)

    verification_report = None
    if request.run_verification:
        evidence_texts = [citation.supporting_text for citation in citations]
        verification_report = verifier.verify(answer, evidence_texts)

    return QueryResponse(
        status=status,
        answer=answer,
        citations=citations,
        official_answer=official_answer,
        official_sources=official_answer.sources,
        retrieved_chunks=official_answer.retrieved_chunks,
        verification_report=verification_report,
        public_signals_used=report is not None,
        public_signals_report=report,
        reddit_signals=report.reddit_signals if report else [],
        youtube_signals=report.youtube_signals if report else [],
        bias_warnings=report.bias_warnings if report else [],
        debug_trace=trace if request.debug else None,
    )
