import logging
from calendar import timegm
from datetime import UTC, datetime
from time import struct_time

import feedparser
import httpx

from app.collectors.base import HTTP_TIMEOUT_SECONDS, BaseCollector, CollectedItem
from app.models.source import Source

logger = logging.getLogger(__name__)

MAX_FEED_BYTES = 5_000_000  # bound downloaded feed size (PRD section 50)


def _struct_time_to_utc(value: struct_time | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromtimestamp(timegm(value), tz=UTC)


class RSSCollector(BaseCollector):
    """Handles both RSS and Atom feeds (feedparser auto-detects the format)."""

    async def collect(self, source: Source) -> list[CollectedItem]:
        feed_url = source.feed_url or source.url
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS, follow_redirects=True) as client:
            response = await client.get(
                feed_url, headers={"User-Agent": "ai-news-radar/0.1 (+https://github.com)"}
            )
            response.raise_for_status()
            content = response.content[:MAX_FEED_BYTES]

        parsed = feedparser.parse(content)
        if parsed.bozo and not parsed.entries:
            raise ValueError(f"Unparsable feed at {feed_url}: {parsed.bozo_exception}")

        items: list[CollectedItem] = []
        for entry in parsed.entries:
            try:
                items.append(self._entry_to_item(entry))
            except Exception:  # noqa: BLE001 - one bad entry must not drop the feed
                logger.warning("Skipping malformed feed entry from %s", source.name, exc_info=True)
        return items

    @staticmethod
    def _entry_to_item(entry: feedparser.FeedParserDict) -> CollectedItem:
        title = (entry.get("title") or "").strip()
        link = (entry.get("link") or "").strip()
        if not title or not link:
            raise ValueError("Feed entry missing title/link")

        published = _struct_time_to_utc(entry.get("published_parsed") or entry.get("updated_parsed"))
        author = entry.get("author")
        summary = entry.get("summary") or entry.get("description") or ""

        html = None
        content_list = entry.get("content")
        if content_list:
            html = content_list[0].get("value")

        return CollectedItem(
            title=title,
            url=link,
            author=author,
            published_at=published,
            summary_text=summary,
            html=html,
        )
