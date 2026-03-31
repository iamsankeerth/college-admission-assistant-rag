from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from app.config import settings


class CorpusVersion:
    def __init__(
        self,
        version: str,
        schema_version: str,
        chunk_count: int,
        college_count: int,
        updated_at: datetime | None = None,
        document_count: int = 0,
    ) -> None:
        self.version = version
        self.schema_version = schema_version
        self.chunk_count = chunk_count
        self.college_count = college_count
        self.document_count = document_count
        self.updated_at = updated_at or datetime.now(timezone.utc)

    def to_dict(self) -> dict:
        return {
            "version": self.version,
            "schema_version": self.schema_version,
            "chunk_count": self.chunk_count,
            "college_count": self.college_count,
            "document_count": self.document_count,
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> CorpusVersion:
        updated_at = data.get("updated_at")
        if isinstance(updated_at, str):
            updated_at = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
        return cls(
            version=data["version"],
            schema_version=data["schema_version"],
            chunk_count=data["chunk_count"],
            college_count=data["college_count"],
            document_count=data.get("document_count", 0),
            updated_at=updated_at,
        )

    def is_stale(self, max_age_days: int = 30) -> bool:
        if not self.updated_at:
            return True
        age = datetime.now(timezone.utc) - self.updated_at
        return age.days > max_age_days


class CorpusManager:
    def __init__(self, version_file: str | Path | None = None) -> None:
        base = Path(__file__).resolve().parents[2]
        self.version_file = (
            Path(version_file) if version_file else base / "data" / "corpus_version.json"
        )

    def get_version(self) -> CorpusVersion | None:
        if not self.version_file.exists():
            return None
        try:
            data = json.loads(self.version_file.read_text(encoding="utf-8"))
            return CorpusVersion.from_dict(data)
        except (OSError, json.JSONDecodeError, KeyError):
            return None

    def write_version(self, version: CorpusVersion) -> None:
        self.version_file.parent.mkdir(parents=True, exist_ok=True)
        self.version_file.write_text(
            json.dumps(version.to_dict(), indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def update_from_corpus(
        self,
        corpus,
        college_count: int,
        version: str | None = None,
    ) -> CorpusVersion:
        current = self.get_version()
        new_version = CorpusVersion(
            version=version or self._next_version(current),
            schema_version=settings.index_schema_version,
            chunk_count=len(corpus.chunks) if hasattr(corpus, "chunks") else 0,
            college_count=college_count,
            document_count=len(corpus.documents) if hasattr(corpus, "documents") else 0,
        )
        self.write_version(new_version)
        return new_version

    def _next_version(self, current: CorpusVersion | None) -> str:
        if current is None:
            return "1.0.0"
        parts = current.version.split(".")
        major = int(parts[0]) if parts else 1
        minor = int(parts[1]) if len(parts) > 1 else 0
        patch = int(parts[2]) if len(parts) > 2 else 0
        patch += 1
        return f"{major}.{minor}.{patch}"
