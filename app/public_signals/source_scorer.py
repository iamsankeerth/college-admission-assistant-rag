from __future__ import annotations

from datetime import datetime, timezone

from app.models import PromotionFlag, SourceTrustLabel


def recency_score(published_at: datetime | None) -> float:
    if published_at is None:
        return 0.4
    delta_days = (datetime.now(timezone.utc) - published_at.astimezone(timezone.utc)).days
    if delta_days <= 180:
        return 1.0
    if delta_days <= 365:
        return 0.8
    if delta_days <= 730:
        return 0.6
    return 0.4


def specificity_score(college_name: str, text: str) -> float:
    lowered = text.lower()
    name_tokens = [token for token in college_name.lower().split() if len(token) > 2]
    matched = sum(1 for token in name_tokens if token in lowered)
    return min(0.4 + matched * 0.2, 1.0)


def trust_label_from_score(score: float) -> SourceTrustLabel:
    if score < 0.35:
        return SourceTrustLabel.low_confidence
    return SourceTrustLabel.public_commentary


def score_public_source(
    college_name: str,
    *,
    text: str,
    published_at: datetime | None,
    role_clues: list[str],
    transcript_richness: float,
    promotion_status: PromotionFlag | None = None,
) -> tuple[float, SourceTrustLabel]:
    score = 0.0
    score += recency_score(published_at) * 0.25
    score += specificity_score(college_name, text) * 0.25
    score += transcript_richness * 0.25
    if role_clues and role_clues != ["unknown"]:
        score += 0.15
    else:
        score += 0.05

    if promotion_status == PromotionFlag.promotional:
        score -= 0.30
        return max(score, 0.0), SourceTrustLabel.promotional
    if promotion_status == PromotionFlag.possibly_promotional:
        score -= 0.15
        return max(score, 0.0), SourceTrustLabel.possibly_promotional

    return max(score, 0.0), trust_label_from_score(score)
