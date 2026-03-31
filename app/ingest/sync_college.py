from __future__ import annotations

import argparse
import asyncio
from urllib.parse import urlparse

from app.ingest.manifests import load_manifest
from app.official.service import OfficialEvidenceService


async def main() -> None:
    parser = argparse.ArgumentParser(description="Sync one college manifest into the registry.")
    parser.add_argument("--college", required=True, help="College name matching a manifest file.")
    args = parser.parse_args()

    manifest = load_manifest(args.college)
    service = OfficialEvidenceService()
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
    print(f"Ingested: {len(result.ingested)}")
    print(f"Errors: {len(result.errors)}")
    for error in result.errors:
        print(error)


if __name__ == "__main__":
    asyncio.run(main())
