from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base
from app.models.mixins import TimestampMixin


class NewsCluster(TimestampMixin, Base):
    """Group of raw items that describe the same real-world event (PRD section 13)."""

    __tablename__ = "news_clusters"

    id: Mapped[int] = mapped_column(primary_key=True)

    raw_items = relationship("RawItem", back_populates="cluster")
    news_item = relationship("NewsItem", back_populates="cluster", uselist=False)

    def __repr__(self) -> str:  # pragma: no cover
        return f"NewsCluster(id={self.id})"
