from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

os.environ.setdefault("ANSWER_PROVIDER", "template")
os.environ.setdefault("EMBEDDING_BACKEND", "hash")
os.environ.setdefault("RERANKER_BACKEND", "heuristic")
os.environ.setdefault("RETRIEVAL_TOP_K_LEXICAL", "6")
os.environ.setdefault("RETRIEVAL_TOP_K_VECTOR", "6")
os.environ.setdefault("RETRIEVAL_TOP_K_RERANK", "5")
os.environ.setdefault("MIN_RERANK_SCORE_TO_ANSWER", "0.05")
os.environ.setdefault("PUBLIC_SIGNALS_ENABLED", "true")


@pytest.fixture
def workspace_tmp_path():
    """Repo-local temp dir to avoid Windows system-temp permission issues."""
    tmp_dir = ROOT / "tmp_test"
    tmp_dir.mkdir(exist_ok=True)
    yield tmp_dir
    shutil.rmtree(tmp_dir, ignore_errors=True)
