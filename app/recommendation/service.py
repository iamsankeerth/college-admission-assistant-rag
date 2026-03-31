from __future__ import annotations

import asyncio
import json
import re
from pathlib import Path

from app.models import (
    BranchCutoff,
    CollegeProfile,
    PublicSignalsReport,
    QueryStatus,
    RecommendationItem,
    RecommendationRequest,
    RecommendationResponse,
    SoftFactors,
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
    "common positives": "startup_culture",
    "common complaints": "attendance_policy",
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
                    college_id=self._slug(item["college_name"]),
                    college_name=item["college_name"],
                    institute_type=item.get("college_type", item.get("category", "College")),
                    state=item["state"],
                    city=item["city"],
                    zone=item["zone"],
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
                    official_source_urls=[item["official_admissions_url"]]
                    if item.get("official_admissions_url")
                    else [],
                    tags=item.get("strength_tags", []),
                )
            )
        return profiles

    def _slug(self, value: str) -> str:
        return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")

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
        eligible: list[RecommendationItem] = []
        filtered_out = 0
        for profile in self.repository.all():
            item = self._score_profile(profile, request)
            if item is None:
                filtered_out += 1
                continue
            eligible.append(item)

        eligible.sort(key=lambda item: item.score, reverse=True)
        top_items = eligible[: request.max_results]

        coroutines = [
            self._build_soft_factors(item.college_name, item.matched_branch)
            for item in top_items
        ]
        soft_factors_results = await asyncio.gather(*coroutines, return_exceptions=True)

        for item, result in zip(top_items, soft_factors_results):
            if isinstance(result, Exception):
                item.soft_factors = SoftFactors()
                item.public_signals_report = None
            else:
                item.soft_factors, item.public_signals_report = result

        notes = [
            "Recommendations blend structured profile scoring with official-document RAG summaries and student-reported public signals.",
            (
                "Public signals (Reddit/YouTube) are crowdsourced and unaudited — treat as directional only. "
                "Official counselling notices and institute pages take precedence for admissions, fees, and deadlines."
            ),
            "Run the recommender twice with optimistic and conservative ranks to compare risk levels.",
        ]
        return RecommendationResponse(
            student_profile=request,
            recommendations=top_items,
            filtered_out_count=filtered_out,
            notes=notes,
        )

    async def _build_soft_factors(
        self,
        college_name: str,
        matched_branch: str | None,
    ) -> tuple[SoftFactors, PublicSignalsReport | None]:
        official_answers: dict[str, str] = {}
        topics = [
            ("placement_summary", self._placement_question(college_name, matched_branch)),
            ("lab_facilities", "What do official sources say about laboratory facilities and infrastructure at {college}?"),
            ("faculty_quality", "What is the faculty profile at {college}? Include qualifications, PhD percentage, and teaching reputation."),
            ("startup_culture", "What does {college} official sources say about startup incubation, innovation ecosystem, and entrepreneurship support?"),
            ("extracurriculars", "What official information exists about student clubs, cultural festivals, sports facilities, and extracurricular activities at {college}?"),
            ("attendance_policy", "What are the attendance requirements and academic policies at {college}?"),
            ("internship_opportunities", "What official information exists about internship opportunities, industry collaborations, and career services at {college}?"),
        ]

        rag_tasks = [
            self._query_official(question.format(college=college_name))
            for _, question in topics
        ]
        public_task = self.public_signals_service.analyze(college_name, focus=None)

        all_tasks = rag_tasks + [public_task]
        results = await asyncio.gather(*all_tasks, return_exceptions=True)

        rag_results = results[: len(rag_tasks)]
        public_result = results[len(rag_tasks)]

        for i, (field_name, _) in enumerate(topics):
            if isinstance(rag_results[i], Exception):
                official_answers[field_name] = "Not available in current official corpus."
            else:
                official_answers[field_name] = rag_results[i]

        theme_map: dict[str, str] = {}
        if not isinstance(public_result, Exception) and public_result is not None:
            theme_map = self._map_themes_to_fields(public_result)

        soft_factors = SoftFactors(
            placement_summary=_merge_field(
                official_answers.get("placement_summary", ""),
                theme_map.get("placement_summary", ""),
            ),
            lab_facilities=_merge_field(
                official_answers.get("lab_facilities", ""),
                theme_map.get("lab_facilities", ""),
            ),
            faculty_quality=_merge_field(
                official_answers.get("faculty_quality", ""),
                theme_map.get("faculty_quality", ""),
            ),
            startup_culture=_merge_field(
                official_answers.get("startup_culture", ""),
                theme_map.get("startup_culture", ""),
            ),
            extracurriculars=_merge_field(
                official_answers.get("extracurriculars", ""),
                theme_map.get("extracurriculars", ""),
            ),
            attendance_policy=_merge_field(
                official_answers.get("attendance_policy", ""),
                theme_map.get("attendance_policy", ""),
            ),
            internship_opportunities=_merge_field(
                official_answers.get("internship_opportunities", ""),
                theme_map.get("internship_opportunities", ""),
            ),
        )

        public_report: PublicSignalsReport | None = (
            public_result if not isinstance(public_result, Exception) else None
        )
        return soft_factors, public_report

    def _placement_question(self, college_name: str, matched_branch: str | None) -> str:
        q = (
            f"What are the placement statistics for {college_name}? "
            "Include highest package, average salary, top recruiters, placement percentage, "
            "and internship/return offer rates."
        )
        if matched_branch:
            q += f" Focus on {matched_branch} placements where available."
        return q

    async def _query_official(self, question: str) -> str:
        try:
            status, answer, _, _, _ = self.official_service.answer_question(
                question,
                college_name=None,
                top_k=4,
            )
            if status != QueryStatus.answered:
                return "Not available in current official corpus."
            return answer
        except Exception:
            return "Not available in current official corpus."

    def _map_themes_to_fields(self, report: PublicSignalsReport) -> dict[str, str]:
        result: dict[str, str] = {}
        all_themes: list[ThemeSummary] = report.reddit_themes + report.youtube_themes
        for theme in all_themes:
            field = TOPIC_TO_FIELD.get(theme.topic)
            if field:
                summary = theme.summary
                if theme.sentiment and theme.sentiment != "mixed":
                    summary = f"[{theme.sentiment.title()}] {summary}"
                if result.get(field):
                    result[field] += f" | {summary}"
                else:
                    result[field] = summary
        return result

    def _score_profile(
        self,
        profile: CollegeProfile,
        request: RecommendationRequest,
    ) -> RecommendationItem | None:
        exam = request.entrance_exam.strip().lower()
        if exam not in [value.lower() for value in profile.entrance_exams]:
            return None
        if request.hostel_required and not profile.hostel_available:
            return None

        preferred_branches = [normalize_branch(branch) for branch in request.preferred_branches]
        matching_cutoffs = [
            cutoff
            for cutoff in profile.branch_cutoffs
            if cutoff.exam.lower() == exam
            and (
                not preferred_branches
                or normalize_branch(cutoff.branch_name) in preferred_branches
            )
        ]
        if not matching_cutoffs:
            return None

        best_cutoff = max(matching_cutoffs, key=lambda cutoff: cutoff.closing_rank)
        fit_bucket = self._rank_bucket(request.rank, best_cutoff.closing_rank)
        if fit_bucket == "not_eligible":
            return None

        rank_score = self._rank_score(request.rank, best_cutoff.closing_rank, fit_bucket)
        affordability_score = self._affordability_score(request.budget_lakh, profile.total_annual_cost_lakh)
        if affordability_score <= 0.0:
            return None

        location_score = self._location_score(profile, request)
        hostel_bonus = 0.05 if request.hostel_required and profile.hostel_available else 0.0

        score = round(rank_score * 0.45 + affordability_score * 0.30 + location_score * 0.20 + hostel_bonus, 4)
        reasons = [
            f"{fit_bucket.title()} rank fit for {best_cutoff.branch_name} under {request.entrance_exam}.",
            f"Estimated annual cost is {profile.total_annual_cost_lakh:.2f} lakh against your budget of {request.budget_lakh:.2f} lakh.",
        ]
        if location_score >= 0.8:
            reasons.append("Strong location match with your preferred city/state/zone filters.")
        elif location_score >= 0.4:
            reasons.append("Partial location match with your preferred geography.")
        if profile.hostel_available:
            reasons.append("Hostel facilities are available according to the seeded college profile.")

        return RecommendationItem(
            college_id=profile.college_id,
            college_name=profile.college_name,
            institute_type=profile.institute_type,
            state=profile.state,
            city=profile.city,
            zone=profile.zone,
            matched_branch=best_cutoff.branch_name,
            fit_bucket=fit_bucket,
            score=score,
            affordability_score=round(affordability_score, 4),
            rank_score=round(rank_score, 4),
            location_score=round(location_score, 4),
            reasons=reasons,
            annual_cost_lakh=profile.total_annual_cost_lakh,
            hostel_available=profile.hostel_available,
            official_source_urls=profile.official_source_urls,
        )

    def _rank_bucket(self, rank: int, cutoff: int) -> str:
        if rank <= cutoff:
            if rank <= max(1, int(cutoff * 0.8)):
                return "safe"
            return "target"
        if rank <= int(cutoff * 1.15):
            return "stretch"
        return "not_eligible"

    def _rank_score(self, rank: int, cutoff: int, bucket: str) -> float:
        if bucket == "safe":
            return 1.0
        if bucket == "target":
            return max(0.75, 1.0 - ((rank - cutoff * 0.8) / max(cutoff * 0.2, 1)))
        if bucket == "stretch":
            overrun = rank - cutoff
            return max(0.45, 0.7 - overrun / max(cutoff * 0.3, 1))
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


def _merge_field(official: str, student: str) -> str:
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
        overview=(
            "Use this guide to enter the minimum information needed for reliable college recommendations. "
            "The recommender blends your exam profile, rank, budget, and geography preferences."
        ),
        fields=[
            StudentPreferenceField(
                field="entrance_exam",
                description="Select the exam that determines your college eligibility for this search.",
                recommended_values=["JEE Advanced", "JEE Main", "BITSAT", "VITEEE", "WBJEE", "TNEA"],
            ),
            StudentPreferenceField(
                field="rank",
                description="Enter your current or expected rank. The recommender uses it to bucket colleges into safe, target, and stretch fits.",
                recommended_values=["actual rank", "best expected rank", "worst expected rank"],
            ),
            StudentPreferenceField(
                field="budget_lakh",
                description="Use the maximum annual spend you can support, including tuition and hostel when relevant.",
                recommended_values=["2.5", "4.0", "6.0", "8.0+"],
            ),
            StudentPreferenceField(
                field="preferred_branches",
                description="Pick one or more branches to bias the ranking toward your academic interests.",
                recommended_values=["Computer Science", "Electronics", "Mechanical", "Civil"],
            ),
            StudentPreferenceField(
                field="preferred_states/cities/zones",
                description="Use any combination of city, state, or zone filters to reflect location preference.",
                recommended_values=["Karnataka", "Delhi", "Hyderabad", "South", "West"],
            ),
            StudentPreferenceField(
                field="hostel_required",
                description="Turn this on if campus accommodation is important to your decision.",
                recommended_values=["true", "false"],
            ),
        ],
        tips=[
            "Run the recommender twice with an optimistic and a conservative rank to compare risk.",
            "Treat stretch options as aspirational and verify the latest counselling cutoffs separately.",
            "Use the official evidence summary to double-check fees, hostels, and admissions rules before final decisions.",
        ],
    )


CollegeRecommendationService = RecommendationService
