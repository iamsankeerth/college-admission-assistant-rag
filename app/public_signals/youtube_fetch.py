from __future__ import annotations

from datetime import datetime, timezone

from youtube_transcript_api import YouTubeTranscriptApi
from yt_dlp import YoutubeDL

from app.config import settings


class YouTubeFetcher:
    def fetch(self, college_name: str, focus: str | None = None) -> list[dict]:
        queries = [
            f"{college_name} campus tour",
            f"{college_name} placements",
            f"{college_name} review",
            f"{college_name} hostel",
            f"{college_name} reality",
            f"{college_name} student life",
        ]
        if focus:
            queries.insert(0, f"{college_name} {focus}")

        seen: set[str] = set()
        videos: list[dict] = []
        for query in queries:
            for entry in self._search(query):
                if entry["id"] in seen:
                    continue
                seen.add(entry["id"])
                videos.append(self._hydrate_video(entry))
                if len(videos) >= settings.youtube_max_results:
                    return videos
        return videos

    def _search(self, query: str) -> list[dict]:
        with YoutubeDL(
            {
                "quiet": True,
                "skip_download": True,
                "extract_flat": True,
            }
        ) as ydl:
            result = ydl.extract_info(f"ytsearch{settings.youtube_limit}:{query}", download=False)
        return result.get("entries", []) if result else []

    def _hydrate_video(self, entry: dict) -> dict:
        video_id = entry.get("id", "")
        transcript, transcript_available = self._get_transcript(video_id)
        upload_date = entry.get("upload_date")
        published_at = None
        if upload_date:
            published_at = datetime.strptime(upload_date, "%Y%m%d").replace(tzinfo=timezone.utc)

        return {
            "source_id": video_id,
            "title": entry.get("title", ""),
            "url": f"https://www.youtube.com/watch?v={video_id}",
            "channel_name": entry.get("channel", "") or entry.get("uploader", ""),
            "publish_date": published_at,
            "description": entry.get("description", "") or "",
            "transcript": transcript,
            "transcript_available": transcript_available,
            "duration_seconds": entry.get("duration"),
            "view_count": entry.get("view_count"),
        }

    def _get_transcript(self, video_id: str) -> tuple[str, bool]:
        if not video_id:
            return "", False
        try:
            transcript = YouTubeTranscriptApi.get_transcript(video_id)
        except Exception:
            return "", False
        text = " ".join(item.get("text", "") for item in transcript)
        return text, bool(text.strip())
