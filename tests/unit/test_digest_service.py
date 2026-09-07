from app.models.enums import Category, Recommendation
from app.services.digest_service import MIN_DIGEST_PRIORITY, build_digest
from tests.helpers import make_news_item


class TestBuildDigest:
    def test_empty_when_no_items(self):
        digest = build_digest([])
        assert digest.is_empty is True

    def test_priority_1_excluded_from_digest(self):
        assert MIN_DIGEST_PRIORITY == 2
        noise = make_news_item(id=1, priority=1)
        digest = build_digest([noise])
        assert digest.is_empty is True

    def test_top3_populated_and_excluded_from_sections(self):
        items = [
            make_news_item(id=i, priority=5, novelty=i, categories=[Category.STT])
            for i in range(1, 4)
        ]
        digest = build_digest(items)
        assert len(digest.top3) == 3

        section_item_ids = {item.id for section in digest.sections for item in section.items}
        top3_ids = {item.id for item in digest.top3}
        assert section_item_ids.isdisjoint(top3_ids)

    def test_category_filtering_groups_items_by_category(self):
        stt_item = make_news_item(id=1, priority=3, categories=[Category.STT])
        agents_item = make_news_item(id=2, priority=3, categories=[Category.AI_AGENTS])
        # Add a third to avoid both landing in top3 leaving no sections
        filler = make_news_item(id=3, priority=2, categories=[Category.PROGRAMMING])

        digest = build_digest([stt_item, agents_item, filler])

        section_by_category = {section.category: section for section in digest.sections}
        all_ids_in_sections = {i.id for s in digest.sections for i in s.items}
        all_top3_ids = {i.id for i in digest.top3}
        # Every input item lands either in TOP3 or in its matching category section.
        assert all_ids_in_sections | all_top3_ids == {1, 2, 3}
        for category, section in section_by_category.items():
            for item in section.items:
                assert category in item.category_values

    def test_worth_testing_only_includes_test_recommendation(self):
        test_item = make_news_item(id=1, priority=4, recommendation=Recommendation.TEST)
        watch_item = make_news_item(id=2, priority=4, recommendation=Recommendation.WATCH)
        skip_item = make_news_item(id=3, priority=2, recommendation=Recommendation.SKIP)

        digest = build_digest([test_item, watch_item, skip_item])
        assert [item.id for item in digest.worth_testing] == [1]

    def test_worth_testing_capped_at_five(self):
        items = [
            make_news_item(id=i, priority=3, novelty=i, recommendation=Recommendation.TEST)
            for i in range(1, 8)
        ]
        digest = build_digest(items)
        assert len(digest.worth_testing) == 5
