from datetime import UTC, datetime

import pytest

from app.models.enums import (
    Category,
    CollectionMethod,
    ProcessingStatus,
    Recommendation,
    SourceType,
)
from app.models.news_item import NewsItem
from app.models.raw_item import RawItem
from app.repositories.news_repository import NewsRepository
from app.repositories.raw_item_repository import RawItemRepository
from app.repositories.source_repository import SourceRepository
from app.repositories.user_repository import UserRepository


@pytest.mark.asyncio
class TestUserRepository:
    async def test_get_or_create_creates_then_returns_same_user(self, db_session):
        repo = UserRepository(db_session)
        user1 = await repo.get_or_create(
            telegram_user_id=42, telegram_chat_id=42, username="alice", timezone="Asia/Almaty"
        )
        await db_session.commit()

        user2 = await repo.get_or_create(
            telegram_user_id=42, telegram_chat_id=42, username="alice", timezone="Asia/Almaty"
        )
        assert user1.id == user2.id

        fetched = await repo.get_by_telegram_id(42)
        assert fetched is not None
        assert fetched.username == "alice"


@pytest.mark.asyncio
class TestSourceRepository:
    async def test_upsert_is_idempotent(self, db_session):
        repo = SourceRepository(db_session)
        await repo.upsert(
            name="Test Blog",
            type=SourceType.OFFICIAL,
            url="https://example.com",
            feed_url="https://example.com/feed.xml",
            priority=5,
            collection_method=CollectionMethod.RSS,
        )
        await repo.upsert(
            name="Test Blog",
            type=SourceType.OFFICIAL,
            url="https://example.com",
            feed_url="https://example.com/feed.xml",
            priority=4,
            collection_method=CollectionMethod.RSS,
        )
        await db_session.commit()

        sources = await repo.list_enabled()
        assert len(sources) == 1
        assert sources[0].priority == 4


@pytest.mark.asyncio
class TestRawItemRepository:
    async def test_create_and_fetch_by_canonical_url(self, db_session):
        repo = RawItemRepository(db_session)
        raw_item = RawItem(
            source_id=1,
            source_name="Test",
            source_type="OFFICIAL",
            source_priority=5,
            title="Title",
            url="https://example.com/post",
            canonical_url="https://example.com/post",
            published_at=datetime.now(UTC),
            discovered_at=datetime.now(UTC),
            raw_text="body",
            content_hash="abc123",
            status=ProcessingStatus.NEW,
        )
        await repo.create(raw_item)
        await db_session.commit()

        fetched = await repo.get_by_canonical_url("https://example.com/post")
        assert fetched is not None
        assert fetched.title == "Title"

    async def test_list_by_status_only_returns_matching(self, db_session):
        repo = RawItemRepository(db_session)
        for i in range(3):
            await repo.create(
                RawItem(
                    source_id=1,
                    source_name="Test",
                    source_type="OFFICIAL",
                    source_priority=5,
                    title=f"Title {i}",
                    url=f"https://example.com/{i}",
                    canonical_url=f"https://example.com/{i}",
                    discovered_at=datetime.now(UTC),
                    content_hash=f"hash{i}",
                    status=ProcessingStatus.NEW if i < 2 else ProcessingStatus.FILTERED,
                )
            )
        await db_session.commit()

        new_items = await repo.list_by_status(ProcessingStatus.NEW)
        assert len(new_items) == 2


@pytest.mark.asyncio
class TestNewsRepository:
    async def test_create_news_item_with_categories_and_query_by_category(self, db_session):
        news_repo = NewsRepository(db_session)
        cluster = await news_repo.create_cluster()

        news_item = NewsItem(
            cluster_id=cluster.id,
            title="New STT model",
            summary="Summary",
            why_it_matters="Matters",
            practical_use="Use",
            risks=[],
            recommendation=Recommendation.TEST,
            priority=5,
            primary_url="https://example.com/stt",
            primary_source="Example",
            processed_at=datetime.now(UTC),
        )
        await news_repo.create_news_item(news_item, [Category.STT, Category.MEETING_INTELLIGENCE])
        await db_session.commit()

        stt_items = await news_repo.list_by_category(Category.STT)
        assert len(stt_items) == 1
        assert stt_items[0].title == "New STT model"
        assert Category.STT in stt_items[0].category_values

        agents_items = await news_repo.list_by_category(Category.AI_AGENTS)
        assert agents_items == []

    async def test_list_by_recommendation(self, db_session):
        news_repo = NewsRepository(db_session)
        for i, rec in enumerate([Recommendation.TEST, Recommendation.WATCH, Recommendation.SKIP]):
            cluster = await news_repo.create_cluster()
            item = NewsItem(
                cluster_id=cluster.id,
                title=f"Item {i}",
                summary="s",
                why_it_matters="w",
                practical_use="p",
                risks=[],
                recommendation=rec,
                priority=3,
                primary_url=f"https://example.com/{i}",
                primary_source="Example",
                processed_at=datetime.now(UTC),
            )
            await news_repo.create_news_item(item, [Category.OTHER])
        await db_session.commit()

        test_items = await news_repo.list_by_recommendation(Recommendation.TEST)
        assert len(test_items) == 1
        assert test_items[0].recommendation == Recommendation.TEST
