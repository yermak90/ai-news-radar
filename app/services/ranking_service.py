"""Final-score ranking and TOP3 diversity selection (PRD sections 53-54)."""

from dataclasses import dataclass

from app.models.news_item import NewsItem

# Weights are isolated here (not hardcoded across the pipeline) so the
# formula can be tuned without touching collection/analysis code.
DEFAULT_WEIGHTS: dict[str, float] = {
    "practical_value": 1.0,
    "novelty": 1.0,
    "technical_significance": 1.0,
    "personal_relevance": 1.0,
    "source_reliability": 1.0,
    "enterprise_relevance": 1.0,
}


def final_score(item: NewsItem, weights: dict[str, float] = DEFAULT_WEIGHTS) -> float:
    return (
        item.practical_value_score * weights["practical_value"]
        + item.novelty_score * weights["novelty"]
        + item.technical_significance_score * weights["technical_significance"]
        + item.personal_relevance_score * weights["personal_relevance"]
        + item.source_reliability_score * weights["source_reliability"]
        + item.enterprise_relevance_score * weights["enterprise_relevance"]
    )


@dataclass
class RankedNewsItem:
    item: NewsItem
    score: float


def rank(items: list[NewsItem], weights: dict[str, float] = DEFAULT_WEIGHTS) -> list[RankedNewsItem]:
    ranked = [RankedNewsItem(item=item, score=final_score(item, weights)) for item in items]
    return sorted(ranked, key=lambda r: r.score, reverse=True)


def select_top(
    items: list[NewsItem], *, count: int = 3, weights: dict[str, float] = DEFAULT_WEIGHTS
) -> list[NewsItem]:
    """Pick the top N items while avoiding near-duplicate picks (PRD section 54).

    Diversity rule: prefer not to pick two items that share every category
    (i.e. cover the same ground) before every distinct "theme" has had a
    turn. This is a simple greedy pass, not a full diversity-optimization
    algorithm — sufficient for a handful of picks in a daily digest.
    """
    ranked = rank(items, weights)

    picked: list[RankedNewsItem] = []
    used_category_sets: list[frozenset] = []

    for candidate in ranked:
        if len(picked) >= count:
            break
        candidate_categories = frozenset(c.value for c in candidate.item.category_values)
        if candidate_categories in used_category_sets:
            continue
        picked.append(candidate)
        used_category_sets.append(candidate_categories)

    if len(picked) < count:
        picked_ids = {p.item.id for p in picked}
        for candidate in ranked:
            if len(picked) >= count:
                break
            if candidate.item.id not in picked_ids:
                picked.append(candidate)

    return [p.item for p in picked[:count]]
