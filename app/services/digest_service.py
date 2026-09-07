"""Builds the Daily Digest content model (PRD sections 23-25).

Pure business logic — no Telegram/formatting concerns here (that's
app/bot/formatters), so it's directly unit-testable.
"""

from dataclasses import dataclass, field

from app.models.enums import Category, Recommendation
from app.models.news_item import NewsItem
from app.services.ranking_service import select_top

CATEGORY_DISPLAY_NAMES: dict[Category, str] = {
    Category.LLM_MODELS: "LLM & Models",
    Category.PROGRAMMING: "Programming / Vibe Coding",
    Category.STT: "STT & Transcription",
    Category.MEETING_INTELLIGENCE: "Meeting Intelligence",
    Category.AI_AGENTS: "AI Agents",
    Category.DOCUMENTS_RAG: "RAG / Documents",
    Category.ENTERPRISE_AI: "Enterprise AI",
    Category.MULTIMEDIA: "Multimedia",
    Category.OTHER: "Other",
}

CATEGORY_ORDER: list[Category] = [
    Category.LLM_MODELS,
    Category.PROGRAMMING,
    Category.STT,
    Category.MEETING_INTELLIGENCE,
    Category.AI_AGENTS,
    Category.DOCUMENTS_RAG,
    Category.ENTERPRISE_AI,
    Category.MULTIMEDIA,
    Category.OTHER,
]

# PRD section 18: priority 1 is noise and stays out of the main digest.
MIN_DIGEST_PRIORITY = 2
MAX_ADDITIONAL_ITEMS = 10
MAX_WORTH_TESTING = 5


@dataclass
class DigestSection:
    category: Category
    display_name: str
    items: list[NewsItem]


@dataclass
class Digest:
    top3: list[NewsItem] = field(default_factory=list)
    sections: list[DigestSection] = field(default_factory=list)
    worth_testing: list[NewsItem] = field(default_factory=list)
    is_empty: bool = False


def build_digest(news_items: list[NewsItem]) -> Digest:
    eligible = [item for item in news_items if item.priority >= MIN_DIGEST_PRIORITY]
    if not eligible:
        return Digest(is_empty=True)

    top3 = select_top(eligible, count=3)
    top3_ids = {item.id for item in top3}

    remaining = [item for item in eligible if item.id not in top3_ids]
    remaining_sorted = sorted(remaining, key=lambda i: (i.priority, i.novelty_score), reverse=True)
    remaining_sorted = remaining_sorted[:MAX_ADDITIONAL_ITEMS]

    sections: list[DigestSection] = []
    for category in CATEGORY_ORDER:
        items_in_category = [
            item for item in remaining_sorted if category in item.category_values
        ]
        if items_in_category:
            sections.append(
                DigestSection(
                    category=category,
                    display_name=CATEGORY_DISPLAY_NAMES[category],
                    items=items_in_category,
                )
            )

    worth_testing_candidates = [
        item for item in eligible if item.recommendation == Recommendation.TEST
    ]
    worth_testing_candidates.sort(key=lambda i: (i.priority, i.novelty_score), reverse=True)
    worth_testing = worth_testing_candidates[:MAX_WORTH_TESTING]

    return Digest(top3=top3, sections=sections, worth_testing=worth_testing)
