import logging
from calendar import timegm
from datetime import UTC, datetime
from time import struct_time

import feedparser
import httpx

from app.collectors.base import HTTP_TIMEOUT_SECONDS, BaseCollector, CollectedItem
from app.models.source import Source

logger = logging.getLogger(__name__)

ARXIV_API_URL = "https://export.arxiv.org/api/query"
DEFAULT_QUERY = "cat:cs.CL+OR+cat:cs.AI+OR+cat:cs.LG"


def _struct_time_to_utc(value: struct_time | None) -> datetime | None:
    if value is None:
        return None
    return datetime.fromtimestamp(timegm(value), tz=UTC)


class ArxivCollector(BaseCollector):
    """arXiv API returns an Atom feed, so it's parsed with feedparser too.

    `source.feed_url`, if set, overrides the search_query parameter.
    """

    async def collect(self, source: Source) -> list[CollectedItem]:
        search_query = source.feed_url or DEFAULT_QUERY
        params = {
            "search_query": search_query,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "max_results": "25",
        }
        async with httpx.AsyncClient(timeout=HTTP_TIMEOUT_SECONDS) as client:
            response = await client.get(ARXIV_API_URL, params=params)
            response.raise_for_status()
            content = response.content

        parsed = feedparser.parse(content)
        items: list[CollectedItem] = []
        for entry in parsed.entries:
            try:
                items.append(self._entry_to_item(entry))
            except Exception:  # noqa: BLE001
                logger.warning("Skipping malformed arXiv entry", exc_info=True)
        return items

    @staticmethod
    def _entry_to_item(entry: feedparser.FeedParserDict) -> CollectedItem:
        title = (entry.get("title") or "").strip().replace("\n", " ")
        link = (entry.get("link") or "").strip()
        if not title or not link:
            raise ValueError("arXiv entry missing title/link")

        published = _struct_time_to_utc(entry.get("published_parsed"))
        authors = entry.get("authors") or []
        author = ", ".join(a.get("name", "") for a in authors[:3]) if authors else None
        summary = entry.get("summary") or ""

        return CollectedItem(
            title=title,
            url=link,
            author=author or None,
            published_at=published,
            summary_text=summary,
            html=None,
        )
