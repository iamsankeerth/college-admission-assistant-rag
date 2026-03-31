from __future__ import annotations

from app.models import ErrorCode


class AppException(Exception):
    def __init__(
        self,
        code: ErrorCode,
        message: str,
        details: dict | None = None,
        status_code: int = 500,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}
        self.status_code = status_code


class ValidationError(AppException):
    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(
            code=ErrorCode.VALIDATION_ERROR,
            message=message,
            details=details,
            status_code=422,
        )


class NotFoundError(AppException):
    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(
            code=ErrorCode.NOT_FOUND,
            message=message,
            details=details,
            status_code=404,
        )


class RetrievalError(AppException):
    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(
            code=ErrorCode.RETRIEVAL_ERROR,
            message=message,
            details=details,
            status_code=500,
        )


class GenerationError(AppException):
    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(
            code=ErrorCode.GENERATION_ERROR,
            message=message,
            details=details,
            status_code=500,
        )


class CircuitBreakerOpenError(AppException):
    def __init__(self, message: str = "Service temporarily unavailable. Please retry later.", details: dict | None = None) -> None:
        super().__init__(
            code=ErrorCode.CIRCUIT_BREAKER_OPEN,
            message=message,
            details=details,
            status_code=503,
        )


class InsufficientEvidenceError(AppException):
    def __init__(self, message: str = "Not enough evidence to answer reliably.", details: dict | None = None) -> None:
        super().__init__(
            code=ErrorCode.INSUFFICIENT_EVIDENCE,
            message=message,
            details=details,
            status_code=200,
        )


class ServiceUnavailableError(AppException):
    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(
            code=ErrorCode.SERVICE_UNAVAILABLE,
            message=message,
            details=details,
            status_code=503,
        )


class CorpusError(AppException):
    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(
            code=ErrorCode.CORPUS_ERROR,
            message=message,
            details=details,
            status_code=500,
        )


class RateLimitedError(AppException):
    def __init__(self, message: str = "Rate limit exceeded. Please slow down.", details: dict | None = None) -> None:
        super().__init__(
            code=ErrorCode.RATE_LIMITED,
            message=message,
            details=details,
            status_code=429,
        )


class PublicSignalsError(AppException):
    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(
            code=ErrorCode.PUBLIC_SIGNALS_ERROR,
            message=message,
            details=details,
            status_code=500,
        )
