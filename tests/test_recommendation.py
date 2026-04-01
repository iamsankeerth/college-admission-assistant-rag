from __future__ import annotations

import pytest
from app.models import EnrichmentStatus, RecommendationRequest
from app.recommendation.service import CollegeProfileRepository, RecommendationService, build_preference_guide


@pytest.mark.asyncio
async def test_recommendation_service_returns_ranked_matches():
    service = RecommendationService()
    response = await service.recommend(
        RecommendationRequest(
            entrance_exam="JEE Advanced",
            rank=1200,
            preferred_branches=["Computer Science and Engineering", "Electrical Engineering"],
            budget_lakh=4.0,
            preferred_states=["Telangana", "Tamil Nadu"],
            preferred_zones=["South"],
            hostel_required=True,
            max_results=5,
        )
    )
    assert response.recommendations
    assert response.recommendations[0].score >= response.recommendations[-1].score
    assert all(item.hostel_available for item in response.recommendations)


@pytest.mark.asyncio
async def test_recommend_always_hydrates_official_even_when_public_disabled():
    service = RecommendationService()
    response = await service.recommend(
        RecommendationRequest(
            entrance_exam="JEE Main",
            rank=8000,
            preferred_branches=["Computer Science and Engineering"],
            budget_lakh=5.0,
            preferred_zones=["South"],
            hostel_required=True,
            max_results=3,
            include_public_signals=False,
        )
    )
    assert response.recommendations
    for item in response.recommendations:
        assert item.enrichment_status == EnrichmentStatus.HYDRATED
        assert item.enrichment is not None
        assert item.enrichment.outcomes_and_campus is not None
        assert item.public_signals_report is None


@pytest.mark.asyncio
async def test_recommend_public_signals_adjustment_with_flag_enabled():
    service = RecommendationService()
    response = await service.recommend(
        RecommendationRequest(
            entrance_exam="JEE Main",
            rank=8000,
            preferred_branches=["Computer Science and Engineering"],
            budget_lakh=5.0,
            preferred_zones=["South"],
            hostel_required=True,
            max_results=3,
            include_public_signals=True,
        )
    )
    assert response.recommendations
    for item in response.recommendations:
        assert item.enrichment_status == EnrichmentStatus.HYDRATED


@pytest.mark.asyncio
async def test_explore_honors_include_public_signals_flag():
    from app.models import CollegeExploreRequest
    service = RecommendationService()

    response_no_public = await service.explore(
        CollegeExploreRequest(
            college_name="IIT Hyderabad",
            include_public_signals=False,
        )
    )
    assert response_no_public.enrichment is not None
    assert response_no_public.public_signals_report is None

    response_with_public = await service.explore(
        CollegeExploreRequest(
            college_name="IIT Hyderabad",
            include_public_signals=True,
        )
    )
    assert response_with_public.enrichment is not None


def test_hybrid_adjustment_final_score_bounded():
    service = RecommendationService()
    repo = CollegeProfileRepository()
    profiles = repo.all()

    for profile in profiles[:3]:
        item = service._score_profile(
            profile,
            RecommendationRequest(
                entrance_exam="JEE Main",
                rank=10000,
                preferred_branches=["Computer Science and Engineering"],
                budget_lakh=10.0,
                max_results=5,
            ),
        )
        if item is not None:
            assert item.final_score >= 0.0, f"final_score should not be negative for {profile.college_name}"
            assert item.final_score <= item.base_score + 0.06, f"final_score should be within +0.06 of base for {profile.college_name}"


def test_hybrid_adjustment_total_capped_at_plus_0_05():
    service = RecommendationService()

    from app.models import PublicSignalsReport
    fake_report = PublicSignalsReport(
        college_name="Test",
        reddit_themes=[],
        youtube_themes=[],
        bias_warnings=[],
    )

    official_adj = 0.04
    public_adj = 0.02
    _, _, total = service._enforce_adjustment_policy(official_adj, public_adj, fake_report)
    assert total <= 0.05, f"Total adjustment {total} should be capped at 0.05"

    official_adj = 0.0
    public_adj = 0.02
    _, _, total = service._enforce_adjustment_policy(official_adj, public_adj, fake_report)
    assert abs(total) <= 0.01, f"Neutral official should allow only ±0.01 nudge, got {total}"


def test_negative_official_adj_blocks_positive_public_adj():
    service = RecommendationService()

    from app.models import PublicSignalsReport
    fake_report = PublicSignalsReport(
        college_name="Test",
        reddit_themes=[],
        youtube_themes=[],
        bias_warnings=[],
    )

    official_adj = -0.02
    public_adj = 0.02
    _, final_public, total = service._enforce_adjustment_policy(official_adj, public_adj, fake_report)
    assert final_public == 0.0, "Negative official should block positive public adjustment"
    assert total <= official_adj, f"Total {total} should not exceed official_adj {official_adj}"


def test_recommendation_repository_loads_all_profiles():
    repository = CollegeProfileRepository()
    profiles = repository.all()
    assert len(profiles) == 15
    assert any(profile.college_name == "IIT Hyderabad" for profile in profiles)


def test_preference_guide_contains_key_fields():
    guide = build_preference_guide()
    field_names = {field.field for field in guide.fields}
    assert "entrance_exam" in field_names
    assert "budget_lakh" in field_names
