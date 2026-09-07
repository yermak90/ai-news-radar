from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.enums import Category, Recommendation
from app.models.news_cluster import NewsCluster
from app.models.news_item import CategoryLink, NewsItem
from app.models.related_source import RelatedSource


class NewsRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_cluster(self) -> NewsCluster:
        cluster = NewsCluster()
        self.session.add(cluster)
        await self.session.flush()
        return cluster

    async def create_news_item(self, news_item: NewsItem, categories: list[Category]) -> NewsItem:
        self.session.add(news_item)
        await self.session.flush()
        for category in categories:
            self.session.add(CategoryLink(news_item_id=news_item.id, category=category))
        await self.session.flush()
        return news_item

    async def add_related_source(self, related_source: RelatedSource) -> RelatedSource:
        self.session.add(related_source)
        await self.session.flush()
        return related_source

    def _base_query(self):
        return select(NewsItem).options(
            selectinload(NewsItem.categories), selectinload(NewsItem.related_sources)
        )

    async def get_by_cluster_id(self, cluster_id: int) -> NewsItem | None:
        result = await self.session.execute(self._base_query().where(NewsItem.cluster_id == cluster_id))
        return result.scalar_one_or_none()

    async def list_recent(
        self,
        *,
        since: datetime | None = None,
        min_priority: int = 1,
        limit: int = 200,
    ) -> list[NewsItem]:
        query = self._base_query().where(NewsItem.priority >= min_priority)
        if since is not None:
            query = query.where(NewsItem.processed_at >= since)
        query = query.order_by(NewsItem.processed_at.desc()).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().unique().all())

    async def list_by_category(
        self, category: Category, *, min_priority: int = 1, limit: int = 20
    ) -> list[NewsItem]:
        query = (
            self._base_query()
            .join(CategoryLink, CategoryLink.news_item_id == NewsItem.id)
            .where(CategoryLink.category == category)
            .where(NewsItem.priority >= min_priority)
            .order_by(NewsItem.processed_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().unique().all())

    async def list_by_recommendation(
        self, recommendation: Recommendation, *, limit: int = 20
    ) -> list[NewsItem]:
        query = (
            self._base_query()
            .where(NewsItem.recommendation == recommendation)
            .order_by(NewsItem.processed_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().unique().all())

    async def list_top(self, *, limit: int = 10, min_priority: int = 2) -> list[NewsItem]:
        query = (
            self._base_query()
            .where(NewsItem.priority >= min_priority)
            .order_by(NewsItem.priority.desc(), NewsItem.processed_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().unique().all())
