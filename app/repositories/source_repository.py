from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import CollectionMethod, SourceType
from app.models.source import Source


class SourceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def list_enabled(self) -> list[Source]:
        result = await self.session.execute(select(Source).where(Source.enabled.is_(True)))
        return list(result.scalars().all())

    async def get_by_name(self, name: str) -> Source | None:
        result = await self.session.execute(select(Source).where(Source.name == name))
        return result.scalar_one_or_none()

    async def upsert(
        self,
        *,
        name: str,
        type: SourceType,
        url: str,
        feed_url: str | None,
        priority: int,
        collection_method: CollectionMethod,
        category_hint: str | None = None,
        enabled: bool = True,
    ) -> Source:
        source = await self.get_by_name(name)
        if source is not None:
            source.type = type
            source.url = url
            source.feed_url = feed_url
            source.priority = priority
            source.collection_method = collection_method
            source.category_hint = category_hint
            source.enabled = enabled
            return source

        source = Source(
            name=name,
            type=type,
            url=url,
            feed_url=feed_url,
            priority=priority,
            collection_method=collection_method,
            category_hint=category_hint,
            enabled=enabled,
        )
        self.session.add(source)
        await self.session.flush()
        return source

    async def mark_checked(self, source: Source, checked_at: datetime) -> None:
        source.last_checked_at = checked_at
