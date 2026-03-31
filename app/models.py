from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum

from pydantic import AliasChoices, BaseModel, Field, HttpUrl


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


class QueryStatus(str, Enum):
    answered = "answered"
    insufficient_evidence = "insufficient_evidence"


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
    chunk_id: str | None = None
    trust_label: SourceTrustLabel = SourceTrustLabel.official_verified


class RetrievedChunk(BaseModel):
    chunk_id: str
    doc_id: str
    college_name: str
    title: str
    url: str
    content: str
    source_kind: str = "official"
    lexical_score: float = 0.0
    vector_score: float = 0.0
    rerank_score: float | None = None
    combined_score: float = 0.0
    retrieval_stage: str = "unknown"
    rank: int | None = None
    trust_label: SourceTrustLabel = SourceTrustLabel.official_verified


class RerankedChunk(BaseModel):
    chunk_id: str
    title: str
    url: str
    rerank_score: float
    rank: int


class AnswerCitation(BaseModel):
    chunk_id: str
    title: str
    url: str
    supporting_text: str


class GenerationTrace(BaseModel):
    provider: str
    model: str
    prompt_name: str
    prompt_version: str
    attempts: int = 1
    fallback_used: bool = False


class RetrievalTrace(BaseModel):
    lexical_candidates: list[RetrievedChunk] = Field(default_factory=list)
    vector_candidates: list[RetrievedChunk] = Field(default_factory=list)
    reranked_candidates: list[RetrievedChunk] = Field(default_factory=list)
    decision: "EvidenceDecision | None" = None
    generation: GenerationTrace | None = None


class EvidenceDecision(BaseModel):
    answerable: bool
    reason: str
    top_score: float = 0.0
    threshold: float = 0.0


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
    include_public_signals: bool = False
    debug: bool = False
    top_k: int | None = None


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


class QueryResponse(BaseModel):
    status: QueryStatus
    answer: str
    citations: list[AnswerCitation] = Field(default_factory=list)
    official_answer: OfficialAnswer
    official_sources: list[OfficialSource] = Field(default_factory=list)
    retrieved_chunks: list[RetrievedChunk] = Field(default_factory=list)
    verification_report: VerificationReport | None = None
    public_signals_used: bool = False
    public_signals_report: PublicSignalsReport | None = None
    reddit_signals: list[RedditSignal] = Field(default_factory=list)
    youtube_signals: list[YouTubeSignal] = Field(default_factory=list)
    bias_warnings: list[BiasWarning] = Field(default_factory=list)
    debug_trace: RetrievalTrace | None = None


class CollegeSourceManifest(BaseModel):
    college_name: str
    allowed_domains: list[str] = Field(default_factory=list)
    seed_urls: list[HttpUrl] = Field(default_factory=list)
    source_kind_defaults: dict[str, str] = Field(default_factory=dict)
    tags: list[str] = Field(default_factory=list)


class GeneratedAnswerPayload(BaseModel):
    status: QueryStatus
    answer: str
    citations: list[str] = Field(default_factory=list)


class GoldenQueryRecord(BaseModel):
    id: str
    college_name: str | None = None
    question: str
    expected_answer_points: list[str] = Field(default_factory=list)
    required_source_urls: list[str] = Field(default_factory=list)
    expected_chunk_ids: list[str] = Field(default_factory=list)
    should_abstain: bool = False
    notes: str = ""


class BranchCutoff(BaseModel):
    branch_name: str
    exam: str
    closing_rank: int
    degree_level: str = "btech"


class CollegeProfile(BaseModel):
    college_id: str
    college_name: str
    institute_type: str
    state: str
    city: str
    zone: str
    location_type: str
    entrance_exams: list[str] = Field(default_factory=list)
    branch_cutoffs: list[BranchCutoff] = Field(default_factory=list)
    annual_tuition_lakh: float
    annual_hostel_lakh: float
    total_annual_cost_lakh: float
    hostel_available: bool = True
    scholarship_notes: str = ""
    official_source_urls: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class RecommendationRequest(BaseModel):
    entrance_exam: str = Field(validation_alias=AliasChoices("entrance_exam", "exam"))
    rank: int = Field(gt=0)
    preferred_branches: list[str] = Field(default_factory=list)
    budget_lakh: float = Field(
        gt=0,
        validation_alias=AliasChoices("budget_lakh", "budget_max_lakh"),
    )
    preferred_states: list[str] = Field(default_factory=list)
    preferred_cities: list[str] = Field(default_factory=list)
    preferred_zones: list[str] = Field(default_factory=list)
    hostel_required: bool = False
    max_results: int = Field(default=5, ge=1, le=15)
    include_rag_summary: bool = True
    include_public_signals: bool = True


class SoftFactors(BaseModel):
    placement_summary: str = ""
    roi_indicator: str = ""
    lab_facilities: str = ""
    faculty_quality: str = ""
    startup_culture: str = ""
    extracurriculars: str = ""
    internship_opportunities: str = ""
    attendance_policy: str = ""


class RecommendationEvidence(BaseModel):
    summary: str
    citations: list[AnswerCitation] = Field(default_factory=list)


class RecommendationItem(BaseModel):
    college_id: str
    college_name: str
    institute_type: str
    state: str
    city: str
    zone: str
    matched_branch: str | None = None
    fit_bucket: str
    score: float
    affordability_score: float
    rank_score: float
    location_score: float
    reasons: list[str] = Field(default_factory=list)
    annual_cost_lakh: float
    hostel_available: bool = True
    official_source_urls: list[str] = Field(default_factory=list)
    rag_evidence: RecommendationEvidence | None = None
    soft_factors: SoftFactors | None = None
    public_signals_disclaimer: str = (
        "The signals below are sourced from Reddit and YouTube — crowdsourced, "
        "unverified, and may include promotional or exaggerated claims. "
        "Treat as directional only. Official institute sources take precedence."
    )
    public_signals_report: PublicSignalsReport | None = None


class RecommendationResponse(BaseModel):
    student_profile: RecommendationRequest
    recommendations: list[RecommendationItem] = Field(default_factory=list)
    filtered_out_count: int = 0
    notes: list[str] = Field(default_factory=list)


class StudentPreferenceField(BaseModel):
    field: str
    description: str
    recommended_values: list[str] = Field(default_factory=list)


class StudentPreferenceGuide(BaseModel):
    title: str
    overview: str
    fields: list[StudentPreferenceField] = Field(default_factory=list)
    tips: list[str] = Field(default_factory=list)
