from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.digest_delivery import DigestDelivery
from app.models.enums import DigestStatus


class DigestRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_delivery(self, user_id: int, digest_date: date) -> DigestDelivery | None:
        result = await self.session.execute(
            select(DigestDelivery)
            .where(DigestDelivery.user_id == user_id)
            .where(DigestDelivery.digest_date == digest_date)
        )
        return result.scalar_one_or_none()

    async def record_delivery(
        self, user_id: int, digest_date: date, sent_at, status: DigestStatus
    ) -> DigestDelivery:
        delivery = DigestDelivery(
            user_id=user_id, digest_date=digest_date, sent_at=sent_at, status=status
        )
        self.session.add(delivery)
        await self.session.flush()
        return delivery
