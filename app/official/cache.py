from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path

from app.config import settings
from app.models import RetrievedChunk


class RetrievalCache:
    def __init__(self, cache_dir: str | Path | None = None, ttl_seconds: int | None = None) -> None:
        base = Path(__file__).resolve().parents[2]
        self.cache_dir = Path(cache_dir) if cache_dir else base / "data" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = ttl_seconds if ttl_seconds is not None else settings.cache_ttl_seconds

    def _cache_key(self, normalized_query: str, college_name: str | None) -> str:
        raw = f"{normalized_query}|{college_name or ''}"
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    def _cache_path(self, cache_key: str) -> Path:
        return self.cache_dir / f"{cache_key}.json"

    def get(self, normalized_query: str, college_name: str | None) -> list[RetrievedChunk] | None:
        if self.ttl_seconds <= 0:
            return None

        cache_key = self._cache_key(normalized_query, college_name)
        path = self._cache_path(cache_key)

        if not path.exists():
            return None

        try:
            age = time.time() - path.stat().st_mtime
            if age > self.ttl_seconds:
                path.unlink(missing_ok=True)
                return None

            data = json.loads(path.read_text(encoding="utf-8"))
            return [RetrievedChunk.model_validate(c) for c in data]
        except (OSError, json.JSONDecodeError, ValueError):
            path.unlink(missing_ok=True)
            return None

    def set(
        self,
        normalized_query: str,
        college_name: str | None,
        chunks: list[RetrievedChunk],
    ) -> None:
        if self.ttl_seconds <= 0:
            return

        cache_key = self._cache_key(normalized_query, college_name)
        path = self._cache_path(cache_key)

        try:
            path.write_text(
                json.dumps([c.model_dump(mode="json") for c in chunks], ensure_ascii=False),
                encoding="utf-8",
            )
        except OSError:
            pass

    def invalidate(self, college_name: str | None = None) -> None:
        if college_name is None:
            for path in self.cache_dir.glob("*.json"):
                path.unlink(missing_ok=True)
            return

        for path in self.cache_dir.glob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                if any(
                    c.get("college_name", "").lower() == college_name.lower()
                    for c in data
                ):
                    path.unlink(missing_ok=True)
            except (OSError, json.JSONDecodeError):
                path.unlink(missing_ok=True)

    def clear(self) -> None:
        for path in self.cache_dir.glob("*.json"):
            path.unlink(missing_ok=True)
