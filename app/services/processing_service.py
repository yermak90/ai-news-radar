"""Extraction -> dedup -> relevance filter -> AI classification/analysis/scoring.

Implements the middle of the pipeline in PRD section 9. Every step is
defensive: one bad raw item is marked FAILED/FILTERED and the loop moves on
(PRD section 34/46) instead of raising and aborting the whole batch.
"""

import logging
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.provider import LLMProvider, NewsAnalysisInput
from app.deduplication.deduplicator import Deduplicator
from app.extractors.content_extractor import extract_content
from app.models.enums import ProcessingStatus
from app.models.news_item import NewsItem
from app.models.raw_item import RawItem
from app.models.related_source import RelatedSource
from app.repositories.news_repository import NewsRepository
from app.repositories.raw_item_repository import RawItemRepository
from app.services.relevance_filter import is_relevant

logger = logging.getLogger(__name__)

DEDUP_LOOKBACK_DAYS = 10


@dataclass
class ProcessingStats:
    extracted: int = 0
    filtered: int = 0
    duplicates: int = 0
    queued_for_ai: int = 0
    analyzed: int = 0
    ai_failed: int = 0


async def extract_and_dedup(session: AsyncSession) -> ProcessingStats:
    """Stage 1: for every NEW raw item — extract content, filter, dedup, cluster."""
    stats = ProcessingStats()
    raw_item_repo = RawItemRepository(session)
    news_repo = NewsRepository(session)
    deduplicator = Deduplicator()

    new_items = await raw_item_repo.list_by_status(ProcessingStatus.NEW)
    since = datetime.now(UTC) - timedelta(days=DEDUP_LOOKBACK_DAYS)
    clustered_items = await raw_item_repo.find_recent_clustered(since)

    for raw_item in new_items:
        try:
            extracted = extract_content(raw_item.raw_html, fallback_text=raw_item.raw_text or "")
            if extracted.text:
                raw_item.raw_text = extracted.text
            if extracted.author and not raw_item.author:
                raw_item.author = extracted.author[:255]
            await raw_item_repo.set_status(raw_item, ProcessingStatus.EXTRACTED)
            stats.extracted += 1

            if not is_relevant(
                title=raw_item.title, text=raw_item.raw_text or "", source_type=raw_item.source_type
            ):
                await raw_item_repo.set_status(raw_item, ProcessingStatus.FILTERED)
                stats.filtered += 1
                continue

            duplicate = deduplicator.find_duplicate(raw_item, clustered_items)
            if duplicate is not None and duplicate.cluster_id is not None:
                raw_item.cluster_id = duplicate.cluster_id
                await raw_item_repo.set_status(raw_item, ProcessingStatus.DUPLICATE)
                stats.duplicates += 1

                existing_news_item = await news_repo.get_by_cluster_id(duplicate.cluster_id)
                if existing_news_item is not None:
                    await news_repo.add_related_source(
                        RelatedSource(
                            news_item_id=existing_news_item.id,
                            source_name=raw_item.source_name,
                            url=raw_item.url,
                            title=raw_item.title,
                            published_at=raw_item.published_at,
                            source_priority=raw_item.source_priority,
                        )
                    )
            else:
                cluster = await news_repo.create_cluster()
                raw_item.cluster_id = cluster.id
                await raw_item_repo.set_status(raw_item, ProcessingStatus.QUEUED_FOR_AI)
                stats.queued_for_ai += 1
                clustered_items.append(raw_item)  # visible to dedup for the rest of this batch

            await session.commit()
        except Exception:
            await session.rollback()
            logger.warning("Failed to extract/dedup raw item %s", raw_item.id, exc_info=True)
            await raw_item_repo.set_status(raw_item, ProcessingStatus.FAILED, reason="extraction/dedup error")
            await session.commit()

    return stats


def _build_news_item(raw_item: RawItem, cluster_id: int, result) -> NewsItem:
    return NewsItem(
        cluster_id=cluster_id,
        title=result.title,
        summary=result.summary,
        why_it_matters=result.why_it_matters,
        practical_use=result.practical_use,
        risks=result.risks,
        recommendation=result.recommendation,
        priority=result.priority,
        novelty_score=result.scores.novelty,
        practical_value_score=result.scores.practical_value,
        technical_significance_score=result.scores.technical_significance,
        enterprise_relevance_score=result.scores.enterprise_relevance,
        personal_relevance_score=result.scores.personal_relevance,
        source_reliability_score=result.scores.source_reliability,
        stt_relevance=result.relevance.stt,
        meeting_relevance=result.relevance.meeting,
        rag_relevance=result.relevance.rag,
        agent_relevance=result.relevance.agents,
        coding_relevance=result.relevance.coding,
        on_prem_relevance=result.relevance.on_prem,
        estimated_test_effort=result.estimated_test_effort,
        suggested_test=result.suggested_test,
        primary_url=raw_item.url,
        primary_source=raw_item.source_name,
        published_at=raw_item.published_at,
        processed_at=datetime.now(UTC),
    )


async def run_ai_analysis(session: AsyncSession, llm_provider: LLMProvider) -> ProcessingStats:
    """Stage 2: run the LLM over every QUEUED_FOR_AI raw item and create its NewsItem."""
    stats = ProcessingStats()
    raw_item_repo = RawItemRepository(session)
    news_repo = NewsRepository(session)

    queued = await raw_item_repo.list_by_status(ProcessingStatus.QUEUED_FOR_AI)

    for raw_item in queued:
        try:
            analysis_input = NewsAnalysisInput(
                source_name=raw_item.source_name,
                source_type=raw_item.source_type,
                url=raw_item.url,
                title=raw_item.title,
                content=raw_item.raw_text or "",
            )
            result = await llm_provider.analyze(analysis_input)

            news_item = _build_news_item(raw_item, raw_item.cluster_id, result)
            await news_repo.create_news_item(news_item, result.categories)

            # Any items merged into this cluster before the primary was analyzed
            # (concurrent duplicates from the same collection batch) become related sources.
            duplicate_siblings = [
                item
                for item in await raw_item_repo.find_recent_clustered(
                    datetime.now(UTC) - timedelta(days=DEDUP_LOOKBACK_DAYS)
                )
                if item.cluster_id == raw_item.cluster_id and item.id != raw_item.id
            ]
            for sibling in duplicate_siblings:
                await news_repo.add_related_source(
                    RelatedSource(
                        news_item_id=news_item.id,
                        source_name=sibling.source_name,
                        url=sibling.url,
                        title=sibling.title,
                        published_at=sibling.published_at,
                        source_priority=sibling.source_priority,
                    )
                )

            await raw_item_repo.set_status(raw_item, ProcessingStatus.PROCESSED)
            stats.analyzed += 1
            await session.commit()
        except Exception as exc:
            await session.rollback()
            logger.warning("AI analysis failed for raw item %s", raw_item.id, exc_info=True)
            await raw_item_repo.set_status(raw_item, ProcessingStatus.FAILED, reason=str(exc)[:500])
            stats.ai_failed += 1
            await session.commit()

    return stats
