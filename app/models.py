from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import BaseModel, Field


class SourceTrustLabel(str, Enum):
    official_verified = "official_verified"
    student_reported = "student_reported"
    public_commentary = "public_commentary"
    promotional = "promotional"
    possibly_promotional = "possibly_promotional"
    low_confidence = "low_confidence"


class PromotionFlag(str, Enum):
    promotional = "promotional"
    possibly_promotional = "possibly_promotional"
    not_flagged = "not_flagged"


class ThemeSummary(BaseModel):
    topic: str
    summary: str
    sentiment: str = "mixed"
    recurring: bool = False
    source_count: int = 0
    examples: list[str] = Field(default_factory=list)


class BiasWarning(BaseModel):
    source_type: str
    source_id: str
    label: SourceTrustLabel
    warning: str


class PromotionAssessment(BaseModel):
    status: PromotionFlag
    trust_label: SourceTrustLabel
    reasons: list[str] = Field(default_factory=list)


class OfficialSource(BaseModel):
    title: str
    url: str
    snippet: str
    trust_label: SourceTrustLabel = SourceTrustLabel.official_verified


class RetrievedChunk(BaseModel):
    chunk_id: str
    title: str
    url: str
    content: str
    lexical_score: float = 0.0
    vector_score: float = 0.0
    combined_score: float = 0.0
    trust_label: SourceTrustLabel = SourceTrustLabel.official_verified


class OfficialAnswer(BaseModel):
    summary: str
    sources: list[OfficialSource] = Field(default_factory=list)
    note: str | None = None
    retrieved_chunks: list[RetrievedChunk] = Field(default_factory=list)


class RedditSignal(BaseModel):
    source_id: str
    title: str
    subreddit: str
    url: str
    post_date: datetime | None = None
    themes: list[str] = Field(default_factory=list)
    positives: list[str] = Field(default_factory=list)
    concerns: list[str] = Field(default_factory=list)
    top_comments: list[str] = Field(default_factory=list)
    sentiment: str = "mixed"
    role_clues: list[str] = Field(default_factory=list)
    confidence_score: float = 0.0
    trust_label: SourceTrustLabel = SourceTrustLabel.student_reported


class YouTubeSignal(BaseModel):
    source_id: str
    title: str
    url: str
    channel_name: str
    publish_date: datetime | None = None
    description: str = ""
    transcript: str = ""
    duration_seconds: int | None = None
    view_count: int | None = None
    themes: list[str] = Field(default_factory=list)
    positives: list[str] = Field(default_factory=list)
    concerns: list[str] = Field(default_factory=list)
    role_clues: list[str] = Field(default_factory=list)
    transcript_available: bool = True
    confidence_score: float = 0.0
    promotion: PromotionAssessment


class PublicSignalsReport(BaseModel):
    college_name: str
    requested_focus: str | None = None
    reddit_signals: list[RedditSignal] = Field(default_factory=list)
    youtube_signals: list[YouTubeSignal] = Field(default_factory=list)
    reddit_themes: list[ThemeSummary] = Field(default_factory=list)
    youtube_themes: list[ThemeSummary] = Field(default_factory=list)
    bias_warnings: list[BiasWarning] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    generated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class QueryRequest(BaseModel):
    question: str
    college_name: str | None = None
    official_answer: OfficialAnswer | None = None
    run_verification: bool = True


class CollegeSignalsRequest(BaseModel):
    college_name: str
    focus: str | None = None


class OfficialIngestRequest(BaseModel):
    college_name: str
    urls: list[str] = Field(default_factory=list)
    file_paths: list[str] = Field(default_factory=list)
    title: str | None = None
    source_kind: str = "official"


class IngestResult(BaseModel):
    document_id: str
    title: str
    source: str
    chunk_count: int


class OfficialIngestResponse(BaseModel):
    ingested: list[IngestResult] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)


class QueryResponse(BaseModel):
    answer: str
    official_answer: OfficialAnswer
    official_sources: list[OfficialSource] = Field(default_factory=list)
    public_signals_used: bool = False
    retrieved_chunks: list[RetrievedChunk] = Field(default_factory=list)
    reddit_signals: list[RedditSignal] = Field(default_factory=list)
    youtube_signals: list[YouTubeSignal] = Field(default_factory=list)
    bias_warnings: list[BiasWarning] = Field(default_factory=list)
    public_signals_report: PublicSignalsReport | None = None
    verification_report: "VerificationReport | None" = None


class ClaimCheck(BaseModel):
    claim: str
    supported: bool
    confidence_score: float
    evidence: list[str] = Field(default_factory=list)


class VerificationReport(BaseModel):
    checks: list[ClaimCheck] = Field(default_factory=list)
    supported_count: int = 0
    unsupported_count: int = 0
    verification_note: str = ""
