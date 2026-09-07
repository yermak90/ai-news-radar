import difflib

from app.extractors.normalize import normalize_title
from app.models.raw_item import RawItem

TITLE_SIMILARITY_THRESHOLD = 0.88
SEMANTIC_SIMILARITY_THRESHOLD = 0.5

# Official > Research > Community/GitHub > Media, per PRD section 13.2.
_SOURCE_TYPE_RANK = {"OFFICIAL": 4, "RESEARCH": 3, "COMMUNITY": 2, "MEDIA": 1}


def _tokenize(text: str) -> set[str]:
    return {token for token in normalize_title(text).split(" ") if len(token) > 2}


def _jaccard_similarity(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    intersection = len(a & b)
    union = len(a | b)
    return intersection / union if union else 0.0


class Deduplicator:
    """Multi-level duplicate detection (PRD section 13.1).

    Level 1 — exact canonical URL match.
    Level 2 — normalized title match (exact or high fuzzy ratio).
    Level 3 — exact content_hash match.
    Level 4 — lightweight semantic similarity (token Jaccard over title+body)
              used as a cheap stand-in for embeddings, applied only to items
              published within a short time window of each other.
    """

    def find_duplicate(self, candidate: RawItem, existing_items: list[RawItem]) -> RawItem | None:
        candidate_canonical = candidate.canonical_url

        for existing in existing_items:
            if existing.canonical_url == candidate_canonical:
                return existing

        for existing in existing_items:
            if existing.content_hash == candidate.content_hash:
                return existing

        candidate_title_norm = normalize_title(candidate.title)
        for existing in existing_items:
            existing_title_norm = normalize_title(existing.title)
            if not candidate_title_norm or not existing_title_norm:
                continue
            if candidate_title_norm == existing_title_norm:
                return existing
            ratio = difflib.SequenceMatcher(None, candidate_title_norm, existing_title_norm).ratio()
            if ratio >= TITLE_SIMILARITY_THRESHOLD:
                return existing

        candidate_tokens = _tokenize(candidate.title) | _tokenize((candidate.raw_text or "")[:500])
        for existing in existing_items:
            if not self._within_time_window(candidate, existing):
                continue
            existing_tokens = _tokenize(existing.title) | _tokenize((existing.raw_text or "")[:500])
            if _jaccard_similarity(candidate_tokens, existing_tokens) >= SEMANTIC_SIMILARITY_THRESHOLD:
                return existing

        return None

    @staticmethod
    def _within_time_window(a: RawItem, b: RawItem, hours: int = 96) -> bool:
        a_time = a.published_at or a.discovered_at
        b_time = b.published_at or b.discovered_at
        if a_time is None or b_time is None:
            return True
        return abs((a_time - b_time).total_seconds()) <= hours * 3600

    @staticmethod
    def select_primary(items: list[RawItem]) -> RawItem:
        """Official > Research > Community > Media; ties broken by source priority, then earliest."""

        def sort_key(item: RawItem):
            published = item.published_at or item.discovered_at
            return (
                -_SOURCE_TYPE_RANK.get(item.source_type, 0),
                -item.source_priority,
                published,
            )

        return sorted(items, key=sort_key)[0]
