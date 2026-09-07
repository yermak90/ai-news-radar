"""Runs all enabled sources through their collectors and stores new RawItems.

A single source's failure (network error, malformed feed, etc.) is caught
and logged; it never stops collection for the remaining sources (PRD
section 46).
"""

import logging
from dataclasses import dataclass, field
from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.collectors import CollectedItem, get_collector
from app.extractors.normalize import content_hash, normalize_url
from app.models.enums import ProcessingStatus
from app.models.raw_item import RawItem
from app.models.source import Source
from app.repositories.raw_item_repository import RawItemRepository
from app.repositories.source_repository import SourceRepository

logger = logging.getLogger(__name__)


@dataclass
class CollectionStats:
    sources_ok: int = 0
    sources_failed: int = 0
    items_found: int = 0
    items_new: int = 0
    failed_sources: list[str] = field(default_factory=list)


def _collected_item_to_raw_item(item: CollectedItem, source: Source) -> RawItem:
    canonical = normalize_url(item.url)
    return RawItem(
        source_id=source.id,
        source_name=source.name,
        source_type=source.type.value,
        source_priority=source.priority,
        title=item.title[:1024],
        url=item.url[:2048],
        canonical_url=canonical[:2048],
        author=(item.author or None) and item.author[:255],
        published_at=item.published_at,
        discovered_at=datetime.now(UTC),
        raw_text=item.summary_text,
        raw_html=item.html,
        language=None,
        content_hash=content_hash(item.title, item.summary_text),
        status=ProcessingStatus.NEW,
    )


async def collect_from_source(session: AsyncSession, source: Source) -> tuple[int, int]:
    """Returns (items_found, items_new) for a single source."""
    collector = get_collector(source)
    collected_items = await collector.collect(source)

    raw_item_repo = RawItemRepository(session)
    new_count = 0
    for item in collected_items:
        canonical = normalize_url(item.url)
        existing = await raw_item_repo.get_by_canonical_url(canonical)
        if existing is not None:
            continue  # idempotent: already collected in a previous run
        raw_item = _collected_item_to_raw_item(item, source)
        await raw_item_repo.create(raw_item)
        new_count += 1

    return len(collected_items), new_count


async def run_collection(session: AsyncSession) -> CollectionStats:
    stats = CollectionStats()
    source_repo = SourceRepository(session)
    sources = await source_repo.list_enabled()

    logger.info("Starting collection job for %d enabled sources", len(sources))

    for source in sources:
        try:
            found, new = await collect_from_source(session, source)
            stats.items_found += found
            stats.items_new += new
            stats.sources_ok += 1
            await source_repo.mark_checked(source, datetime.now(UTC))
            await session.commit()
            logger.info("Source %r: %d items found, %d new", source.name, found, new)
        except Exception:
            await session.rollback()
            stats.sources_failed += 1
            stats.failed_sources.append(source.name)
            logger.warning("Collection failed for source %r", source.name, exc_info=True)

    logger.info(
        "Collection job finished: %d/%d sources ok, %d items found, %d new",
        stats.sources_ok,
        len(sources),
        stats.items_found,
        stats.items_new,
    )
    return stats
