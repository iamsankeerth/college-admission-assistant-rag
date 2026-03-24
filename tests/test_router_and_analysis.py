from app.public_signals.promo_detector import assess_promotion
from app.public_signals.router import detect_college_name, should_use_public_signals
from app.public_signals.theme_extractor import summarize_themes


def test_detect_college_name_from_question():
    assert detect_college_name("Is IIT Hyderabad worth it for CSE?") == "IIT Hyderabad"


def test_should_use_public_signals_for_student_reality_query():
    assert should_use_public_signals(
        "Tell me the placements reality and campus life at IIT Hyderabad"
    )


def test_promo_detector_flags_sponsored_video():
    result = assess_promotion(
        "IIT Hyderabad review",
        "This video is sponsored and includes admission guidance links.",
        "Paid promotion and partner offer for applications.",
        "Best Admission Consultancy",
    )
    assert result.status == "promotional"


def test_theme_summary_marks_recurring_topics():
    summaries = summarize_themes(
        [
            {"source_id": "a", "themes": ["placements"], "sentiment": "mixed", "title": "One"},
            {"source_id": "b", "themes": ["placements"], "sentiment": "positive", "title": "Two"},
        ]
    )
    placement_summary = next(item for item in summaries if item.topic == "placements")
    assert placement_summary.recurring is True
    assert placement_summary.source_count == 2
