from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.enums import ProcessingStatus
from app.models.mixins import TimestampMixin


class RawItem(TimestampMixin, Base):
    """A single collected item before dedup/analysis (PRD section 11)."""

    __tablename__ = "raw_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), nullable=False, index=True)
    source_name: Mapped[str] = mapped_column(String(255), nullable=False)
    source_type: Mapped[str] = mapped_column(String(32), nullable=False)
    source_priority: Mapped[int] = mapped_column(Integer, nullable=False)

    title: Mapped[str] = mapped_column(String(1024), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    canonical_url: Mapped[str] = mapped_column(String(2048), nullable=False, index=True)
    author: Mapped[str | None] = mapped_column(String(255), nullable=True)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    discovered_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_html: Mapped[str | None] = mapped_column(Text, nullable=True)
    language: Mapped[str | None] = mapped_column(String(16), nullable=True)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)

    status: Mapped[ProcessingStatus] = mapped_column(
        Enum(ProcessingStatus, native_enum=False), default=ProcessingStatus.NEW, nullable=False, index=True
    )
    failure_reason: Mapped[str | None] = mapped_column(String(1024), nullable=True)

    cluster_id: Mapped[int | None] = mapped_column(
        ForeignKey("news_clusters.id"), nullable=True, index=True
    )

    cluster = relationship("NewsCluster", back_populates="raw_items")

    def __repr__(self) -> str:  # pragma: no cover
        return f"RawItem(id={self.id}, title={self.title[:40]!r})"
