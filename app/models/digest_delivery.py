from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.enums import DigestStatus


class DigestDelivery(Base):
    """Tracks daily digest sends so a user isn't auto-sent the same digest twice (PRD section 48)."""

    __tablename__ = "digest_deliveries"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    digest_date: Mapped[date] = mapped_column(Date, nullable=False, index=True)
    sent_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[DigestStatus] = mapped_column(Enum(DigestStatus, native_enum=False), nullable=False)
