from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.api.middleware import RequestIDMiddleware, StructuredLoggingMiddleware, get_request_id, setup_logging
from app.api.v1 import v1 as v1_router
from app.config import settings
from app.exceptions import AppException
from app.models import (
    CollegeSignalsRequest,
    ErrorDetail,
    ErrorResponse,
    ErrorCode,
    OfficialIngestRequest,
    QueryRequest,
    QueryResponse,
    RecommendationRequest,
    RecommendationResponse,
    StudentPreferenceGuide,
)
from app.official.service import OfficialEvidenceService
from app.official.vector_store import OfficialVectorStore
from app.public_signals.router import detect_college_name
from app.public_signals.service import PublicSignalsService
from app.recommendation import RecommendationService, build_preference_guide
from app.verification.service import FinalAnswerVerifier


setup_logging(level=settings.log_level)
logger = logging.getLogger("app.api")


official_service = OfficialEvidenceService()
public_signals_service = PublicSignalsService()
verifier = FinalAnswerVerifier()
recommendation_service = RecommendationService(
    official_service=official_service,
    public_signals_service=public_signals_service,
)


class SubsystemHealth(BaseModel):
    status: str
    detail: str | None = None


class HealthResponse(BaseModel):
    status: str
    version: str
    subsystems: dict[str, SubsystemHealth]


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("application_startup", extra={"version": settings.app_version})
    yield
    logger.info("application_shutdown")


app = FastAPI(
    title="College Admission Assistant RAG",
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(StructuredLoggingMiddleware)
app.add_middleware(RequestIDMiddleware)
app.include_router(v1_router)


@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    error_response = ErrorResponse(
        error=ErrorDetail(code=exc.code, message=exc.message, details=exc.details),
        request_id=request_id,
    )
    logger.warning(
        "app_exception",
        extra={
            "request_id": request_id,
            "error_code": exc.code.value,
            "error_message": exc.message,
        },
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=error_response.model_dump(mode="json"),
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None)
    logger.error(
        "unhandled_exception",
        extra={"request_id": request_id, "error": str(exc), "type": type(exc).__name__},
    )
    error_response = ErrorResponse(
        error=ErrorDetail(
            code=ErrorCode.INTERNAL_ERROR,
            message="An internal error occurred. Please retry or contact support.",
        ),
        request_id=request_id,
    )
    return JSONResponse(
        status_code=500,
        content=error_response.model_dump(mode="json"),
    )


@app.get("/health", response_model=dict[str, str], tags=["health"])
async def health_liveness() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/health/ready", response_model=HealthResponse, tags=["health"])
async def health_readiness() -> HealthResponse:
    subsystems: dict[str, SubsystemHealth] = {}
    overall_status = "ok"

    try:
        vs = OfficialVectorStore()
        vs.upsert_chunks([])
        subsystems["vector_store"] = SubsystemHealth(status="ok", detail="ChromaDB accessible")
    except Exception as exc:
        subsystems["vector_store"] = SubsystemHealth(status="error", detail=str(exc))
        overall_status = "degraded"

    try:
        from app.generation.service import build_answer_generator
        gen = build_answer_generator()
        subsystems["generator"] = SubsystemHealth(status="ok", detail=f"Provider: {gen.provider}")
    except Exception as exc:
        subsystems["generator"] = SubsystemHealth(status="error", detail=str(exc))
        overall_status = "degraded"

    try:
        reddit_ok = public_signals_service.reddit_fetcher is not None
        yt_ok = public_signals_service.youtube_fetcher is not None
        if reddit_ok and yt_ok:
            subsystems["public_signals"] = SubsystemHealth(status="ok", detail="Reddit and YouTube fetchers initialized")
        else:
            subsystems["public_signals"] = SubsystemHealth(status="degraded", detail="Some fetchers unavailable")
            overall_status = "degraded"
    except Exception as exc:
        subsystems["public_signals"] = SubsystemHealth(status="error", detail=str(exc))
        overall_status = "degraded"

    return HealthResponse(status=overall_status, version=settings.app_version, subsystems=subsystems)


@app.get("/guide/preferences", response_model=StudentPreferenceGuide, tags=["guide"])
async def preference_guide() -> StudentPreferenceGuide:
    return build_preference_guide()


@app.post("/query", response_model=QueryResponse, tags=["query"])
async def query_v0(request: QueryRequest) -> QueryResponse:
    request_id = get_request_id()
    college_name = request.college_name or detect_college_name(request.question)
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


@app.post("/query/college-signals", tags=["public-signals"])
async def query_college_signals(request: CollegeSignalsRequest):
    return await public_signals_service.analyze(request.college_name, request.focus)


@app.post("/recommend", response_model=RecommendationResponse, tags=["recommend"])
async def recommend_v0(request: RecommendationRequest) -> RecommendationResponse:
    return await recommendation_service.recommend(request)


@app.post("/admin/ingest", tags=["admin"])
async def admin_ingest(request: OfficialIngestRequest):
    return await official_service.ingest_sources(
        college_name=request.college_name,
        urls=request.urls,
        file_paths=request.file_paths,
        title=request.title,
        source_kind=request.source_kind,
    )


@app.get("/metrics", tags=["observability"])
async def metrics():
    if not settings.metrics_enabled:
        return {"status": "disabled", "message": "Metrics are disabled. Set METRICS_ENABLED=true to enable."}
    from app.observability import get_metrics
    return get_metrics().get_all()
