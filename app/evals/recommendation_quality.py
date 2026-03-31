from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path

from app.config import settings
from app.recommendation.service import RecommendationService


TEST_PROFILES = [
    {
        "entrance_exam": "JEE Advanced",
        "rank": 2500,
        "preferred_branches": ["Computer Science and Engineering"],
        "budget_lakh": 5.0,
        "preferred_zones": ["South"],
        "hostel_required": True,
        "max_results": 5,
    },
    {
        "entrance_exam": "JEE Main",
        "rank": 12000,
        "preferred_branches": ["Electrical Engineering", "Mechanical Engineering"],
        "budget_lakh": 4.0,
        "preferred_states": ["Karnataka", "Tamil Nadu", "Maharashtra"],
        "hostel_required": True,
        "max_results": 5,
    },
    {
        "entrance_exam": "JEE Main",
        "rank": 45000,
        "preferred_branches": ["Civil Engineering", "Mechanical Engineering"],
        "budget_lakh": 3.0,
        "preferred_zones": ["North", "Central"],
        "hostel_required": False,
        "max_results": 5,
    },
]


async def run_recommendation_quality_check() -> dict:
    service = RecommendationService()
    results: list[dict] = []

    for profile in TEST_PROFILES:
        from app.models import RecommendationRequest
        request = RecommendationRequest(**profile)
        response = await service.recommend(request)
        checks = _check_quality(response)
        results.append({**profile, **checks})

    failing_profiles = [r for r in results if not r["pass"]]
    failing_metrics = []
    for fp in failing_profiles:
        for issue in fp["issues"]:
            failing_metrics.append(f"{fp['college_id'] if 'college_id' in fp else 'unknown'}: {issue}")

    all_pass = len(failing_profiles) == 0
    return {
        "status": "pass" if all_pass else "fail",
        "total_profiles": len(TEST_PROFILES),
        "passed": len(results) - len(failing_profiles),
        "failing_profiles_count": len(failing_profiles),
        "failing_metrics": failing_metrics,
        "results": results,
    }


def _check_quality(response) -> dict:
    recommendations = response.recommendations
    issues: list[str] = []

    if not recommendations:
        issues.append("No recommendations returned")
        return {"pass": False, "issues": issues}

    for item in recommendations:
        if item.base_score <= 0:
            issues.append(f"Zero/negative base_score for {item.college_name}")
        if item.final_score < 0:
            issues.append(f"Negative final_score for {item.college_name}")
        if item.enrichment_status and item.enrichment_status.value == "failed":
            issues.append(f"Enrichment failed for {item.college_name}")
        if item.base_score < item.final_score - 0.06:
            issues.append(f"Unusually large hybrid adjustment for {item.college_name}")
        if item.final_score > 1.05:
            issues.append(f"final_score exceeds 1.05 cap for {item.college_name}")

    if not recommendations[0].reasons:
        issues.append("Top recommendation has no reasons")

    return {
        "pass": len(issues) == 0,
        "issues": issues,
        "top_college": recommendations[0].college_name if recommendations else None,
        "top_score": recommendations[0].final_score if recommendations else None,
        "enrichment_statuses": [r.enrichment_status.value if r.enrichment_status else "unknown" for r in recommendations],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run recommendation quality gate.")
    parser.add_argument("--report", default=str(Path(settings.eval_report_dir) / "rec_quality_check.json"))
    args = parser.parse_args()

    result = asyncio.run(run_recommendation_quality_check())

    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(result, indent=2), encoding="utf-8")

    print(json.dumps(result, indent=2))

    if result["status"] == "fail":
        print(f"\nFailing metrics ({len(result['failing_metrics'])}):")
        for fm in result["failing_metrics"]:
            print(f"  - {fm}")
        raise SystemExit(f"Recommendation quality failed: {result['failing_profiles_count']}/{result['total_profiles']} profiles failed")


if __name__ == "__main__":
    main()
