from __future__ import annotations

import pytest
from app.models import RecommendationRequest
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
