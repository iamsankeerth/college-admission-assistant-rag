from __future__ import annotations

import asyncio
from urllib.parse import urlparse

from app.ingest.manifests import load_manifests
from app.official.service import OfficialEvidenceService


async def main() -> None:
    service = OfficialEvidenceService()
    for manifest in load_manifests():
        allowed_domains = set(manifest.allowed_domains)
        filtered_urls = [
            str(url)
            for url in manifest.seed_urls
            if not allowed_domains or urlparse(str(url)).netloc in allowed_domains
        ]
        result = await service.ingest_sources(
            college_name=manifest.college_name,
            urls=filtered_urls,
            file_paths=[],
            source_kind=manifest.source_kind_defaults.get("default", "official"),
        )
        print(f"{manifest.college_name}: {len(result.ingested)} ingested, {len(result.errors)} errors")


if __name__ == "__main__":
    asyncio.run(main())
