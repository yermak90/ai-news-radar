import httpx
import pytest
import respx

from app.collectors.rss import RSSCollector
from app.models.enums import CollectionMethod, SourceType
from app.models.source import Source

SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Example AI Blog</title>
    <item>
      <title>New Model Released</title>
      <link>https://example.com/new-model</link>
      <description>Details about the new model release.</description>
      <pubDate>Mon, 01 Sep 2026 10:00:00 GMT</pubDate>
      <author>jane@example.com</author>
    </item>
    <item>
      <title>Another Update</title>
      <link>https://example.com/another-update</link>
      <description>Some other update.</description>
      <pubDate>Tue, 02 Sep 2026 10:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
"""

MALFORMED_ENTRY_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Example AI Blog</title>
    <item>
      <title>Missing link entry</title>
      <description>No link here.</description>
    </item>
    <item>
      <title>Valid Entry</title>
      <link>https://example.com/valid</link>
      <description>This one is fine.</description>
    </item>
  </channel>
</rss>
"""


def make_source(feed_url: str = "https://example.com/feed.xml") -> Source:
    return Source(
        id=1,
        name="Example Source",
        type=SourceType.OFFICIAL,
        url="https://example.com",
        feed_url=feed_url,
        priority=5,
        collection_method=CollectionMethod.RSS,
    )


class TestRSSCollector:
    @pytest.mark.asyncio
    @respx.mock
    async def test_parses_feed_entries(self):
        respx.get("https://example.com/feed.xml").mock(
            return_value=httpx.Response(200, content=SAMPLE_RSS.encode("utf-8"))
        )

        items = await RSSCollector().collect(make_source())

        assert len(items) == 2
        assert items[0].title == "New Model Released"
        assert items[0].url == "https://example.com/new-model"
        assert items[0].published_at is not None

    @pytest.mark.asyncio
    @respx.mock
    async def test_skips_malformed_entries_without_failing(self):
        respx.get("https://example.com/feed.xml").mock(
            return_value=httpx.Response(200, content=MALFORMED_ENTRY_RSS.encode("utf-8"))
        )

        items = await RSSCollector().collect(make_source())

        assert len(items) == 1
        assert items[0].title == "Valid Entry"

    @pytest.mark.asyncio
    @respx.mock
    async def test_raises_on_http_error(self):
        respx.get("https://example.com/feed.xml").mock(return_value=httpx.Response(500))

        with pytest.raises(httpx.HTTPStatusError):
            await RSSCollector().collect(make_source())
