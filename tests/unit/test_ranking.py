from app.models.enums import Category
from app.services.ranking_service import final_score, rank, select_top
from tests.helpers import make_news_item


class TestFinalScore:
    def test_sums_all_score_components(self):
        item = make_news_item(
            id=1,
            novelty=1,
            practical_value=2,
            technical_significance=3,
            personal_relevance=4,
            source_reliability=5,
            enterprise_relevance=1,
        )
        assert final_score(item) == 1 + 2 + 3 + 4 + 5 + 1

    def test_higher_scores_produce_higher_final_score(self):
        low = make_news_item(id=1, novelty=1, practical_value=1)
        high = make_news_item(id=2, novelty=5, practical_value=5)
        assert final_score(high) > final_score(low)


class TestRank:
    def test_orders_by_score_descending(self):
        low = make_news_item(id=1, novelty=1, practical_value=1, technical_significance=1)
        high = make_news_item(id=2, novelty=5, practical_value=5, technical_significance=5)
        mid = make_news_item(id=3, novelty=3, practical_value=3, technical_significance=3)

        ranked = rank([low, high, mid])
        assert [r.item.id for r in ranked] == [2, 3, 1]


class TestSelectTop:
    def test_returns_requested_count(self):
        items = [make_news_item(id=i, novelty=i) for i in range(1, 6)]
        top = select_top(items, count=3)
        assert len(top) == 3

    def test_picks_highest_scoring_items_first(self):
        items = [make_news_item(id=i, novelty=i, categories=[Category.OTHER]) for i in range(1, 6)]
        top = select_top(items, count=1)
        assert top[0].id == 5

    def test_diversity_prefers_different_category_sets(self):
        stt_high = make_news_item(id=1, novelty=5, categories=[Category.STT])
        stt_low = make_news_item(id=2, novelty=4, categories=[Category.STT])
        agents = make_news_item(id=3, novelty=3, categories=[Category.AI_AGENTS])

        top = select_top([stt_high, stt_low, agents], count=2)
        top_ids = {item.id for item in top}
        # Should prefer covering two distinct themes (STT + Agents) over two STT items.
        assert top_ids == {1, 3}

    def test_falls_back_to_score_order_when_categories_run_out(self):
        items = [
            make_news_item(id=1, novelty=5, categories=[Category.STT]),
            make_news_item(id=2, novelty=4, categories=[Category.AI_AGENTS]),
            make_news_item(id=3, novelty=3, categories=[Category.PROGRAMMING]),
            make_news_item(id=4, novelty=2, categories=[Category.STT]),
        ]
        top = select_top(items, count=4)
        assert len(top) == 4
