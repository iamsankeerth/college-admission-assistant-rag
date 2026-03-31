from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path
from typing import Any

from app.models import (
    BranchCutoff,
    CollegeExploreRequest,
    CollegeExploreResponse,
    CollegeProfile,
    CostAndAdmissions,
    Enrichment3Section,
    EnrichmentStatus,
    FitSnapshot,
    HybridAdjustmentBreakdown,
    OfficialSource,
    OutcomesAndCampus,
    PublicSignalsReport,
    QueryStatus,
    RecommendationItem,
    RecommendationRequest,
    RecommendationResponse,
    ScoreBreakdown,
    StudentPreferenceField,
    StudentPreferenceGuide,
    ThemeSummary,
)
from app.official.service import OfficialEvidenceService
from app.public_signals.service import PublicSignalsService


TOPIC_TO_FIELD: dict[str, str] = {
    "placements": "placement_summary",
    "infrastructure": "lab_facilities",
    "faculty and admin": "faculty_quality",
    "internships and research": "internship_opportunities",
    "peer group and culture": "extracurriculars",
    "academics": "attendance_policy",
}


class CollegeProfileRepository:
    def __init__(self, path: str | Path | None = None) -> None:
        base_dir = Path(__file__).resolve().parents[2] / "data"
        self.path = Path(path) if path else base_dir / "college_profiles.json"
        self.profiles = self._load_profiles()

    def _load_profiles(self) -> list[CollegeProfile]:
        raw = json.loads(self.path.read_text(encoding="utf-8-sig"))
        profiles: list[CollegeProfile] = []
        for item in raw:
            profiles.append(
                CollegeProfile(
                    college_id=re.sub(r"[^a-z0-9]+", "-", item["college_name"].lower()).strip("-"),
                    college_name=item["college_name"],
                    institute_type=item.get("college_type", item.get("category", "College")),
                    state=item.get("state", ""),
                    city=item.get("city", ""),
                    zone=item.get("zone", ""),
                    location_type="metro" if item.get("is_metro") else "non_metro",
                    entrance_exams=item.get("accepted_exams", []),
                    branch_cutoffs=[
                        BranchCutoff(
                            branch_name=branch["name"],
                            exam=branch["exam"],
                            closing_rank=int(branch["value"]),
                        )
                        for branch in item.get("branches", [])
                    ],
                    annual_tuition_lakh=float(item.get("annual_cost_lakh", {}).get("tuition", 0.0)),
                    annual_hostel_lakh=float(item.get("annual_cost_lakh", {}).get("hostel_mess", 0.0)),
                    total_annual_cost_lakh=float(item.get("annual_cost_lakh", {}).get("total", 0.0)),
                    hostel_available=bool(item.get("hostel_available", True)),
                    scholarship_notes=item.get("notes", ""),
                    official_source_urls=[item["official_admissions_url"]] if item.get("official_admissions_url") else [],
                    tags=item.get("strength_tags", []),
                )
            )
        return profiles

    def all(self) -> list[CollegeProfile]:
        return list(self.profiles)


def normalize_branch(branch: str) -> str:
    return branch.strip().lower().replace("&", "and")


class RecommendationService:
    def __init__(
        self,
        repository: CollegeProfileRepository | None = None,
        official_service: OfficialEvidenceService | None = None,
        public_signals_service: PublicSignalsService | None = None,
    ) -> None:
        self.repository = repository or CollegeProfileRepository()
        self.official_service = official_service or OfficialEvidenceService()
        self.public_signals_service = public_signals_service or PublicSignalsService()

    async def recommend(self, request: RecommendationRequest) -> RecommendationResponse:
        base_items = self._recommend_base(request)
        top_items = base_items[: request.max_results]

        if request.include_public_signals:
            await self._enrich_batch(top_items, include_public_signals=True)
        else:
            for item in top_items:
                item.enrichment_status = EnrichmentStatus.HYDRATED

        top_items.sort(key=lambda x: x.final_score, reverse=True)

        return RecommendationResponse(
            student_profile=request,
            recommendations=top_items,
            stage="enriched",
            filtered_out_count=len(base_items) - len(top_items),
            notes=[
                "Recommendations blend structured profile scoring with official-document RAG summaries and student-reported public signals.",
                (
                    "Public signals (Reddit/YouTube) are crowdsourced and unaudited — treat as directional only. "
                    "Official counselling notices and institute pages take precedence."
                ),
            ],
        )

    def _recommend_base(self, request: RecommendationRequest) -> list[RecommendationItem]:
        eligible: list[RecommendationItem] = []
        for profile in self.repository.all():
            item = self._score_profile(profile, request)
            if item is None:
                continue
            eligible.append(item)

        eligible.sort(key=lambda x: x.final_score, reverse=True)
        return eligible

    def _score_profile(self, profile: CollegeProfile, request: RecommendationRequest) -> RecommendationItem | None:
        exam = request.entrance_exam.strip().lower()
        accepted_exams = [e.lower() for e in profile.entrance_exams]
        if exam not in accepted_exams:
            return None
        if request.hostel_required and not profile.hostel_available:
            return None

        preferred_branches = [normalize_branch(b) for b in request.preferred_branches]
        matching = [
            b for b in profile.branch_cutoffs
            if b.exam.lower() == exam
            and (
                not preferred_branches
                or normalize_branch(b.branch_name) in preferred_branches
            )
        ]
        if not matching:
            return None

        best = max(matching, key=lambda b: b.closing_rank)
        closing_rank = best.closing_rank
        fit_bucket = self._rank_bucket(request.rank, closing_rank)
        if fit_bucket == "not_eligible":
            return None

        rank_score = self._rank_score(request.rank, closing_rank, fit_bucket)
        affordability = self._affordability_score(request.budget_lakh, profile.total_annual_cost_lakh)
        if affordability <= 0.0:
            return None

        location_score = self._location_score(profile, request)
        hostel_bonus = 0.05 if request.hostel_required and profile.hostel_available else 0.0

        base_score = round(rank_score * 0.45 + affordability * 0.30 + location_score * 0.20 + hostel_bonus, 4)
        score_breakdown = ScoreBreakdown(
            rank_score=round(rank_score, 4),
            affordability_score=round(affordability, 4),
            location_score=round(location_score, 4),
            hostel_bonus=hostel_bonus,
        )

        reasons = [
            f"{fit_bucket.title()} rank fit for {best.branch_name} under {request.entrance_exam}.",
            f"Estimated annual cost is {profile.total_annual_cost_lakh:.2f} lakh against your budget of {request.budget_lakh:.2f} lakh.",
        ]
        if location_score >= 0.8:
            reasons.append("Strong location match with your preferred geography.")
        elif location_score >= 0.4:
            reasons.append("Partial location match.")
        if profile.hostel_available:
            reasons.append("Hostel facilities are available.")

        return RecommendationItem(
            college_id=profile.college_id,
            college_name=profile.college_name,
            institute_type=profile.institute_type,
            state=profile.state,
            city=profile.city,
            zone=profile.zone,
            matched_branch=best.branch_name,
            fit_bucket=fit_bucket,
            base_score=base_score,
            hybrid_adjustment=0.0,
            final_score=base_score,
            score=base_score,
            score_breakdown=score_breakdown,
            hybrid_adjustment_breakdown=HybridAdjustmentBreakdown(),
            enrichment_status=EnrichmentStatus.PENDING,
            reasons=reasons,
            annual_cost_lakh=profile.total_annual_cost_lakh,
            hostel_available=profile.hostel_available,
            official_source_urls=profile.official_source_urls,
            enrichment=Enrichment3Section(
                fit_snapshot=FitSnapshot(
                    fit_bucket=fit_bucket,
                    matched_branch=best.branch_name,
                    rank_score=round(rank_score, 4),
                    closing_rank=closing_rank,
                    fit_notes=reasons,
                ),
                cost_and_admissions=CostAndAdmissions(
                    annual_cost_lakh=profile.total_annual_cost_lakh,
                    hostel_available=profile.hostel_available,
                    scholarship_notes=profile.scholarship_notes,
                    admission_process="",
                    counselling_body="JoSAA / CSAB",
                    official_source_url=profile.official_source_urls[0] if profile.official_source_urls else None,
                ),
                outcomes_and_campus=OutcomesAndCampus(),
            ),
        )

    async def _enrich_batch(
        self,
        items: list[RecommendationItem],
        include_public_signals: bool,
    ) -> None:
        tasks = [self._enrich_item(item, include_public_signals) for item in items]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        for item, result in zip(items, results):
            if isinstance(result, Exception):
                item.enrichment_status = EnrichmentStatus.FAILED

    async def _enrich_item(
        self,
        item: RecommendationItem,
        include_public_signals: bool,
    ) -> None:
        try:
            evidence, public_report = await self._build_enrichment(
                item.college_name, item.matched_branch
            )
            self._apply_enrichment(item, evidence, public_report, include_public_signals)
            item.enrichment_status = EnrichmentStatus.HYDRATED
        except Exception:
            item.enrichment_status = EnrichmentStatus.FAILED

    async def _build_enrichment(
        self, college_name: str, matched_branch: str | None
    ) -> tuple[dict[str, str], PublicSignalsReport | None]:
        questions = {
            "placement": (
                f"What are the placement statistics for {college_name}? "
                "Include highest package, average salary, top recruiters, placement percentage."
            ),
            "labs": f"What do official sources say about laboratory facilities and infrastructure at {college_name}?",
            "faculty": f"What is the faculty profile at {college_name}? Include qualifications and teaching reputation.",
            "startup": f"What does {college_name} official sources say about startup incubation and entrepreneurship support?",
            "extras": (
                f"What official information exists about student clubs, "
                f"cultural festivals, sports facilities, and extracurricular activities at {college_name}?"
            ),
            "attendance": f"What are the attendance requirements and academic policies at {college_name}?",
            "internship": (
                f"What official information exists about internship opportunities "
                f"and industry collaborations at {college_name}?"
            ),
        }

        rag_tasks = [self._query_official(q) for q in questions.values()]
        public_task = self.public_signals_service.analyze(college_name, focus=None)

        rag_results, public_result = await asyncio.gather(
            asyncio.gather(*rag_tasks, return_exceptions=True),
            public_task,
        )

        answers = {
            key: "" if isinstance(val, Exception) else val
            for key, val in zip(questions.keys(), rag_results)
        }

        public_report = None if isinstance(public_result, Exception) else public_result
        theme_map = self._map_themes(public_report) if public_report else {}

        return {"answers": answers, "themes": theme_map}, public_report

    def _apply_enrichment(
        self,
        item: RecommendationItem,
        evidence: dict[str, Any],
        public_report: PublicSignalsReport | None,
        include_public_signals: bool,
    ) -> None:
        answers = evidence.get("answers", {})
        themes = evidence.get("themes", {})

        placement = _merge(answers.get("placement", ""), themes.get("placement_summary", ""))
        labs = _merge(answers.get("labs", ""), themes.get("lab_facilities", ""))
        faculty = _merge(answers.get("faculty", ""), themes.get("faculty_quality", ""))
        startup = _merge(answers.get("startup", ""), themes.get("startup_culture", ""))
        extras = _merge(answers.get("extras", ""), themes.get("extracurriculars", ""))
        attendance = _merge(answers.get("attendance", ""), themes.get("attendance_policy", ""))

        roi = self._parse_roi(placement)

        official_adj, official_reason = self._compute_official_adjustment(item, answers, themes, roi)
        public_adj, public_reason = self._compute_public_adjustment(
            public_report, include_public_signals
        )
        final_official, final_public, total_adj = self._enforce_adjustment_policy(
            official_adj, public_adj, public_report
        )

        item.hybrid_adjustment = round(total_adj, 4)
        item.final_score = round(max(0.0, min(1.05, item.base_score + total_adj)), 4)
        item.score = item.final_score
        item.hybrid_adjustment_breakdown = HybridAdjustmentBreakdown(
            official_evidence_adjustment=round(final_official, 4),
            public_signals_adjustment=round(final_public, 4),
            reason=f"Official: {official_reason}. Public: {public_reason}",
        )

        item.enrichment = Enrichment3Section(
            fit_snapshot=FitSnapshot(
                fit_bucket=item.fit_bucket,
                matched_branch=item.matched_branch,
                rank_score=item.score_breakdown.rank_score if item.score_breakdown else 0.0,
                closing_rank=(
                    item.enrichment.fit_snapshot.closing_rank
                    if item.enrichment and item.enrichment.fit_snapshot
                    else None
                ),
                fit_notes=item.reasons,
            ),
            cost_and_admissions=CostAndAdmissions(
                annual_cost_lakh=item.annual_cost_lakh,
                hostel_available=item.hostel_available,
                scholarship_notes=(
                    item.enrichment.cost_and_admissions.scholarship_notes
                    if item.enrichment and item.enrichment.cost_and_admissions
                    else ""
                ),
                admission_process="",
                counselling_body="JoSAA / CSAB",
                official_source_url=item.official_source_urls[0] if item.official_source_urls else None,
            ),
            outcomes_and_campus=OutcomesAndCampus(
                placement_summary=placement,
                roi_indicator=roi,
                lab_facilities=labs,
                faculty_quality=faculty,
                startup_culture=startup,
                extracurriculars=extras,
                attendance_policy=attendance,
            ),
        )
        item.public_signals_report = public_report

    def _compute_official_adjustment(
        self,
        item: RecommendationItem,
        answers: dict[str, str],
        themes: dict[str, str],
        roi: str,
    ) -> tuple[float, str]:
        adj = 0.0
        reasons: list[str] = []

        if roi == "excellent":
            adj += 0.02
            reasons.append("ROI excellent")
        elif roi == "good":
            adj += 0.01
            reasons.append("ROI good")
        elif roi == "low":
            adj -= 0.01
            reasons.append("ROI low")

        meaningful_fields = 0
        for key in ("placement", "labs", "faculty", "startup", "extras", "attendance"):
            val = answers.get(key, "")
            if val and "Not available" not in val and "Not available" not in val:
                meaningful_fields += 1

        if meaningful_fields >= 4:
            adj += 0.01
            reasons.append(f"Rich evidence ({meaningful_fields} fields)")
        elif meaningful_fields < 3:
            adj -= 0.01
            reasons.append(f"Thin evidence ({meaningful_fields} fields)")

        placement_empty = not answers.get("placement") or "Not available" in answers.get("placement", "")
        if placement_empty:
            adj -= 0.01
            reasons.append("Placement data missing")

        adj = max(-0.04, min(0.04, adj))
        reason_str = "; ".join(reasons) if reasons else "Neutral official evidence"
        return adj, reason_str

    def _compute_public_adjustment(
        self,
        public_report: PublicSignalsReport | None,
        include_public_signals: bool,
    ) -> tuple[float, str]:
        if not include_public_signals or public_report is None:
            return 0.0, "Public signals disabled"

        adj = 0.0
        reasons: list[str] = []

        bias_warnings = public_report.bias_warnings or []
        has_bias = len(bias_warnings) > 0

        all_themes: list[ThemeSummary] = public_report.reddit_themes + public_report.youtube_themes
        recurring_positive = sum(
            1 for t in all_themes
            if t.recurring and t.sentiment in ("positive", "mixed") and "promotional" not in t.topic
        )
        recurring_concerns = sum(
            1 for t in all_themes
            if t.recurring and t.sentiment in ("negative", "concern")
        )

        if has_bias:
            adj = -0.02
            reasons.append("Promotional/bias warnings detected")
        elif recurring_positive >= 3:
            adj = 0.01
            reasons.append(f"Recurring positive signals ({recurring_positive})")
        elif recurring_positive >= 1:
            adj = 0.005
            reasons.append(f"Mildly positive signals ({recurring_positive})")
        elif recurring_concerns >= 2:
            adj = -0.01
            reasons.append(f"Concerns raised ({recurring_concerns})")

        low_confidence = sum(1 for t in all_themes if t.sentiment == "mixed" and not t.recurring)
        if low_confidence >= 4 and adj >= 0:
            adj = 0.0
            reasons.append("Low confidence signals")

        adj = max(-0.02, min(0.02, adj))
        reason_str = "; ".join(reasons) if reasons else "Neutral public signals"
        return adj, reason_str

    def _enforce_adjustment_policy(
        self,
        official_adj: float,
        public_adj: float,
        public_report: PublicSignalsReport | None,
    ) -> tuple[float, float, float]:
        bias_warnings = public_report.bias_warnings if public_report else []
        has_bias = len(bias_warnings) > 0

        if official_adj < 0:
            if public_adj > 0:
                public_adj = 0.0
            if official_adj + public_adj > 0:
                public_adj = -official_adj
        elif official_adj == 0:
            if has_bias and public_adj > 0:
                public_adj = 0.0
            public_adj = max(-0.01, min(0.01, public_adj))
            if public_adj > 0 and abs(public_adj) > abs(official_adj) * 0.5:
                public_adj = 0.0
        else:
            if has_bias and public_adj > 0:
                public_adj = 0.0
            if public_adj > 0 and abs(public_adj) > abs(official_adj) * 0.5:
                public_adj = abs(official_adj) * 0.5

        total = official_adj + public_adj
        total = max(-0.05, min(0.05, total))

        return official_adj, public_adj, total

    async def _query_official(self, question: str) -> str:
        try:
            status, answer, _, _, _ = self.official_service.answer_question(
                question, college_name=None, top_k=4
            )
            return answer if status == QueryStatus.answered else ""
        except Exception:
            return ""

    def _map_themes(self, report: PublicSignalsReport | None) -> dict[str, str]:
        if not report:
            return {}
        result: dict[str, str] = {}
        for theme in report.reddit_themes + report.youtube_themes:
            field = TOPIC_TO_FIELD.get(theme.topic)
            if field:
                label = (
                    f"[{theme.sentiment.title()}] {theme.summary}"
                    if theme.sentiment != "mixed"
                    else theme.summary
                )
                result[field] = (result.get(field, "") + " | " + label).strip(" |")
        return result

    def _parse_roi(self, placement_text: str) -> str:
        lpa_values = [
            float(m.group(1))
            for m in re.finditer(r"(\d+(?:\.\d+)?)\s*LPA", placement_text, re.IGNORECASE)
        ]
        if not lpa_values:
            return "unknown"
        highest = max(lpa_values)
        if highest > 15:
            return "excellent"
        if highest > 8:
            return "good"
        if highest > 3:
            return "moderate"
        return "low"

    async def explore(self, request: CollegeExploreRequest) -> CollegeExploreResponse:
        college_name = request.college_name
        evidence, public_report = await self._build_enrichment(college_name, request.branch)
        answers = evidence.get("answers", {})
        themes = evidence.get("themes", {})

        placement_q = (
            f"What do official sources say about {college_name} regarding admissions, "
            "fees, placements, campus facilities, and academics?"
        )
        status, summary, citations, official_answer, _ = self.official_service.answer_question(
            placement_q, college_name, top_k=4
        )

        official_sources_list: list[OfficialSource] = [
            OfficialSource(
                title=src.title,
                url=src.url,
                snippet=src.snippet,
                chunk_id=src.chunk_id,
            )
            for src in (official_answer.sources if official_answer else [])
        ]

        outcomes = OutcomesAndCampus(
            placement_summary=_merge(answers.get("placement", ""), themes.get("placement_summary", "")),
            lab_facilities=_merge(answers.get("labs", ""), themes.get("lab_facilities", "")),
            faculty_quality=_merge(answers.get("faculty", ""), themes.get("faculty_quality", "")),
            startup_culture=_merge(answers.get("startup", ""), themes.get("startup_culture", "")),
            extracurriculars=_merge(answers.get("extras", ""), themes.get("extracurriculars", "")),
            attendance_policy=_merge(answers.get("attendance", ""), themes.get("attendance_policy", "")),
        )

        roi = self._parse_roi(answers.get("placement", ""))
        outcomes.roi_indicator = roi

        return CollegeExploreResponse(
            college_name=college_name,
            enrichment_status=EnrichmentStatus.HYDRATED,
            official_summary=summary if status == QueryStatus.answered else "",
            citations=citations,
            official_sources=official_sources_list,
            enrichment=Enrichment3Section(
                fit_snapshot=FitSnapshot(
                    fit_bucket="",
                    matched_branch=request.branch,
                    rank_score=0.0,
                    closing_rank=request.rank,
                    fit_notes=[],
                ),
                cost_and_admissions=CostAndAdmissions(
                    annual_cost_lakh=0.0,
                    hostel_available=True,
                    admission_process="",
                    counselling_body="JoSAA / CSAB",
                ),
                outcomes_and_campus=outcomes,
            ),
            public_signals_report=public_report,
        )

    def _rank_bucket(self, rank: int, cutoff: int) -> str:
        if rank <= cutoff:
            return "safe" if rank <= max(1, int(cutoff * 0.8)) else "target"
        if rank <= int(cutoff * 1.15):
            return "stretch"
        return "not_eligible"

    def _rank_score(self, rank: int, cutoff: int, bucket: str) -> float:
        if bucket == "safe":
            return 1.0
        if bucket == "target":
            return max(0.75, 1.0 - ((rank - cutoff * 0.8) / max(cutoff * 0.2, 1)))
        if bucket == "stretch":
            return max(0.45, 0.7 - (rank - cutoff) / max(cutoff * 0.3, 1))
        return 0.0

    def _affordability_score(self, budget: float, annual_cost: float) -> float:
        if annual_cost > budget * 1.1:
            return 0.0
        if annual_cost <= budget:
            return min(1.0, 0.75 + (budget - annual_cost) / max(budget, 1))
        return max(0.4, 1.0 - ((annual_cost - budget) / max(budget * 0.1, 0.1)))

    def _location_score(self, profile: CollegeProfile, request: RecommendationRequest) -> float:
        score = 0.2
        if request.preferred_cities and profile.city in request.preferred_cities:
            score = max(score, 1.0)
        if request.preferred_states and profile.state in request.preferred_states:
            score = max(score, 0.8)
        if request.preferred_zones and profile.zone in request.preferred_zones:
            score = max(score, 0.6)
        if not request.preferred_cities and not request.preferred_states and not request.preferred_zones:
            score = 0.5
        if profile.location_type == "metro":
            score = min(1.0, score + 0.08)
        return score


def _merge(official: str, student: str) -> str:
    if official and student:
        return f"Official: {official} | Student signals: {student}"
    if official:
        return f"Official: {official} | Student signals: Not reported"
    if student:
        return f"Official: Not available | Student signals: {student}"
    return "Not available"


def build_preference_guide() -> StudentPreferenceGuide:
    return StudentPreferenceGuide(
        title="Student Preference Configuration Guide",
        overview="Use this guide to enter the minimum information needed for reliable college recommendations.",
        fields=[
            StudentPreferenceField(
                field="entrance_exam",
                description="Select the exam that determines your college eligibility.",
                recommended_values=["JEE Advanced", "JEE Main", "BITSAT", "VITEEE", "WBJEE", "TNEA"],
            ),
            StudentPreferenceField(
                field="rank",
                description="Enter your current or expected rank.",
                recommended_values=["actual rank", "best expected rank", "worst expected rank"],
            ),
            StudentPreferenceField(
                field="budget_lakh",
                description="Maximum annual spend including tuition and hostel.",
                recommended_values=["2.5", "4.0", "6.0", "8.0+"],
            ),
            StudentPreferenceField(
                field="preferred_branches",
                description="Pick one or more branches to bias the ranking.",
                recommended_values=["Computer Science", "Electronics", "Mechanical", "Civil"],
            ),
            StudentPreferenceField(
                field="preferred_states/cities/zones",
                description="Use any combination of city, state, or zone filters.",
                recommended_values=["Karnataka", "Delhi", "Hyderabad", "South", "West"],
            ),
            StudentPreferenceField(
                field="hostel_required",
                description="Turn this on if campus accommodation is important.",
                recommended_values=["true", "false"],
            ),
        ],
        tips=[
            "Run the recommender twice with optimistic and conservative ranks to compare risk.",
            "Treat stretch options as aspirational and verify the latest counselling cutoffs.",
            "Use the official evidence summary to double-check fees, hostels, and admissions rules.",
        ],
    )


CollegeRecommendationService = RecommendationService
