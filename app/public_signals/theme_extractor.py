from __future__ import annotations

from collections import Counter, defaultdict

from app.models import ThemeSummary


TOPIC_KEYWORDS = {
    "placements": ("placement", "placements", "job", "jobs", "package", "internship"),
    "academics": ("academics", "curriculum", "course", "professor", "teaching"),
    "infrastructure": ("infrastructure", "lab", "labs", "building", "wifi", "classroom"),
    "hostel and mess": ("hostel", "mess", "food", "room", "rooms"),
    "faculty and admin": ("faculty", "admin", "administration", "professor", "dean"),
    "internships and research": ("research", "internship", "internships", "labs", "projects"),
    "peer group and culture": ("peer", "culture", "crowd", "clubs", "fests", "community"),
    "location and connectivity": ("location", "city", "travel", "connectivity", "remote"),
    "common complaints": ("issue", "problem", "bad", "concern", "delay", "complaint"),
    "common positives": ("good", "great", "excellent", "best", "positive", "strong"),
}


def extract_topics(text: str) -> list[str]:
    lowered = text.lower()
    topics: list[str] = []
    for topic, keywords in TOPIC_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            topics.append(topic)
    return topics


def summarize_themes(items: list[dict], topic_key: str = "themes") -> list[ThemeSummary]:
    grouped_examples: dict[str, list[str]] = defaultdict(list)
    sentiments: dict[str, Counter] = defaultdict(Counter)
    source_ids: dict[str, set[str]] = defaultdict(set)

    for item in items:
        topics = item.get(topic_key) or []
        for topic in topics:
            source_id = item.get("source_id", "")
            source_ids[topic].add(source_id)
            example = item.get("title") or item.get("summary") or ""
            if example:
                grouped_examples[topic].append(example)
            sentiments[topic][item.get("sentiment", "mixed")] += 1

    summaries: list[ThemeSummary] = []
    for topic, ids in source_ids.items():
        sentiment = sentiments[topic].most_common(1)[0][0] if sentiments[topic] else "mixed"
        recurring = len(ids) >= 2
        summaries.append(
            ThemeSummary(
                topic=topic,
                summary=f"{topic.title()} came up in {len(ids)} independent source(s).",
                sentiment=sentiment,
                recurring=recurring,
                source_count=len(ids),
                examples=grouped_examples[topic][:3],
            )
        )

    return sorted(summaries, key=lambda item: (not item.recurring, -item.source_count, item.topic))
