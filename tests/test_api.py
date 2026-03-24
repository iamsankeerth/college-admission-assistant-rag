from datetime import datetime, timezone

from fastapi.testclient import TestClient

from app.api.main import app
from app.models import (
    BiasWarning,
    OfficialAnswer,
    OfficialSource,
    PublicSignalsReport,
    RedditSignal,
    SourceTrustLabel,
    ThemeSummary,
)


client = TestClient(app)


def test_query_without_public_signals_returns_official_answer():
    response = client.post(
        "/query",
        json={
            "question": "Explain how admissions work through official counselling.",
            "official_answer": {
                "summary": "Officially, admissions follow counselling notices.",
                "sources": [
                    {
                        "title": "Official Notice",
                        "url": "https://example.edu/notice",
                        "snippet": "Admissions follow official counselling notices.",
                    }
                ],
            },
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["public_signals_used"] is False
    assert body["official_answer"]["summary"] == "Officially, admissions follow counselling notices."


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
            "official_answer": {
                "summary": "Officially, hostel and campus information comes from institute pages.",
                "sources": [
                    {
                        "title": "Campus Life",
                        "url": "https://example.edu/campus",
                        "snippet": "The campus page describes hostel and student facilities.",
                    }
                ],
            },
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["public_signals_used"] is True
    assert body["bias_warnings"]
    assert "Student Signals: Reddit" in body["answer"]
