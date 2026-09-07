from datetime import UTC, datetime

import pytest

from app.ai.provider import MockLLMProvider
from app.models.enums import CollectionMethod, ProcessingStatus, SourceType
from app.models.raw_item import RawItem
from app.models.source import Source
from app.repositories.news_repository import NewsRepository
from app.repositories.raw_item_repository import RawItemRepository
from app.repositories.source_repository import SourceRepository
from app.services.processing_service import extract_and_dedup, run_ai_analysis


async def _make_source(db_session) -> Source:
    repo = SourceRepository(db_session)
    source = await repo.upsert(
        name="Official STT Blog",
        type=SourceType.OFFICIAL,
        url="https://example.com",
        feed_url="https://example.com/feed.xml",
        priority=5,
        collection_method=CollectionMethod.RSS,
    )
    await db_session.commit()
    return source


async def _make_raw_item(db_session, source: Source, **overrides) -> RawItem:
    repo = RawItemRepository(db_session)
    defaults = {
        "source_id": source.id,
        "source_name": source.name,
        "source_type": source.type.value,
        "source_priority": source.priority,
        "title": "New multilingual speech-to-text model released",
        "url": "https://example.com/stt-model",
        "canonical_url": "https://example.com/stt-model",
        "published_at": datetime.now(UTC),
        "discovered_at": datetime.now(UTC),
        "raw_text": "A new open-source speech-to-text (ASR) transcription model was released today.",
        "raw_html": None,
        "content_hash": "hash-1",
        "status": ProcessingStatus.NEW,
    }
    defaults.update(overrides)
    raw_item = RawItem(**defaults)
    await repo.create(raw_item)
    await db_session.commit()
    return raw_item


@pytest.mark.asyncio
class TestProcessingPipeline:
    async def test_relevant_item_flows_through_to_news_item(self, db_session):
        source = await _make_source(db_session)
        await _make_raw_item(db_session, source)

        extraction_stats = await extract_and_dedup(db_session)
        assert extraction_stats.queued_for_ai == 1
        assert extraction_stats.filtered == 0
        assert extraction_stats.duplicates == 0

        analysis_stats = await run_ai_analysis(db_session, MockLLMProvider())
        assert analysis_stats.analyzed == 1
        assert analysis_stats.ai_failed == 0

        raw_item_repo = RawItemRepository(db_session)
        processed = await raw_item_repo.list_by_status(ProcessingStatus.PROCESSED)
        assert len(processed) == 1

        news_repo = NewsRepository(db_session)
        news_item = await news_repo.get_by_cluster_id(processed[0].cluster_id)
        assert news_item is not None
        assert news_item.recommendation is not None
        assert 1 <= news_item.priority <= 5
        assert news_item.category_values  # at least one category assigned

    async def test_irrelevant_item_is_filtered_before_ai(self, db_session):
        source = await _make_source(db_session)
        source.type = SourceType.MEDIA  # non-official sources go through keyword filtering
        await db_session.commit()

        await _make_raw_item(
            db_session,
            source,
            source_type=SourceType.MEDIA.value,
            title="Local sports team wins championship",
            raw_text="The home team won the championship game last night in front of a big crowd.",
        )

        extraction_stats = await extract_and_dedup(db_session)
        assert extraction_stats.filtered == 1
        assert extraction_stats.queued_for_ai == 0

    async def test_duplicate_item_does_not_create_second_news_item(self, db_session):
        source = await _make_source(db_session)
        await _make_raw_item(
            db_session,
            source,
            title="Acme releases new ASR model",
            url="https://example.com/acme-asr",
            canonical_url="https://example.com/acme-asr",
            content_hash="hash-a",
            raw_text="Acme just released a new automatic speech recognition model with diarization.",
        )
        await _make_raw_item(
            db_session,
            source,
            title="acme releases new asr model",  # same normalized title -> duplicate
            url="https://othersite.com/acme-asr-copy",
            canonical_url="https://othersite.com/acme-asr-copy",
            content_hash="hash-b",
            raw_text="Acme just released a new automatic speech recognition model with diarization.",
        )

        await extract_and_dedup(db_session)
        await run_ai_analysis(db_session, MockLLMProvider())

        raw_item_repo = RawItemRepository(db_session)
        duplicates = await raw_item_repo.list_by_status(ProcessingStatus.DUPLICATE)
        assert len(duplicates) == 1

        news_repo = NewsRepository(db_session)
        news_items = await news_repo.list_recent(min_priority=1)
        assert len(news_items) == 1
        assert len(news_items[0].related_sources) == 1
