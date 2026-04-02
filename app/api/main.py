from __future__ import annotations

import logging
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.api.middleware import RequestIDMiddleware, StructuredLoggingMiddleware, setup_logging
from app.api.v1 import v1 as v1_router
from app.config import settings
from app.exceptions import AppException
from app.models import (
    ErrorDetail,
    ErrorResponse,
    ErrorCode,
)
from app.dependencies import public_signals_service
from app.verification.service import FinalAnswerVerifier


setup_logging(level=settings.log_level)
logger = logging.getLogger("app.api")

verifier = FinalAnswerVerifier()


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

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

    persist_path = Path(settings.chroma_persist_dir)
    if persist_path.exists():
        subsystems["vector_store"] = SubsystemHealth(status="ok", detail="Vector store path accessible")
    else:
        subsystems["vector_store"] = SubsystemHealth(status="degraded", detail="Vector store path not found")
        overall_status = "degraded"

    provider = getattr(settings, "answer_provider", "not_configured")
    subsystems["generator"] = SubsystemHealth(status="ok", detail=f"Provider: {provider}")

    try:
        reddit_ok = getattr(public_signals_service, "reddit_fetcher", None) is not None
        yt_ok = getattr(public_signals_service, "youtube_fetcher", None) is not None
        if reddit_ok and yt_ok:
            subsystems["public_signals"] = SubsystemHealth(status="ok", detail="Reddit and YouTube fetchers available")
        else:
            subsystems["public_signals"] = SubsystemHealth(status="degraded", detail="Some fetchers unavailable")
            overall_status = "degraded"
    except Exception as exc:
        subsystems["public_signals"] = SubsystemHealth(status="error", detail=str(exc))
        overall_status = "degraded"

    return HealthResponse(status=overall_status, version=settings.app_version, subsystems=subsystems)
