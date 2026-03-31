from __future__ import annotations

import json
from pathlib import Path

from app.models import CollegeProfile


PROFILES_FILE = Path(__file__).resolve().parents[2] / "data" / "college_profiles.json"


class CollegeProfileStore:
    def __init__(self, profiles_path: str | Path | None = None) -> None:
        self.path = Path(profiles_path) if profiles_path else PROFILES_FILE
        self._profiles: dict[str, CollegeProfile] | None = None

    def _load(self) -> dict[str, CollegeProfile]:
        if self._profiles is not None:
            return self._profiles

        self._profiles = {}
        if self.path.exists():
            raw = json.loads(self.path.read_text(encoding="utf-8-sig"))
            for item in raw:
                profile = CollegeProfile.model_validate(item)
                self._profiles[profile.college_id] = profile
        return self._profiles

    def all(self) -> list[CollegeProfile]:
        return list(self._load().values())

    def get(self, college_id: str) -> CollegeProfile | None:
        return self._load().get(college_id)

    def upsert(self, profile: CollegeProfile) -> CollegeProfile:
        self._load()[profile.college_id] = profile
        self._save()
        return profile

    def delete(self, college_id: str) -> bool:
        if college_id in self._load():
            del self._load()[college_id]
            self._save()
            return True
        return False

    def _save(self) -> None:
        profiles = list(self._load().values())
        serializable = [p.model_dump() for p in profiles]
        self.path.write_text(
            json.dumps(serializable, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        self._profiles = None

    def invalidate_cache(self) -> None:
        self._profiles = None


store = CollegeProfileStore()
