from __future__ import annotations

from pydantic import BaseModel, Field


class AppSettings(BaseModel):
    cache_ttl_seconds: int = Field(default=60 * 60 * 24)
    reddit_limit: int = Field(default=8)
    youtube_limit: int = Field(default=10)
    youtube_max_results: int = Field(default=15)
    request_timeout_seconds: float = Field(default=20.0)
    user_agent: str = Field(
        default="CollegeAdmissionAssistant/0.1 (public signals pipeline)"
    )


settings = AppSettings()
