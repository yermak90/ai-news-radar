from datetime import datetime

from sqlalchemy import JSON, DateTime, Enum, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.enums import Category, Recommendation
from app.models.mixins import TimestampMixin


class NewsItem(TimestampMixin, Base):
    """Analyzed, digest-ready news entry (PRD section 30)."""

    __tablename__ = "news_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    cluster_id: Mapped[int] = mapped_column(ForeignKey("news_clusters.id"), unique=True, nullable=False)

    title: Mapped[str] = mapped_column(String(512), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    why_it_matters: Mapped[str] = mapped_column(Text, nullable=False)
    practical_use: Mapped[str] = mapped_column(Text, nullable=False)
    risks: Mapped[list[str]] = mapped_column(JSON, default=list, nullable=False)
    recommendation: Mapped[Recommendation] = mapped_column(
        Enum(Recommendation, native_enum=False), nullable=False
    )
    priority: Mapped[int] = mapped_column(Integer, nullable=False)

    # 0-5 scoring model (PRD section 19)
    novelty_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    practical_value_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    technical_significance_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    enterprise_relevance_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    personal_relevance_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    source_reliability_score: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Special relevance scores (PRD section 20)
    stt_relevance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    meeting_relevance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    rag_relevance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    agent_relevance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    coding_relevance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    on_prem_relevance: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    estimated_test_effort: Mapped[str | None] = mapped_column(String(32), nullable=True)
    suggested_test: Mapped[str | None] = mapped_column(Text, nullable=True)

    primary_url: Mapped[str] = mapped_column(String(2048), nullable=False)
    primary_source: Mapped[str] = mapped_column(String(255), nullable=False)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    cluster = relationship("NewsCluster", back_populates="news_item")
    related_sources = relationship(
        "RelatedSource", back_populates="news_item", cascade="all, delete-orphan"
    )
    categories: Mapped[list["CategoryLink"]] = relationship(
        "CategoryLink", back_populates="news_item", cascade="all, delete-orphan"
    )

    @property
    def category_values(self) -> list[Category]:
        return [link.category for link in self.categories]

    def __repr__(self) -> str:  # pragma: no cover
        return f"NewsItem(id={self.id}, title={self.title[:40]!r})"


class CategoryLink(Base):
    """Explicit mapping-object version of the m2m table above.

    Kept as a proper ORM entity (instead of a plain secondary= table) so
    category filtering can be queried directly without loading NewsItem.
    """

    __tablename__ = "news_item_category_links"

    news_item_id: Mapped[int] = mapped_column(ForeignKey("news_items.id"), primary_key=True)
    category: Mapped[Category] = mapped_column(Enum(Category, native_enum=False), primary_key=True)

    news_item = relationship("NewsItem", back_populates="categories")
