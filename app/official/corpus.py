from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
import re


TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
SENTENCE_PATTERN = re.compile(r"(?<=[.!?])\s+")


def tokenize(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text.lower())


def split_sentences(text: str) -> list[str]:
    if not text.strip():
        return []
    return [sentence.strip() for sentence in SENTENCE_PATTERN.split(text.strip()) if sentence.strip()]


def chunk_text(text: str, chunk_size: int = 650, overlap: int = 120) -> list[str]:
    sentences = split_sentences(text)
    if not sentences:
        return []

    chunks: list[str] = []
    current_sentences: list[str] = []
    current_tokens = 0

    for sentence in sentences:
        sentence_tokens = tokenize(sentence)
        if not sentence_tokens:
            continue

        if current_sentences and current_tokens + len(sentence_tokens) > chunk_size:
            chunks.append(" ".join(current_sentences).strip())
            overlap_sentences: list[str] = []
            overlap_tokens = 0
            for existing in reversed(current_sentences):
                existing_tokens = len(tokenize(existing))
                overlap_sentences.insert(0, existing)
                overlap_tokens += existing_tokens
                if overlap_tokens >= overlap:
                    break
            current_sentences = overlap_sentences[:]
            current_tokens = overlap_tokens

        current_sentences.append(sentence)
        current_tokens += len(sentence_tokens)

    if current_sentences:
        chunks.append(" ".join(current_sentences).strip())

    return chunks


@dataclass(slots=True)
class OfficialDocument:
    doc_id: str
    college_name: str
    title: str
    url: str
    published_at: datetime | None
    content: str
    source_kind: str = "official"


@dataclass(slots=True)
class OfficialChunk:
    chunk_id: str
    doc_id: str
    college_name: str
    title: str
    url: str
    content: str
    published_at: datetime | None
    tokens: list[str]
    source_kind: str = "official"


class OfficialCorpus:
    def __init__(
        self,
        corpus_path: str | Path | None = None,
        registry_path: str | Path | None = None,
    ) -> None:
        base_dir = Path(__file__).resolve().parents[2] / "data"
        self.corpus_path = Path(corpus_path) if corpus_path else base_dir / "official_corpus.json"
        self.registry_path = Path(registry_path) if registry_path else base_dir / "official_registry.json"
        self.documents = self._load_documents()
        self.chunks = self._build_chunks(self.documents)

    def refresh(self) -> None:
        self.documents = self._load_documents()
        self.chunks = self._build_chunks(self.documents)

    def _load_documents(self) -> list[OfficialDocument]:
        documents = self._read_document_file(self.corpus_path)
        documents.extend(self._read_document_file(self.registry_path))
        deduped: dict[str, OfficialDocument] = {document.doc_id: document for document in documents}
        return list(deduped.values())

    def _read_document_file(self, path: Path) -> list[OfficialDocument]:
        if not path.exists():
            return []
        raw = json.loads(path.read_text(encoding="utf-8-sig"))
        documents: list[OfficialDocument] = []
        for item in raw:
            published = item.get("published_at")
            documents.append(
                OfficialDocument(
                    doc_id=item["doc_id"],
                    college_name=item["college_name"],
                    title=item["title"],
                    url=item["url"],
                    published_at=datetime.fromisoformat(published.replace("Z", "+00:00"))
                    if isinstance(published, str) and published
                    else None,
                    content=item["content"],
                    source_kind=item.get("source_kind", "official"),
                )
            )
        return documents

    def save_registry_documents(self, documents: list[OfficialDocument]) -> None:
        existing = {document.doc_id: document for document in self._read_document_file(self.registry_path)}
        for document in documents:
            existing[document.doc_id] = document
        serializable = []
        for document in existing.values():
            item = asdict(document)
            if document.published_at is not None:
                item["published_at"] = document.published_at.isoformat()
            serializable.append(item)
        self.registry_path.write_text(
            json.dumps(serializable, indent=2, ensure_ascii=True),
            encoding="utf-8",
        )
        self.refresh()

    def _build_chunks(self, documents: list[OfficialDocument]) -> list[OfficialChunk]:
        chunks: list[OfficialChunk] = []
        for document in documents:
            for idx, chunk_text_value in enumerate(chunk_text(document.content)):
                chunks.append(
                    OfficialChunk(
                        chunk_id=f"{document.doc_id}::chunk-{idx}",
                        doc_id=document.doc_id,
                        college_name=document.college_name,
                        title=document.title,
                        url=document.url,
                        content=chunk_text_value,
                        published_at=document.published_at,
                        tokens=tokenize(chunk_text_value),
                        source_kind=document.source_kind,
                    )
                )
        return chunks
