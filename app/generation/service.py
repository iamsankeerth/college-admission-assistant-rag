from __future__ import annotations

import json
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

    def generate(
        self,
        *,
        question: str,
        college_name: str | None,
        chunks: list[RetrievedChunk],
    ) -> tuple[GeneratedAnswerPayload, GenerationTrace]:
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
        for _ in range(2):
            attempts += 1
            try:
                response = self.client.models.generate_content(
                    model=settings.gemini_model,
                    contents=prompt,
                    config=self.types.GenerateContentConfig(
                        temperature=0.1,
                        response_mime_type="application/json",
                    ),
                )
                payload = GeneratedAnswerPayload.model_validate_json(response.text)
                return payload, GenerationTrace(
                    provider="gemini",
                    model=settings.gemini_model,
                    prompt_name="answer",
                    prompt_version=prompt_version,
                    attempts=attempts,
                )
            except (ValidationError, json.JSONDecodeError, ValueError):
                prompt += (
                    "\n\nThe previous response was invalid. "
                    "Return strict JSON only with status, answer, and citations."
                )

        fallback = GeneratedAnswerPayload(
            status=QueryStatus.insufficient_evidence,
            answer=self.abstain_config.get(
                "fallback_answer",
                "I do not have enough official evidence to answer that reliably.",
            ),
            citations=[],
        )
        return fallback, GenerationTrace(
            provider="gemini",
            model=settings.gemini_model,
            prompt_name="answer",
            prompt_version=prompt_version,
            attempts=attempts,
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
