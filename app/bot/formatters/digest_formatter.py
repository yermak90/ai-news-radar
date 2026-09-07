from app.bot.formatters.news_card_formatter import format_news_card
from app.bot.formatters.text import chunk_messages, escape_html
from app.models.news_item import NewsItem
from app.services.digest_service import Digest

EMPTY_DIGEST_TEXT = (
    "🗞 <b>AI News Radar — Daily Digest</b>\n\n"
    "Сегодня нет материалов, которые прошли порог значимости для дайджеста. "
    "Загляните позже или используйте /refresh."
)


def format_digest(digest: Digest) -> list[str]:
    """Renders a Digest into one or more Telegram-ready HTML messages (PRD sections 23-27)."""
    if digest.is_empty:
        return [EMPTY_DIGEST_TEXT]

    blocks: list[str] = ["🗞 <b>AI News Radar — Daily Digest</b>"]

    if digest.top3:
        blocks.append("<b>🏆 TOP 3</b>")
        for i, item in enumerate(digest.top3, start=1):
            blocks.append(format_news_card(item, rank=i))

    for section in digest.sections:
        blocks.append(f"<b>📚 {escape_html(section.display_name)}</b>")
        for item in section.items:
            blocks.append(format_news_card(item))

    if digest.worth_testing:
        blocks.append("<b>✅ Worth Testing</b>")
        for i, item in enumerate(digest.worth_testing, start=1):
            lines = [
                f"<b>{i}. {escape_html(item.title)}</b>",
                "Почему стоит попробовать:",
                escape_html(item.why_it_matters),
            ]
            if item.estimated_test_effort:
                lines.append(f"Test effort: ~{escape_html(item.estimated_test_effort)}")
            if item.suggested_test:
                lines.append(f"Suggested test: {escape_html(item.suggested_test)}")
            blocks.append("\n".join(lines))

    return chunk_messages(blocks)


def format_news_list(items: list[NewsItem], *, title: str) -> list[str]:
    """Renders a flat list of news items (used by /stt, /meeting, /top, /testing, etc.)."""
    if not items:
        return [f"<b>{escape_html(title)}</b>\n\nПока нет материалов в этой категории."]

    blocks = [f"<b>{escape_html(title)}</b>"]
    blocks += [format_news_card(item) for item in items]
    return chunk_messages(blocks)
