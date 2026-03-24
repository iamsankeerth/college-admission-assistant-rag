from __future__ import annotations

import re


COLLEGE_HINTS = (
    "iit",
    "nit",
    "iiit",
    "bits",
    "university",
    "college",
    "campus",
    "institute",
)

PUBLIC_SIGNAL_HINTS = (
    "student opinion",
    "student review",
    "student reviews",
    "college reality",
    "placements reality",
    "campus life",
    "hostel life",
    "is this college worth it",
    "reddit",
    "youtube",
    "student life",
)


def detect_college_name(question: str) -> str | None:
    patterns = [
        r"\b(IIT\s+[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\b",
        r"\b(NIT\s+[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\b",
        r"\b(IIIT\s+[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\b",
        r"\b(BITS\s+[A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+)*)\b",
        r"\b([A-Z][a-zA-Z]+(?:\s+[A-Z][a-zA-Z]+){0,4}\s+(?:College|University|Institute))\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, question)
        if match:
            return match.group(1).strip()
    return None


def should_use_public_signals(question: str, college_name: str | None = None) -> bool:
    normalized = question.lower()
    if college_name:
        return True

    if any(token in normalized for token in PUBLIC_SIGNAL_HINTS):
        return True

    if any(token in normalized for token in COLLEGE_HINTS) and re.search(
        r"\b(placements?|infrastructure|hostel|culture|campus|worth|reality)\b",
        normalized,
    ):
        return True

    return False
