from __future__ import annotations

import json
import time
from typing import Protocol

from pydantic import ValidationError

from app.config import settings
from app.models import (
    GeneratedAnswerPayload,
    GenerationTrace,
    QueryStatus,
    RetrievedChunk,
)


def _truncate(text: str, limit: int = 320) -> str:
    return text if len(text) <= limit else text[: limit - 3].rstrip() + "..."


def _build_context_block(chunks: list[RetrievedChunk]) -> str:
    lines = []
    for chunk in chunks:
        lines.append(
            "\n".join(
                [
                    f"Chunk ID: {chunk.chunk_id}",
                    f"Title: {chunk.title}",
                    f"URL: {chunk.url}",
                    f"Excerpt: {_truncate(chunk.content)}",
                ]
            )
        )
    return "\n\n".join(lines)


class AnswerGenerator(Protocol):
    def generate(
        self,
        *,
        question: str,
        college_name: str | None,
        chunks: list[RetrievedChunk],
    ) -> tuple[GeneratedAnswerPayload, GenerationTrace]: ...


class TemplateAnswerGenerator:
    def __init__(self) -> None:
        self.prompt_config = settings.answer_prompt

    def generate(
        self,
        *,
        question: str,
        college_name: str | None,
        chunks: list[RetrievedChunk],
    ) -> tuple[GeneratedAnswerPayload, GenerationTrace]:
        if not chunks:
            return (
                GeneratedAnswerPayload(
                    status=QueryStatus.insufficient_evidence,
                    answer=settings.abstain_prompt.get(
                        "fallback_answer",
                        "I do not have enough official evidence to answer that reliably.",
                    ),
                    citations=[],
                ),
                GenerationTrace(
                    provider="template",
                    model="deterministic-template",
                    prompt_name="abstain",
                    prompt_version=str(settings.abstain_prompt.get("version", "1")),
                    fallback_used=True,
                ),
            )

        header = f"Official findings for {college_name}:" if college_name else "Official findings:"
        bullets = [
            f"- {chunk.title}: {_truncate(chunk.content, limit=220)}"
            for chunk in chunks[: min(3, len(chunks))]
        ]
        answer = "\n".join([header, *bullets])
        payload = GeneratedAnswerPayload(
            status=QueryStatus.answered,
            answer=answer,
            citations=[chunk.chunk_id for chunk in chunks[: min(5, len(chunks))]],
        )
        trace = GenerationTrace(
            provider="template",
            model="deterministic-template",
            prompt_name="answer",
            prompt_version=str(self.prompt_config.get("version", "1")),
            fallback_used=True,
        )
        return payload, trace


class GeminiAnswerGenerator:
    def __init__(self) -> None:
        from google import genai
        from google.genai import types

        self.genai = genai
        self.types = types
        self.client = genai.Client(api_key=settings.gemini_api_key)
        self.prompt_config = settings.answer_prompt
        self.abstain_config = settings.abstain_prompt
        self.max_attempts = 3
        self.base_delay = 1.0
        self.max_delay = 8.0

        from app.generation.circuit_breaker import get_circuit_breaker, CircuitBreakerConfig

        self.circuit_breaker = get_circuit_breaker(
            "gemini-generation",
            CircuitBreakerConfig(
                failure_threshold=5,
                success_threshold=2,
                timeout_seconds=30.0,
            ),
        )

    def generate(
        self,
        *,
        question: str,
        college_name: str | None,
        chunks: list[RetrievedChunk],
    ) -> tuple[GeneratedAnswerPayload, GenerationTrace]:
        if not self.circuit_breaker.is_available:
            return self._degraded_response(
                "circuit_breaker_open",
                "Gemini generation service is temporarily unavailable.",
            )

        prompt_version = str(self.prompt_config.get("version", "1"))
        context_block = _build_context_block(chunks)
        system_prompt = self.prompt_config.get(
            "system",
            "Answer only from the provided chunks and cite chunk IDs.",
        )
        user_prompt_template = self.prompt_config.get(
            "user_template",
            (
                "Question: {question}\n"
                "College: {college_name}\n"
                "Retrieved official evidence:\n{context}\n\n"
                "Return JSON with keys: status, answer, citations."
            ),
        )
        prompt = "\n\n".join(
            [
                system_prompt,
                user_prompt_template.format(
                    question=question,
                    college_name=college_name or "unknown",
                    context=context_block,
                ),
            ]
        )

        attempts = 0
        last_error: Exception | None = None
        for attempt in range(self.max_attempts):
            attempts += 1
            start_time = time.time()
            try:
                response = self.client.models.generate_content(
                    model=settings.gemini_model,
                    contents=prompt,
                    config=self.types.GenerateContentConfig(
                        temperature=0.1,
                        response_mime_type="application/json",
                    ),
                )
                latency_ms = (time.time() - start_time) * 1000
                payload = GeneratedAnswerPayload.model_validate_json(response.text)
                self.circuit_breaker.record_success()
                return payload, GenerationTrace(
                    provider="gemini",
                    model=settings.gemini_model,
                    prompt_name="answer",
                    prompt_version=prompt_version,
                    attempts=attempts,
                    latency_ms=round(latency_ms, 2),
                )
            except ValidationError:
                prompt += (
                    "\n\nThe previous response was invalid. "
                    "Return strict JSON only with status, answer, and citations."
                )
            except (json.JSONDecodeError, ValueError):
                prompt += (
                    "\n\nThe previous response was not valid JSON. "
                    "Return strict JSON only with status, answer, and citations."
                )
            except Exception as exc:
                error_str = str(exc).lower()
                is_rate_limit = (
                    "429" in error_str
                    or "rate limit" in error_str
                    or "quota" in error_str
                    or "RESOURCE_EXHAUSTED" in error_str
                )
                is_timeout = (
                    "timeout" in error_str
                    or "timed out" in error_str
                    or "deadline" in error_str
                )
                is_server_error = (
                    "500" in error_str
                    or "502" in error_str
                    or "503" in error_str
                    or "server error" in error_str
                )
                if is_rate_limit or is_timeout or is_server_error:
                    if attempt < self.max_attempts - 1:
                        delay = min(self.base_delay * (2 ** attempt), self.max_delay)
                        time.sleep(delay)
                        continue
                    if is_rate_limit:
                        self.circuit_breaker.record_failure()
                        return self._degraded_response("rate_limited", "Rate limit exceeded. Please slow down.", retry_after=60)
                    if is_timeout:
                        return self._degraded_response("timeout", "Generation timed out. Please try again.", retry_after=10)
                last_error = exc  # noqa: F841

        self.circuit_breaker.record_failure()
        return self._degraded_response(
            "generation_failed",
            self.abstain_config.get(
                "fallback_answer",
                "I do not have enough official evidence to answer that reliably.",
            ),
        )

    def _degraded_response(
        self,
        reason: str,
        message: str,
        retry_after: int | None = None,
    ) -> tuple[GeneratedAnswerPayload, GenerationTrace]:
        fallback = GeneratedAnswerPayload(
            status=QueryStatus.insufficient_evidence,
            answer=message,
            citations=[],
        )
        return fallback, GenerationTrace(
            provider="gemini",
            model=settings.gemini_model,
            prompt_name="answer",
            prompt_version="1",
            attempts=3,
            fallback_used=True,
        )


def build_answer_generator() -> AnswerGenerator:
    provider = settings.answer_provider.lower()
    if provider == "template":
        return TemplateAnswerGenerator()
    if provider == "gemini" and settings.gemini_api_key:
        try:
            return GeminiAnswerGenerator()
        except Exception:
            return TemplateAnswerGenerator()
    return TemplateAnswerGenerator()
