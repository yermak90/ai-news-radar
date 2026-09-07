import logging
from datetime import datetime

import httpx

from app.collectors.base import HTTP_TIMEOUT_SECONDS, BaseCollector, CollectedItem
from app.models.source import Source

logger = logging.getLogger(__name__)


class GitHubReleasesCollector(BaseCollector):
    """Fetches GitHub Releases via the public REST API.

    `source.feed_url` must be a GitHub API releases endpoint, e.g.
    https://api.github.com/repos/huggingface/transformers/releases
    """

    async def collect(self, source: Source) -> list[CollectedItem]:
        api_url = source.feed_url or source.url
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "ai-news-radar/0.1 (+https://github.com)",
        }
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
            response = await client.get(api_url, headers=headers, params={"per_page": 15})
            response.raise_for_status()
            releases = response.json()

        items: list[CollectedItem] = []
        for release in releases:
            try:
                items.append(self._release_to_item(release))
            except Exception:
                logger.warning("Skipping malformed GitHub release from %s", source.name, exc_info=True)
        return items

    @staticmethod
    def _release_to_item(release: dict) -> CollectedItem:
        title = release.get("name") or release.get("tag_name")
        url = release.get("html_url")
        if not title or not url:
            raise ValueError("Release missing name/url")

        published_raw = release.get("published_at") or release.get("created_at")
        published_at = datetime.fromisoformat(published_raw) if published_raw else None

        author = (release.get("author") or {}).get("login")
        body = release.get("body") or ""

        return CollectedItem(
            title=str(title),
            url=str(url),
            author=author,
            published_at=published_at,
            summary_text=body,
            html=None,
        )
