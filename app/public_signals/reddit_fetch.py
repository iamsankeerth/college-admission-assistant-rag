from __future__ import annotations

from datetime import datetime, timezone

import httpx

from app.config import settings


class RedditFetcher:
    async def fetch(self, college_name: str, focus: str | None = None) -> list[dict]:
        queries = [
            f"{college_name} {suffix} reddit"
            for suffix in ("placements", "infrastructure", "hostel", "college life")
        ]
        if focus:
            queries.insert(0, f"{college_name} {focus} reddit")

        headers = {"User-Agent": settings.user_agent}
        posts: list[dict] = []
        seen: set[str] = set()

        async with httpx.AsyncClient(
            timeout=settings.request_timeout_seconds,
            headers=headers,
            follow_redirects=True,
        ) as client:
            subreddit_results = await self._find_candidate_subreddits(client, college_name)
            for subreddit in subreddit_results[:2]:
                subreddit_posts = await self._fetch_subreddit_posts(client, subreddit, college_name)
                for post in subreddit_posts:
                    if post["url"] not in seen:
                        seen.add(post["url"])
                        posts.append(post)

            for query in queries:
                response = await client.get(
                    "https://www.reddit.com/search.json",
                    params={"q": query, "sort": "relevance", "t": "year", "limit": settings.reddit_limit},
                )
                response.raise_for_status()
                payload = response.json()
                for child in payload.get("data", {}).get("children", []):
                    post = self._map_post(child.get("data", {}))
                    if post and post["url"] not in seen:
                        seen.add(post["url"])
                        posts.append(post)

        return posts[: settings.reddit_limit]

    async def _find_candidate_subreddits(
        self, client: httpx.AsyncClient, college_name: str
    ) -> list[str]:
        response = await client.get(
            "https://www.reddit.com/subreddits/search.json",
            params={"q": college_name, "limit": 5},
        )
        response.raise_for_status()
        payload = response.json()
        results: list[str] = []
        for child in payload.get("data", {}).get("children", []):
            subreddit = child.get("data", {}).get("display_name_prefixed")
            if subreddit:
                results.append(subreddit)
        return results

    async def _fetch_subreddit_posts(
        self, client: httpx.AsyncClient, subreddit: str, college_name: str
    ) -> list[dict]:
        response = await client.get(
            f"https://www.reddit.com/{subreddit}/search.json",
            params={"q": college_name, "restrict_sr": 1, "sort": "new", "limit": 5},
        )
        response.raise_for_status()
        payload = response.json()
        results: list[dict] = []
        for child in payload.get("data", {}).get("children", []):
            post = self._map_post(child.get("data", {}))
            if post:
                results.append(post)
        return results

    def _map_post(self, data: dict) -> dict | None:
        permalink = data.get("permalink")
        title = data.get("title")
        if not permalink or not title:
            return None

        comments = []
        for comment in data.get("selftext", "").splitlines():
            cleaned = comment.strip()
            if cleaned:
                comments.append(cleaned)
        return {
            "source_id": data.get("id", permalink),
            "title": title,
            "subreddit": data.get("subreddit_name_prefixed", "r/unknown"),
            "url": f"https://www.reddit.com{permalink}",
            "post_date": datetime.fromtimestamp(
                data.get("created_utc", 0), tz=timezone.utc
            )
            if data.get("created_utc")
            else None,
            "text": "\n".join(filter(None, [data.get("title", ""), data.get("selftext", "")])),
            "top_comments": comments[:5],
            "score": data.get("score", 0),
            "num_comments": data.get("num_comments", 0),
        }
