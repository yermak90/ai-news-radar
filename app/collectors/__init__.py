from app.collectors.arxiv import ArxivCollector
from app.collectors.base import BaseCollector, CollectedItem
from app.collectors.github import GitHubReleasesCollector
from app.collectors.hackernews import HackerNewsCollector
from app.collectors.rss import RSSCollector
from app.models.enums import CollectionMethod
from app.models.source import Source

_RSS_COLLECTOR = RSSCollector()
_GITHUB_COLLECTOR = GitHubReleasesCollector()
_HACKERNEWS_COLLECTOR = HackerNewsCollector()
_ARXIV_COLLECTOR = ArxivCollector()


def get_collector(source: Source) -> BaseCollector:
    """Resolve the collector implementation for a source.

    RSS/ATOM/GITHUB map 1:1 to a collector. CollectionMethod.API covers a
    couple of source-specific public APIs (Hacker News, arXiv) that don't
    share a common request shape, so those are dispatched by source name.
    """
    method = source.collection_method
    if method in (CollectionMethod.RSS, CollectionMethod.ATOM):
        return _RSS_COLLECTOR
    if method == CollectionMethod.GITHUB:
        return _GITHUB_COLLECTOR
    if method == CollectionMethod.API:
        name = source.name.lower()
        if "hacker news" in name or "hackernews" in name:
            return _HACKERNEWS_COLLECTOR
        if "arxiv" in name:
            return _ARXIV_COLLECTOR
        raise ValueError(f"No API collector implementation registered for source {source.name!r}")
    raise ValueError(f"No collector implementation registered for {method}")


__all__ = [
    "ArxivCollector",
    "BaseCollector",
    "CollectedItem",
    "GitHubReleasesCollector",
    "HackerNewsCollector",
    "RSSCollector",
    "get_collector",
]
