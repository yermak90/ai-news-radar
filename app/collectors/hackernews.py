import logging
from datetime import UTC, datetime
from urllib.parse import parse_qsl

import httpx

from app.collectors.base import HTTP_TIMEOUT_SECONDS, BaseCollector, CollectedItem
from app.models.source import Source

logger = logging.getLogger(__name__)

ALGOLIA_SEARCH_URL = "https://hn.algolia.com/api/v1/search_by_date"


class HackerNewsCollector(BaseCollector):
    """Uses the public HN Algolia Search API to find recent AI-tagged stories.

    `source.feed_url`, if set, overrides the search query string
    (e.g. "query=AI&tags=story"); otherwise a sensible AI-focused default is used.
    """

    async def collect(self, source: Source) -> list[CollectedItem]:
        params = {"tags": "story", "query": "AI", "hitsPerPage": "30"}
        if source.feed_url:
            params.update(dict(parse_qsl(source.feed_url)))

        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
            response = await client.get(ALGOLIA_SEARCH_URL, params=params)
            response.raise_for_status()
            payload = response.json()

        items: list[CollectedItem] = []
        for hit in payload.get("hits", []):
            try:
                items.append(self._hit_to_item(hit))
            except Exception:
                logger.warning("Skipping malformed HN hit", exc_info=True)
        return items

    @staticmethod
    def _hit_to_item(hit: dict) -> CollectedItem:
        title = hit.get("title")
        url = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
        if not title:
            raise ValueError("HN hit missing title")

        created_at = hit.get("created_at")
        published_at = datetime.fromisoformat(created_at).astimezone(UTC) if created_at else None

        return CollectedItem(
            title=str(title),
            url=str(url),
            author=hit.get("author"),
            published_at=published_at,
            summary_text=hit.get("story_text") or "",
            html=None,
        )
