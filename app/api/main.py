from __future__ import annotations

from fastapi import FastAPI

from app.models import (
    CollegeSignalsRequest,
    OfficialIngestRequest,
    QueryRequest,
    QueryResponse,
)
from app.official.service import OfficialEvidenceService
from app.public_signals.router import detect_college_name, should_use_public_signals
from app.public_signals.service import PublicSignalsService
from app.verification.service import FinalAnswerVerifier


app = FastAPI(title="College Admission Assistant RAG")

official_service = OfficialEvidenceService()
public_signals_service = PublicSignalsService()
verifier = FinalAnswerVerifier()


def _theme_bullets(themes, default: str) -> str:
    if not themes:
        return default
    return "\n".join(
        f"- {theme.topic}: {theme.summary}"
        + (" Recurring across multiple sources." if theme.recurring else "")
        for theme in themes[:5]
    )


def _warning_bullets(warnings, default: str) -> str:
    if not warnings:
        return default
    return "\n".join(f"- {warning.warning}" for warning in warnings)


def compose_final_answer(official_summary: str, official_sources, report_used: bool, report) -> str:
    sections = [
        "Official Recommendation",
        official_summary,
        "",
        "Official Sources",
        "\n".join(
            f"- {source.title}: {source.snippet} ({source.url})"
            for source in official_sources[:4]
        )
        or "Official facts should come from counseling documents, institute websites, and fee or cutoff PDFs.",
    ]

    if report_used and report is not None:
        sections.extend(
            [
                "",
                "Student Signals: Reddit",
                _theme_bullets(report.reddit_themes, default="Reddit data was unavailable or low-signal."),
                "",
                "Student Signals: YouTube",
                _theme_bullets(report.youtube_themes, default="YouTube data was unavailable or low-signal."),
                "",
                "Cautions and Bias Warnings",
                _warning_bullets(report.bias_warnings, default="No promotion warnings were triggered."),
                "",
                "Bottom Line",
                "Public commentary is advisory only. Use it to understand lived experience and recurring concerns, not to replace official admissions facts.",
            ]
        )

    return "\n".join(sections)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/query/college-signals")
async def query_college_signals(request: CollegeSignalsRequest):
    return await public_signals_service.analyze(request.college_name, request.focus)


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
    official_answer = official_service.get_official_answer(
        request.question, college_name, request.official_answer
    )

    use_public_signals = should_use_public_signals(request.question, college_name)
    report = None
    if use_public_signals and college_name:
        report = await public_signals_service.analyze(college_name, request.question)

    answer = compose_final_answer(
        official_answer.summary,
        official_answer.sources,
        use_public_signals and report is not None,
        report,
    )
    verification_report = None
    if request.run_verification:
        evidence_texts = [source.snippet for source in official_answer.sources]
        if report:
            evidence_texts.extend(signal.title + " " + " ".join(signal.concerns + signal.positives) for signal in report.reddit_signals)
            evidence_texts.extend(signal.title + " " + " ".join(signal.concerns + signal.positives) for signal in report.youtube_signals)
        verification_report = verifier.verify(answer, evidence_texts)

    return QueryResponse(
        answer=answer,
        official_answer=official_answer,
        official_sources=official_answer.sources,
        public_signals_used=use_public_signals and report is not None,
        retrieved_chunks=official_answer.retrieved_chunks,
        reddit_signals=report.reddit_signals if report else [],
        youtube_signals=report.youtube_signals if report else [],
        bias_warnings=report.bias_warnings if report else [],
        public_signals_report=report,
        verification_report=verification_report,
    )
