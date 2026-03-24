from __future__ import annotations

from datetime import datetime, timezone
import hashlib
from pathlib import Path

from bs4 import BeautifulSoup
import httpx
from pypdf import PdfReader

from app.config import settings
from app.models import IngestResult
from app.official.corpus import OfficialChunk, OfficialCorpus, OfficialDocument
from app.official.vector_store import OfficialVectorStore


class OfficialIngestionService:
    def __init__(
        self,
        corpus: OfficialCorpus | None = None,
        vector_store: OfficialVectorStore | None = None,
    ) -> None:
        self.corpus = corpus or OfficialCorpus()
        self.vector_store = vector_store or OfficialVectorStore()
        self.vector_store.upsert_chunks(self.corpus.chunks)

    async def ingest(
        self,
        *,
        college_name: str,
        urls: list[str],
        file_paths: list[str],
        title: str | None = None,
        source_kind: str = "official",
    ) -> tuple[list[IngestResult], list[str]]:
        ingested: list[IngestResult] = []
        errors: list[str] = []
        new_documents: list[OfficialDocument] = []

        for url in urls:
            try:
                document = await self._document_from_url(college_name, url, title, source_kind)
                new_documents.append(document)
            except Exception as exc:
                errors.append(f"Failed to ingest URL {url}: {exc}")

        for file_path in file_paths:
            try:
                document = self._document_from_file(college_name, file_path, title, source_kind)
                new_documents.append(document)
            except Exception as exc:
                errors.append(f"Failed to ingest file {file_path}: {exc}")

        if new_documents:
            self.corpus.save_registry_documents(new_documents)
            all_chunk_map = {chunk.doc_id: [] for chunk in self.corpus.chunks}
            for chunk in self.corpus.chunks:
                all_chunk_map.setdefault(chunk.doc_id, []).append(chunk)
            upsert_chunks: list[OfficialChunk] = []
            for document in new_documents:
                chunks = all_chunk_map.get(document.doc_id, [])
                upsert_chunks.extend(chunks)
                ingested.append(
                    IngestResult(
                        document_id=document.doc_id,
                        title=document.title,
                        source=document.url,
                        chunk_count=len(chunks),
                    )
                )
            self.vector_store.upsert_chunks(upsert_chunks)

        return ingested, errors

    async def _document_from_url(
        self, college_name: str, url: str, title: str | None, source_kind: str
    ) -> OfficialDocument:
        async with httpx.AsyncClient(timeout=settings.request_timeout_seconds) as client:
            response = await client.get(url, follow_redirects=True)
            response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        page_title = title or (soup.title.string.strip() if soup.title and soup.title.string else url)
        text = " ".join(
            node.get_text(" ", strip=True)
            for node in soup.find_all(["p", "li", "h1", "h2", "h3", "article"])
        ).strip()
        if not text:
            text = soup.get_text(" ", strip=True)
        return OfficialDocument(
            doc_id=self._make_doc_id(college_name, url),
            college_name=college_name,
            title=page_title,
            url=url,
            published_at=datetime.now(timezone.utc),
            content=text,
            source_kind=source_kind,
        )

    def _document_from_file(
        self, college_name: str, file_path: str, title: str | None, source_kind: str
    ) -> OfficialDocument:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(path)
        page_title = title or path.stem
        suffix = path.suffix.lower()
        if suffix == ".pdf":
            reader = PdfReader(str(path))
            text = " ".join(page.extract_text() or "" for page in reader.pages)
        elif suffix in {".html", ".htm"}:
            soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
            text = soup.get_text(" ", strip=True)
        else:
            text = path.read_text(encoding="utf-8")
        return OfficialDocument(
            doc_id=self._make_doc_id(college_name, str(path.resolve())),
            college_name=college_name,
            title=page_title,
            url=str(path.resolve()),
            published_at=datetime.now(timezone.utc),
            content=text,
            source_kind=source_kind,
        )

    def _make_doc_id(self, college_name: str, source: str) -> str:
        digest = hashlib.sha1(f"{college_name}|{source}".encode("utf-8")).hexdigest()[:12]
        slug = college_name.lower().replace(" ", "-")
        return f"{slug}-{digest}"
