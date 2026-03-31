from __future__ import annotations

from pathlib import Path

import yaml

from app.config import settings
from app.models import CollegeSourceManifest


def manifest_dir() -> Path:
    return Path(settings.source_manifest_dir)


def load_manifests() -> list[CollegeSourceManifest]:
    manifests: list[CollegeSourceManifest] = []
    for path in sorted(manifest_dir().glob("*.yaml")):
        with path.open("r", encoding="utf-8") as handle:
            payload = yaml.safe_load(handle) or {}
        manifests.append(CollegeSourceManifest.model_validate(payload))
    return manifests


def load_manifest(college_name: str) -> CollegeSourceManifest:
    normalized = college_name.strip().lower()
    for manifest in load_manifests():
        if manifest.college_name.lower() == normalized:
            return manifest
    raise FileNotFoundError(f"No manifest found for college '{college_name}'")
