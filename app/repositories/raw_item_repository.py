from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import ProcessingStatus
from app.models.raw_item import RawItem


class RawItemRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_canonical_url(self, canonical_url: str) -> RawItem | None:
        result = await self.session.execute(
            select(RawItem).where(RawItem.canonical_url == canonical_url)
        )
        return result.scalar_one_or_none()

    async def get_by_content_hash(self, content_hash: str) -> RawItem | None:
        result = await self.session.execute(
            select(RawItem).where(RawItem.content_hash == content_hash)
        )
        return result.scalar_one_or_none()

    async def create(self, raw_item: RawItem) -> RawItem:
        self.session.add(raw_item)
        await self.session.flush()
        return raw_item

    async def list_by_status(self, status: ProcessingStatus, limit: int = 500) -> list[RawItem]:
        result = await self.session.execute(
            select(RawItem).where(RawItem.status == status).order_by(RawItem.discovered_at).limit(limit)
        )
        return list(result.scalars().all())

    async def find_recent_clustered(self, since: datetime, limit: int = 1000) -> list[RawItem]:
        """Raw items already assigned to a cluster, for dedup comparison against new items."""
        result = await self.session.execute(
            select(RawItem)
            .where(RawItem.cluster_id.is_not(None))
            .where(RawItem.discovered_at >= since)
            .order_by(RawItem.discovered_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def set_status(self, raw_item: RawItem, status: ProcessingStatus, *, reason: str | None = None) -> None:
        raw_item.status = status
        if reason is not None:
            raw_item.failure_reason = reason[:1024]
