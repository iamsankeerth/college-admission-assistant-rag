from __future__ import annotations

import re

from app.public_signals.theme_extractor import extract_topics


POSITIVE_WORDS = ("good", "great", "excellent", "strong", "impressive", "supportive")
NEGATIVE_WORDS = ("bad", "poor", "issue", "problem", "concern", "weak", "delay")
ROLE_PATTERNS = {
    "current_student": r"\b(i am|i'm)\s+(a\s+)?(student|undergrad|postgrad)\b",
    "alumnus": r"\b(alumnus|alumni|graduated|passout)\b",
    "applicant": r"\b(applicant|aspirant|considering|planning to join)\b",
}


def split_points(text: str) -> list[str]:
    candidates = re.split(r"[.\n!?]+", text)
    return [segment.strip() for segment in candidates if segment.strip()]


def detect_sentiment(text: str) -> str:
    lowered = text.lower()
    pos = sum(lowered.count(word) for word in POSITIVE_WORDS)
    neg = sum(lowered.count(word) for word in NEGATIVE_WORDS)
    if pos > neg:
        return "positive"
    if neg > pos:
        return "negative"
    return "mixed"


def detect_role_clues(text: str) -> list[str]:
    lowered = text.lower()
    clues: list[str] = []
    for clue, pattern in ROLE_PATTERNS.items():
        if re.search(pattern, lowered):
            clues.append(clue)
    return clues or ["unknown"]


def extract_highlights(text: str) -> tuple[list[str], list[str]]:
    positives: list[str] = []
    concerns: list[str] = []
    for segment in split_points(text):
        lowered = segment.lower()
        if any(word in lowered for word in POSITIVE_WORDS):
            positives.append(segment)
        if any(word in lowered for word in NEGATIVE_WORDS):
            concerns.append(segment)
    return positives[:5], concerns[:5]


def analyze_text(text: str) -> dict:
    topics = extract_topics(text)
    positives, concerns = extract_highlights(text)
    return {
        "themes": topics,
        "positives": positives,
        "concerns": concerns,
        "sentiment": detect_sentiment(text),
        "role_clues": detect_role_clues(text),
        "transcript_richness": min(len(text.split()) / 400.0, 1.0),
    }
