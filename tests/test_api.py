from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.api.main import app
from app.models import (
    BiasWarning,
    PublicSignalsReport,
    RedditSignal,
    SourceTrustLabel,
    ThemeSummary,
)


client = TestClient(app)


def test_query_returns_structured_answer():
    response = client.post(
        "/query",
        json={
            "question": "How are admissions handled at IIT Hyderabad?",
            "college_name": "IIT Hyderabad",
            "run_verification": True,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "answered"
    assert body["citations"]
    assert body["official_answer"]["sources"]
    assert body["verification_report"] is not None


def test_recommend_endpoint_returns_personalized_results():
    response = client.post(
        "/recommend",
        json={
            "entrance_exam": "JEE Main",
            "rank": 12000,
            "preferred_branches": ["Computer Science and Engineering"],
            "budget_lakh": 4.5,
            "preferred_states": ["Karnataka", "Tamil Nadu"],
            "preferred_zones": ["South"],
            "hostel_required": True,
            "max_results": 4,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["recommendations"]
    assert body["student_profile"]["entrance_exam"] == "JEE Main"
    assert body["recommendations"][0]["reasons"]


def test_preference_guide_endpoint_returns_fields():
    response = client.get("/guide/preferences")
    assert response.status_code == 200
    body = response.json()
    assert body["fields"]
    assert any(field["field"] == "entrance_exam" for field in body["fields"])


def test_query_can_return_debug_trace():
    response = client.post(
        "/query",
        json={
            "question": "What do official sources say about IIT Hyderabad hostel facilities?",
            "college_name": "IIT Hyderabad",
            "debug": True,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["debug_trace"] is not None
    assert body["debug_trace"]["reranked_candidates"]


def test_query_abstains_on_unsupported_specific_claim():
    response = client.post(
        "/query",
        json={
            "question": "What was the exact highest salary package and closing rank for computer science at IIT Hyderabad in 2025?",
            "college_name": "IIT Hyderabad",
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "insufficient_evidence"
    assert body["citations"] == []


def test_query_with_public_signals_uses_stubbed_report(monkeypatch):
    from app.api import main

    async def fake_analyze(college_name: str, focus: str | None = None):
        return PublicSignalsReport(
            college_name=college_name,
            requested_focus=focus,
            reddit_signals=[
                RedditSignal(
                    source_id="r1",
                    title="IIT Hyderabad hostel discussion",
                    subreddit="r/iithyderabad",
                    url="https://reddit.com/r/iithyderabad/1",
                    post_date=datetime.now(timezone.utc),
                    themes=["hostel and mess"],
                    concerns=["Some students mention mess timing issues."],
                    sentiment="mixed",
                    confidence_score=0.71,
                    trust_label=SourceTrustLabel.student_reported,
                )
            ],
            youtube_themes=[
                ThemeSummary(
                    topic="placements",
                    summary="Placements came up in 2 independent source(s).",
                    recurring=True,
                    source_count=2,
                )
            ],
            reddit_themes=[
                ThemeSummary(
                    topic="hostel and mess",
                    summary="Hostel and mess came up in 1 independent source(s).",
                    recurring=False,
                    source_count=1,
                )
            ],
            bias_warnings=[
                BiasWarning(
                    source_type="youtube",
                    source_id="y1",
                    label=SourceTrustLabel.possibly_promotional,
                    warning="Video 'Sponsored IIT Hyderabad review' may be promotional.",
                )
            ],
        )

    monkeypatch.setattr(main.public_signals_service, "analyze", fake_analyze)

    response = client.post(
        "/query",
        json={
            "question": "What is campus life like at IIT Hyderabad?",
            "college_name": "IIT Hyderabad",
            "include_public_signals": True,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["public_signals_used"] is True
    assert body["bias_warnings"]
    assert body["public_signals_report"]["reddit_themes"]


def test_admin_colleges_list_returns_structured_error_on_store_failure(monkeypatch):
    from app.api import v1 as v1_module

    def raise_on_all(*args, **kwargs):
        raise RuntimeError("Store read failed")
    monkeypatch.setattr(v1_module.profile_store, "all", raise_on_all)
    response = client.get("/v1/admin/colleges")
    assert response.status_code == 500
    body = response.json()
    assert "error" in body
    assert body["error"]["code"] == "CORPUS_ERROR"


def test_health_ready_is_lightweight_and_safe():
    from unittest.mock import patch

    with patch("app.official.vector_store.OfficialVectorStore") as mock_vs:
        with patch("app.generation.service.build_answer_generator") as mock_build:
            response = client.get("/health/ready")
            assert response.status_code == 200
            body = response.json()
            assert body["subsystems"]["generator"]["status"] == "ok"
            assert "Provider:" in body["subsystems"]["generator"]["detail"]
            mock_vs.assert_not_called()
            mock_build.assert_not_called()
