from __future__ import annotations

import json
import logging
import sys
import time
import uuid
from contextvars import ContextVar
from typing import Any, Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

request_id_var: ContextVar[str | None] = ContextVar("request_id", default=None)


def get_request_id() -> str | None:
    return request_id_var.get()


class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        request_id = get_request_id()
        log_obj: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id,
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "extra"):
            log_obj.update(record.extra)
        return json.dumps(log_obj, default=str)


def setup_logging(level: str = "INFO") -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter("%(timestamp)s %(level)s %(name)s %(message)s"))
    root_logger = logging.getLogger()
    root_logger.handlers = []
    root_logger.addHandler(handler)
    root_logger.setLevel(getattr(logging, level.upper(), logging.INFO))


class RequestIDMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp, *, header_name: str = "X-Request-ID") -> None:
        super().__init__(app)
        self.header_name = header_name

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        request_id = request.headers.get(self.header_name) or str(uuid.uuid4())
        request_id_var.set(request_id)
        request.state.request_id = request_id
        response = await call_next(request)
        response.headers[self.header_name] = request_id
        return response


class StructuredLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: ASGIApp) -> None:
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        start_time = time.perf_counter()
        request_id = getattr(request.state, "request_id", None)
        logger = logging.getLogger("app.api")

        logger.info(
            "request_started",
            extra={
                "method": request.method,
                "path": request.url.path,
                "query": str(request.query_params),
                "request_id": request_id,
            },
        )

        try:
            response = await call_next(request)
        except Exception as exc:
            duration = time.perf_counter() - start_time
            logger.error(
                "request_failed",
                extra={
                    "method": request.method,
                    "path": request.url.path,
                    "request_id": request_id,
                    "duration_ms": round(duration * 1000, 2),
                    "error": str(exc),
                },
            )
            raise

        duration = time.perf_counter() - start_time
        logger.info(
            "request_completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": round(duration * 1000, 2),
                "request_id": request_id,
            },
        )
        return response


def log_extra(request_id: str | None = None, **kwargs: Any) -> dict[str, Any]:
    extra: dict[str, Any] = {}
    if request_id:
        extra["request_id"] = request_id
    extra.update(kwargs)
    return extra
