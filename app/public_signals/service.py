from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from cachetools import TTLCache

from app.config import settings
from app.models import (
    BiasWarning,
    PublicSignalsReport,
    RedditSignal,
    SourceTrustLabel,
    YouTubeSignal,
)
from app.public_signals.promo_detector import assess_promotion
from app.public_signals.reddit_fetch import RedditFetcher
from app.public_signals.source_scorer import score_public_source
from app.public_signals.theme_extractor import summarize_themes
from app.public_signals.transcript_parser import analyze_text
from app.public_signals.youtube_fetch import YouTubeFetcher


class PublicSignalsService:
    def __init__(
        self,
        reddit_fetcher: RedditFetcher | None = None,
        youtube_fetcher: YouTubeFetcher | None = None,
    ) -> None:
        self.reddit_fetcher = reddit_fetcher or RedditFetcher()
        self.youtube_fetcher = youtube_fetcher or YouTubeFetcher()
        self.cache: TTLCache[str, PublicSignalsReport] = TTLCache(
            maxsize=128, ttl=settings.cache_ttl_seconds
        )

    async def analyze(self, college_name: str, focus: str | None = None) -> PublicSignalsReport:
        cache_key = self._cache_key(college_name, focus)
        cached = self.cache.get(cache_key)
        if cached:
            return cached

        errors: list[str] = []
        reddit_signals: list[RedditSignal] = []
        youtube_signals: list[YouTubeSignal] = []
        bias_warnings: list[BiasWarning] = []

        try:
            reddit_items = await self.reddit_fetcher.fetch(college_name, focus)
            reddit_signals = [self._build_reddit_signal(college_name, item) for item in reddit_items]
        except Exception as exc:  # pragma: no cover
            errors.append(f"Reddit data was unavailable: {exc}")

        try:
            with ThreadPoolExecutor(max_workers=1) as pool:
                youtube_items = pool.submit(self.youtube_fetcher.fetch, college_name, focus).result()
            youtube_signals = [
                self._build_youtube_signal(college_name, item) for item in youtube_items
            ]
        except Exception as exc:  # pragma: no cover
            errors.append(f"YouTube data was unavailable: {exc}")

        for signal in youtube_signals:
            if signal.promotion.trust_label in (
                SourceTrustLabel.promotional,
                SourceTrustLabel.possibly_promotional,
            ):
                bias_warnings.append(
                    BiasWarning(
                        source_type="youtube",
                        source_id=signal.source_id,
                        label=signal.promotion.trust_label,
                        warning=(
                            f"Video '{signal.title}' may be promotional. "
                            "Treat strong positive claims cautiously."
                        ),
                    )
                )

        report = PublicSignalsReport(
            college_name=college_name,
            requested_focus=focus,
            reddit_signals=reddit_signals,
            youtube_signals=youtube_signals,
            reddit_themes=summarize_themes([signal.model_dump() for signal in reddit_signals]),
            youtube_themes=summarize_themes([signal.model_dump() for signal in youtube_signals]),
            bias_warnings=bias_warnings,
            errors=errors,
            generated_at=datetime.now(timezone.utc),
        )
        self.cache[cache_key] = report
        return report

    def _cache_key(self, college_name: str, focus: str | None) -> str:
        date_key = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        return f"{college_name.lower()}::{(focus or '').lower()}::{date_key}"

    def _build_reddit_signal(self, college_name: str, item: dict) -> RedditSignal:
        analysis = analyze_text(item.get("text", ""))
        confidence, trust_label = score_public_source(
            college_name,
            text=item.get("text", ""),
            published_at=item.get("post_date"),
            role_clues=analysis["role_clues"],
            transcript_richness=analysis["transcript_richness"],
        )
        return RedditSignal(
            source_id=item["source_id"],
            title=item["title"],
            subreddit=item["subreddit"],
            url=item["url"],
            post_date=item.get("post_date"),
            themes=analysis["themes"],
            positives=analysis["positives"],
            concerns=analysis["concerns"],
            top_comments=item.get("top_comments", []),
            sentiment=analysis["sentiment"],
            role_clues=analysis["role_clues"],
            confidence_score=round(confidence, 3),
            trust_label=SourceTrustLabel.student_reported
            if trust_label != SourceTrustLabel.low_confidence
            else trust_label,
        )

    def _build_youtube_signal(self, college_name: str, item: dict) -> YouTubeSignal:
        combined_text = " ".join(
            part for part in [item.get("title", ""), item.get("description", ""), item.get("transcript", "")]
        )
        analysis = analyze_text(combined_text)
        promotion = assess_promotion(
            item.get("title", ""),
            item.get("description", ""),
            item.get("transcript", ""),
            item.get("channel_name", ""),
        )
        confidence, trust_label = score_public_source(
            college_name,
            text=combined_text,
            published_at=item.get("publish_date"),
            role_clues=analysis["role_clues"],
            transcript_richness=analysis["transcript_richness"],
            promotion_status=promotion.status,
        )
        return YouTubeSignal(
            source_id=item["source_id"],
            title=item["title"],
            url=item["url"],
            channel_name=item["channel_name"],
            publish_date=item.get("publish_date"),
            description=item.get("description", ""),
            transcript=item.get("transcript", ""),
            duration_seconds=item.get("duration_seconds"),
            view_count=item.get("view_count"),
            themes=analysis["themes"],
            positives=analysis["positives"],
            concerns=analysis["concerns"],
            role_clues=analysis["role_clues"],
            transcript_available=item.get("transcript_available", False),
            confidence_score=round(confidence, 3),
            promotion=promotion.model_copy(update={"trust_label": trust_label}),
        )
