from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.session import Base
from app.models.enums import CollectionMethod, SourceType
from app.models.mixins import TimestampMixin


class Source(TimestampMixin, Base):
    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[SourceType] = mapped_column(Enum(SourceType, native_enum=False), nullable=False)
    url: Mapped[str] = mapped_column(String(1024), nullable=False)
    feed_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    # Reliability / priority score, 1 (unknown) - 5 (official), per PRD section 52.
    priority: Mapped[int] = mapped_column(Integer, default=3, nullable=False)
    collection_method: Mapped[CollectionMethod] = mapped_column(
        Enum(CollectionMethod, native_enum=False), nullable=False
    )
    category_hint: Mapped[str | None] = mapped_column(String(64), nullable=True)
    last_checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:  # pragma: no cover
        return f"Source(id={self.id}, name={self.name!r})"
