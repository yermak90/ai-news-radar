from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime

from app.models.source import Source

HTTP_TIMEOUT_SECONDS = 20.0


@dataclass(frozen=True)
class CollectedItem:
    """One item fetched from a source, before it becomes a RawItem row."""

    title: str
    url: str
    author: str | None
    published_at: datetime | None
    summary_text: str
    html: str | None = None


class BaseCollector(ABC):
    """One implementation per collection method (PRD section 33: RSS/ATOM/API/GITHUB/HTML/OTHER).

    A collector must not raise on a single malformed entry — it should skip
    it and keep going, so one bad item doesn't drop the whole source.
    """

    @abstractmethod
    async def collect(self, source: Source) -> list[CollectedItem]:
        """Fetch and parse a source's feed/API. May raise on total source failure
        (network error, non-2xx, unparsable payload) — callers must catch and
        continue on to the next source (PRD section 46)."""
