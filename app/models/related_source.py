from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class RelatedSource(Base):
    """Additional URLs merged into a NewsItem's cluster (PRD section 31)."""

    __tablename__ = "related_sources"

    id: Mapped[int] = mapped_column(primary_key=True)
    news_item_id: Mapped[int] = mapped_column(ForeignKey("news_items.id"), nullable=False, index=True)
    source_name: Mapped[str] = mapped_column(String(255), nullable=False)
    url: Mapped[str] = mapped_column(String(2048), nullable=False)
    title: Mapped[str] = mapped_column(String(1024), nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_priority: Mapped[int] = mapped_column(Integer, nullable=False)

    news_item = relationship("NewsItem", back_populates="related_sources")
