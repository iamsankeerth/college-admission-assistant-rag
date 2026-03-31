from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel

from app.api.middleware import get_request_id
from app.config import settings
from app.models import (
    CollegeExploreRequest,
    CollegeExploreResponse,
    CollegeSignalsRequest,
    OfficialIngestRequest,
    QueryRequest,
    QueryResponse,
    RecommendationRequest,
    RecommendationResponse,
    StudentPreferenceGuide,
)
from app.official.service import OfficialEvidenceService
from app.public_signals.service import PublicSignalsService
from app.recommendation import RecommendationService, build_preference_guide
from app.verification.service import FinalAnswerVerifier


official_service = OfficialEvidenceService()
public_signals_service = PublicSignalsService()
verifier = FinalAnswerVerifier()
recommendation_service = RecommendationService(
    official_service=official_service,
    public_signals_service=public_signals_service,
)

v1 = APIRouter(prefix="/v1", tags=["v1"])


class HealthResponse(BaseModel):
    status: str
    version: str
    index_schema_version: str


@v1.get("/health", response_model=HealthResponse)
async def v1_health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        version=settings.app_version,
        index_schema_version=settings.index_schema_version,
    )


@v1.get("/guide/preferences", response_model=StudentPreferenceGuide)
async def v1_preference_guide() -> StudentPreferenceGuide:
    return build_preference_guide()


@v1.post("/query", response_model=QueryResponse)
async def v1_query(request: QueryRequest) -> QueryResponse:
    request_id = get_request_id()
    college_name = request.college_name
    status, answer, citations, official_answer, trace = official_service.answer_question(
        request.question,
        college_name,
        provided=request.official_answer,
        top_k=request.top_k,
    )

    report = None
    warnings: list[str] = []
    if request.include_public_signals and settings.public_signals_enabled and college_name:
        try:
            report = await public_signals_service.analyze(college_name, request.question)
        except Exception as exc:
            warnings.append(f"Public signals unavailable: {exc}")
            report = None

    verification_report = None
    if request.run_verification:
        evidence_texts = [citation.supporting_text for citation in citations]
        verification_report = verifier.verify(answer, evidence_texts)

    return QueryResponse(
        request_id=request_id,
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
        warnings=warnings,
    )


@v1.post("/query/college-signals")
async def v1_query_college_signals(request: CollegeSignalsRequest):
    return await public_signals_service.analyze(request.college_name, request.focus)


@v1.post("/recommend", response_model=RecommendationResponse)
async def v1_recommend(request: RecommendationRequest) -> RecommendationResponse:
    return await recommendation_service.recommend(request)


@v1.post("/college/explore", response_model=CollegeExploreResponse)
async def v1_explore_college(request: CollegeExploreRequest) -> CollegeExploreResponse:
    return await recommendation_service.explore(request)


@v1.post("/admin/ingest")
async def v1_admin_ingest(request: OfficialIngestRequest):
    return await official_service.ingest_sources(
        college_name=request.college_name,
        urls=request.urls,
        file_paths=request.file_paths,
        title=request.title,
        source_kind=request.source_kind,
    )
