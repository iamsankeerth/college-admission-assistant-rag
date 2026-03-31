from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

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
from app.official.corpus_manager import CorpusManager
from app.official.service import OfficialEvidenceService
from app.public_signals.service import PublicSignalsService
from app.recommendation import RecommendationService, build_preference_guide
from app.recommendation.store import CollegeProfileStore
from app.verification.service import FinalAnswerVerifier


official_service = OfficialEvidenceService()
public_signals_service = PublicSignalsService()
verifier = FinalAnswerVerifier()
recommendation_service = RecommendationService(
    official_service=official_service,
    public_signals_service=public_signals_service,
)
profile_store = CollegeProfileStore()
corpus_manager = CorpusManager()

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


class CorpusStatusResponse(BaseModel):
    version: str | None
    schema_version: str
    chunk_count: int
    college_count: int
    document_count: int
    updated_at: str | None
    is_stale: bool


class RefreshResponse(BaseModel):
    status: str
    new_version: str | None
    chunk_count: int


@v1.get("/admin/corpus/status", response_model=CorpusStatusResponse)
async def v1_corpus_status() -> CorpusStatusResponse:
    version_info = corpus_manager.get_version()
    corpus_version = version_info.version if version_info else None
    schema_version = version_info.schema_version if version_info else settings.index_schema_version
    is_stale = version_info.is_stale() if version_info else True
    return CorpusStatusResponse(
        version=corpus_version,
        schema_version=schema_version,
        chunk_count=version_info.chunk_count if version_info else 0,
        college_count=version_info.college_count if version_info else 0,
        document_count=version_info.document_count if version_info else 0,
        updated_at=version_info.updated_at.isoformat() if version_info and version_info.updated_at else None,
        is_stale=is_stale,
    )


@v1.post("/admin/corpus/refresh", response_model=RefreshResponse)
async def v1_corpus_refresh() -> RefreshResponse:
    official_service.retriever.refresh()
    college_names = {chunk.college_name for chunk in official_service.corpus.chunks}
    version = corpus_manager.update_from_corpus(official_service.corpus, len(college_names))
    return RefreshResponse(
        status="ok",
        new_version=version.version,
        chunk_count=len(official_service.corpus.chunks),
    )


class CollegeProfileUpdateRequest(BaseModel):
    college_name: str | None = None
    state: str | None = None
    city: str | None = None
    zone: str | None = None
    annual_tuition_lakh: float | None = None
    annual_hostel_lakh: float | None = None
    hostel_available: bool | None = None


class CollegeProfileResponse(BaseModel):
    college_id: str
    college_name: str
    institute_type: str
    state: str
    city: str
    zone: str


@v1.get("/admin/colleges", response_model=list[CollegeProfileResponse])
async def v1_list_colleges() -> list[CollegeProfileResponse]:
    profiles = profile_store.all()
    return [CollegeProfileResponse.model_validate(p) for p in profiles]


@v1.get("/admin/colleges/{college_id}", response_model=CollegeProfileResponse)
async def v1_get_college(college_id: str) -> CollegeProfileResponse:
    profile = profile_store.get(college_id)
    if profile is None:
        raise HTTPException(status_code=404, detail=f"College profile '{college_id}' not found")
    return CollegeProfileResponse.model_validate(profile)


@v1.put("/admin/colleges/{college_id}")
async def v1_update_college(
    college_id: str, request: CollegeProfileUpdateRequest
) -> CollegeProfileResponse:
    profile = profile_store.get(college_id)
    if profile is None:
        raise HTTPException(status_code=404, detail=f"College profile '{college_id}' not found")

    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(profile, field, value)

    profile_store.upsert(profile)
    return CollegeProfileResponse.model_validate(profile)


@v1.delete("/admin/colleges/{college_id}")
async def v1_delete_college(college_id: str) -> dict:
    deleted = profile_store.delete(college_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"College profile '{college_id}' not found")
    return {"status": "deleted", "college_id": college_id}


class FeedbackRequest(BaseModel):
    query: str
    college_name: str | None = None
    recommended_colleges: list[str] = Field(default_factory=list)
    helpful: bool
    comments: str = ""


class FeedbackResponse(BaseModel):
    status: str
    feedback_id: str
    recorded_at: str


@v1.post("/feedback", response_model=FeedbackResponse)
async def v1_feedback(request: FeedbackRequest) -> FeedbackResponse:
    import uuid
    from pathlib import Path
    import json

    feedback_id = str(uuid.uuid4())
    feedback_entry = {
        "feedback_id": feedback_id,
        "query": request.query,
        "college_name": request.college_name,
        "recommended_colleges": request.recommended_colleges,
        "helpful": request.helpful,
        "comments": request.comments,
        "recorded_at": datetime.now(timezone.utc).isoformat(),
    }

    feedback_dir = Path("data/feedback")
    feedback_dir.mkdir(parents=True, exist_ok=True)
    feedback_file = feedback_dir / "feedback.jsonl"

    with feedback_file.open("a", encoding="utf-8") as f:
        f.write(json.dumps(feedback_entry, ensure_ascii=False) + "\n")

    return FeedbackResponse(
        status="recorded",
        feedback_id=feedback_id,
        recorded_at=feedback_entry["recorded_at"],
    )
