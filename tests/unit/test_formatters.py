from app.bot.formatters.digest_formatter import format_digest, format_news_list
from app.bot.formatters.news_card_formatter import format_news_card
from app.bot.formatters.text import TELEGRAM_MESSAGE_LIMIT, chunk_messages, escape_html
from app.models.enums import Category, Recommendation
from app.services.digest_service import build_digest
from tests.helpers import make_news_item


class TestEscapeHtml:
    def test_escapes_angle_brackets_and_ampersand(self):
        assert escape_html("<script>a & b</script>") == "&lt;script&gt;a &amp; b&lt;/script&gt;"


class TestChunkMessages:
    def test_single_small_block_stays_one_message(self):
        assert chunk_messages(["hello"]) == ["hello"]

    def test_splits_when_exceeding_limit(self):
        big_block = "x" * (TELEGRAM_MESSAGE_LIMIT - 100)
        messages = chunk_messages([big_block, big_block, big_block])
        assert len(messages) > 1
        for message in messages:
            assert len(message) <= TELEGRAM_MESSAGE_LIMIT

    def test_no_message_exceeds_telegram_limit(self):
        blocks = [f"block {i} " + "y" * 500 for i in range(20)]
        for message in chunk_messages(blocks):
            assert len(message) <= TELEGRAM_MESSAGE_LIMIT


class TestFormatNewsCard:
    def test_includes_title_priority_and_recommendation(self):
        item = make_news_item(id=1, title="New Model", priority=5, recommendation=Recommendation.TEST)
        card = format_news_card(item)
        assert "New Model" in card
        assert "Priority: 5/5" in card
        assert "TEST" in card

    def test_escapes_html_in_title(self):
        item = make_news_item(id=1, title="<b>Injected</b>")
        card = format_news_card(item)
        assert "<b>Injected</b>" not in card
        assert "&lt;b&gt;Injected&lt;/b&gt;" in card


class TestFormatDigest:
    def test_empty_digest_has_message(self):
        digest = build_digest([])
        messages = format_digest(digest)
        assert len(messages) == 1
        assert "AI News Radar" in messages[0]

    def test_full_digest_stays_within_telegram_limits(self):
        items = [
            make_news_item(id=i, priority=4, novelty=i % 5, categories=[Category.STT])
            for i in range(1, 15)
        ]
        digest = build_digest(items)
        messages = format_digest(digest)
        assert len(messages) >= 1
        for message in messages:
            assert len(message) <= TELEGRAM_MESSAGE_LIMIT


class TestFormatNewsList:
    def test_empty_list_shows_placeholder(self):
        messages = format_news_list([], title="STT")
        assert "STT" in messages[0]
        assert "Пока нет" in messages[0]

    def test_nonempty_list_includes_all_items(self):
        items = [make_news_item(id=i, title=f"Item {i}") for i in range(1, 4)]
        messages = format_news_list(items, title="STT")
        combined = "\n".join(messages)
        for i in range(1, 4):
            assert f"Item {i}" in combined
