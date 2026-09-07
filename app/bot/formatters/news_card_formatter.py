from app.bot.formatters.text import escape_html
from app.models.enums import Recommendation
from app.models.news_item import NewsItem

_PRIORITY_EMOJI = {5: "🔥", 4: "⭐", 3: "🔹", 2: "▪️", 1: "·"}
_RECOMMENDATION_EMOJI = {
    Recommendation.TEST: "🧪",
    Recommendation.WATCH: "👀",
    Recommendation.SKIP: "⏭",
}


def format_news_card(item: NewsItem, *, rank: int | None = None) -> str:
    """Renders one NewsItem as an HTML card (PRD section 27)."""
    emoji = _PRIORITY_EMOJI.get(item.priority, "▪️")
    heading = f"{emoji} <b>{escape_html(item.title)}</b>"
    if rank is not None:
        heading = f"<b>{rank}. {escape_html(item.title)}</b> {emoji}"

    categories = ", ".join(c.value for c in item.category_values) or "OTHER"
    rec_emoji = _RECOMMENDATION_EMOJI.get(item.recommendation, "")

    lines = [
        heading,
        "",
        f"Category: <i>{escape_html(categories)}</i>",
        f"Priority: {item.priority}/5",
        f"Recommendation: {rec_emoji} <b>{item.recommendation.value}</b>",
        "",
        f"{escape_html(item.summary)}",
        "",
        "<b>Почему важно:</b>",
        escape_html(item.why_it_matters),
        "",
        "<b>Практическое применение:</b>",
        escape_html(item.practical_use),
    ]

    if item.risks:
        lines += ["", "<b>Риски/ограничения:</b>", escape_html("; ".join(item.risks))]

    if item.recommendation == Recommendation.TEST and item.estimated_test_effort:
        lines += ["", f"Test effort: ~{escape_html(item.estimated_test_effort)}"]
        if item.suggested_test:
            lines += [f"Suggested test: {escape_html(item.suggested_test)}"]

    lines += ["", f'Source: <a href="{escape_html(item.primary_url)}">{escape_html(item.primary_source)}</a>']

    return "\n".join(lines)
