from datetime import UTC, datetime

from app.models.enums import Category, Recommendation
from app.models.news_item import CategoryLink, NewsItem


def make_news_item(
    *,
    id: int = 1,
    title: str = "Test News",
    categories: list[Category] | None = None,
    priority: int = 3,
    recommendation: Recommendation = Recommendation.WATCH,
    novelty: int = 3,
    practical_value: int = 3,
    technical_significance: int = 3,
    personal_relevance: int = 3,
    source_reliability: int = 3,
    enterprise_relevance: int = 3,
    estimated_test_effort: str | None = None,
    suggested_test: str | None = None,
) -> NewsItem:
    """Builds a transient (non-persisted) NewsItem for pure unit tests."""
    item = NewsItem(
        id=id,
        cluster_id=id,
        title=title,
        summary=f"Summary of {title}",
        why_it_matters="It matters because it's a test.",
        practical_use="Use it in tests.",
        risks=[],
        recommendation=recommendation,
        priority=priority,
        novelty_score=novelty,
        practical_value_score=practical_value,
        technical_significance_score=technical_significance,
        enterprise_relevance_score=enterprise_relevance,
        personal_relevance_score=personal_relevance,
        source_reliability_score=source_reliability,
        stt_relevance=0,
        meeting_relevance=0,
        rag_relevance=0,
        agent_relevance=0,
        coding_relevance=0,
        on_prem_relevance=0,
        estimated_test_effort=estimated_test_effort,
        suggested_test=suggested_test,
        primary_url="https://example.com/news",
        primary_source="Example Source",
        published_at=datetime.now(UTC),
        processed_at=datetime.now(UTC),
    )
    for category in categories or [Category.OTHER]:
        item.categories.append(CategoryLink(news_item_id=id, category=category))
    return item
