from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_college_profiles_cover_same_colleges_as_official_corpus():
    profiles_path = ROOT / "data" / "college_profiles.json"
    corpus_path = ROOT / "data" / "official_corpus.json"

    profiles = json.loads(profiles_path.read_text(encoding="utf-8"))
    corpus = json.loads(corpus_path.read_text(encoding="utf-8-sig"))

    profile_names = {item["college_name"] for item in profiles}
    corpus_names = {item["college_name"] for item in corpus}

    assert len(profiles) == 15
    assert profile_names == corpus_names


def test_college_profiles_have_matching_metadata():
    profiles = json.loads((ROOT / "data" / "college_profiles.json").read_text(encoding="utf-8"))

    for profile in profiles:
        assert profile["accepted_exams"]
        assert profile["branches"]
        assert profile["annual_cost_lakh"]["total"] > 0
        assert isinstance(profile["hostel_available"], bool)
        assert profile["official_admissions_url"].startswith("https://")
