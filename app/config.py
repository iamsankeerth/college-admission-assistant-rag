from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = PROJECT_ROOT / "config"


def load_yaml_config(path: str | Path) -> dict:
    config_path = Path(path)
    if not config_path.is_absolute():
        config_path = PROJECT_ROOT / config_path
    if not config_path.exists():
        return {}
    with config_path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ValueError(f"Expected mapping config in {config_path}")
    return data


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    app_name: str = "College Admission Assistant RAG"
    environment: str = "development"

    cache_ttl_seconds: int = 60 * 60 * 24
    request_timeout_seconds: float = 20.0
    user_agent: str = "CollegeAdmissionAssistant/0.2 (official evidence rag)"

    reddit_limit: int = 8
    youtube_limit: int = 10
    youtube_max_results: int = 15
    public_signals_enabled: bool = False

    answer_provider: str = "gemini"
    gemini_api_key: str | None = None
    gemini_model: str = "gemini-2.5-flash"

    embedding_backend: str = "sentence_transformers"
    embedding_model_name: str = "BAAI/bge-small-en-v1.5"
    reranker_backend: str = "cross_encoder"
    reranker_model_name: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    retrieval_top_k_lexical: int = 10
    retrieval_top_k_vector: int = 10
    retrieval_top_k_rerank: int = 5
    min_rerank_score_to_answer: float = 0.1

    retrieval_config_path: str = "config/retrieval.yaml"
    model_config_path: str = "config/models.yaml"
    answer_prompt_path: str = "config/prompts/answer.yaml"
    abstain_prompt_path: str = "config/prompts/abstain.yaml"

    chroma_collection_name: str = "official_documents"
    chroma_persist_dir: str = "data/chroma"

    source_manifest_dir: str = "sources/colleges"
    eval_dataset_path: str = "evals/golden_queries.jsonl"
    eval_report_dir: str = "evals/reports"

    @property
    def retrieval_config(self) -> dict:
        return load_yaml_config(self.retrieval_config_path)

    @property
    def model_config_values(self) -> dict:
        return load_yaml_config(self.model_config_path)

    @property
    def answer_prompt(self) -> dict:
        return load_yaml_config(self.answer_prompt_path)

    @property
    def abstain_prompt(self) -> dict:
        return load_yaml_config(self.abstain_prompt_path)


@lru_cache(maxsize=1)
def get_settings() -> AppSettings:
    return AppSettings()


settings = get_settings()
