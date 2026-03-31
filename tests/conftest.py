from __future__ import annotations

import os
import sys
from pathlib import Path


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
