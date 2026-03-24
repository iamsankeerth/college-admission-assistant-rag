from __future__ import annotations

import re

from app.models import PromotionAssessment, PromotionFlag, SourceTrustLabel


PROMO_PATTERNS = (
    r"\bsponsored\b",
    r"\bpaid promotion\b",
    r"\bin collaboration with\b",
    r"\bpartner(?:ed)? with\b",
    r"\baffiliate\b",
    r"\bapply through\b",
    r"\bcounselling\b",
    r"\badmission guidance\b",
    r"\breferral\b",
)

PROMO_CHANNEL_HINTS = ("admission", "counselling", "career guidance", "consultancy")


def assess_promotion(title: str, description: str, transcript: str, channel_name: str) -> PromotionAssessment:
    haystack = " ".join([title, description, transcript]).lower()
    reasons: list[str] = []

    for pattern in PROMO_PATTERNS:
        if re.search(pattern, haystack):
            reasons.append(f"Matched promotion signal: `{pattern}`")

    lowered_channel = channel_name.lower()
    if any(token in lowered_channel for token in PROMO_CHANNEL_HINTS):
        reasons.append("Channel identity suggests counseling or admissions marketing.")

    if len(reasons) >= 2:
        return PromotionAssessment(
            status=PromotionFlag.promotional,
            trust_label=SourceTrustLabel.promotional,
            reasons=reasons,
        )

    if len(reasons) == 1:
        return PromotionAssessment(
            status=PromotionFlag.possibly_promotional,
            trust_label=SourceTrustLabel.possibly_promotional,
            reasons=reasons,
        )

    return PromotionAssessment(
        status=PromotionFlag.not_flagged,
        trust_label=SourceTrustLabel.public_commentary,
        reasons=[],
    )
