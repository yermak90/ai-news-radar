from datetime import UTC, datetime

from app.deduplication.deduplicator import Deduplicator
from app.extractors.normalize import content_hash, normalize_url
from app.models.raw_item import RawItem


def make_raw_item(
    *,
    id: int,
    title: str,
    url: str,
    source_type: str = "MEDIA",
    source_priority: int = 3,
    published_at: datetime | None = None,
    text: str = "",
) -> RawItem:
    return RawItem(
        id=id,
        source_id=1,
        source_name="Test Source",
        source_type=source_type,
        source_priority=source_priority,
        title=title,
        url=url,
        canonical_url=normalize_url(url),
        published_at=published_at or datetime(2026, 1, 1, tzinfo=UTC),
        discovered_at=datetime(2026, 1, 1, tzinfo=UTC),
        raw_text=text,
        raw_html=None,
        content_hash=content_hash(title, text),
        cluster_id=10,
    )


class TestExactDeduplication:
    def test_exact_canonical_url_match_is_a_duplicate(self):
        existing = make_raw_item(id=1, title="A new model", url="https://a.com/post?utm_source=x")
        candidate = make_raw_item(id=2, title="Completely different title", url="https://a.com/post")

        duplicate = Deduplicator().find_duplicate(candidate, [existing])
        assert duplicate is existing

    def test_exact_content_hash_match_is_a_duplicate(self):
        existing = make_raw_item(id=1, title="Same Title", url="https://a.com/1", text="same body")
        candidate = make_raw_item(id=2, title="Same Title", url="https://b.com/2", text="same body")

        duplicate = Deduplicator().find_duplicate(candidate, [existing])
        assert duplicate is existing

    def test_normalized_title_match_is_a_duplicate(self):
        existing = make_raw_item(id=1, title="OpenAI releases GPT-5!", url="https://a.com/1")
        candidate = make_raw_item(id=2, title="openai releases gpt 5", url="https://b.com/2")

        duplicate = Deduplicator().find_duplicate(candidate, [existing])
        assert duplicate is existing

    def test_unrelated_items_are_not_duplicates(self):
        existing = make_raw_item(
            id=1,
            title="New STT model released by ExampleCorp",
            url="https://a.com/1",
            text="Speech to text model with diarization support.",
        )
        candidate = make_raw_item(
            id=2,
            title="Quarterly earnings report published",
            url="https://b.com/2",
            text="Financial results for the quarter.",
        )

        duplicate = Deduplicator().find_duplicate(candidate, [existing])
        assert duplicate is None

    def test_no_existing_items_returns_none(self):
        candidate = make_raw_item(id=1, title="Anything", url="https://a.com/1")
        assert Deduplicator().find_duplicate(candidate, []) is None


class TestPrimarySourceSelection:
    def test_official_beats_media(self):
        official = make_raw_item(id=1, title="T", url="https://a.com/1", source_type="OFFICIAL")
        media = make_raw_item(id=2, title="T", url="https://b.com/2", source_type="MEDIA")

        primary = Deduplicator.select_primary([media, official])
        assert primary is official

    def test_research_beats_community(self):
        research = make_raw_item(id=1, title="T", url="https://a.com/1", source_type="RESEARCH")
        community = make_raw_item(id=2, title="T", url="https://b.com/2", source_type="COMMUNITY")

        primary = Deduplicator.select_primary([community, research])
        assert primary is research

    def test_ties_broken_by_source_priority(self):
        low_priority = make_raw_item(
            id=1, title="T", url="https://a.com/1", source_type="OFFICIAL", source_priority=3
        )
        high_priority = make_raw_item(
            id=2, title="T", url="https://b.com/2", source_type="OFFICIAL", source_priority=5
        )

        primary = Deduplicator.select_primary([low_priority, high_priority])
        assert primary is high_priority
