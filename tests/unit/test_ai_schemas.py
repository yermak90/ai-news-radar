import pytest
from pydantic import ValidationError

from app.ai.schemas import AIAnalysisResult

VALID_PAYLOAD = {
    "title": "New multilingual STT model",
    "summary": "A new open-source STT model was released.",
    "categories": ["STT", "MEETING_INTELLIGENCE"],
    "why_it_matters": "It improves transcription quality for multiple languages.",
    "practical_use": "Can be benchmarked against the current STT pipeline.",
    "risks": ["Preview quality, no independent benchmarks yet."],
    "recommendation": "TEST",
    "priority": 5,
    "scores": {
        "novelty": 4,
        "practical_value": 5,
        "technical_significance": 4,
        "enterprise_relevance": 5,
        "personal_relevance": 5,
        "source_reliability": 5,
    },
    "relevance": {
        "stt": 5,
        "meeting": 5,
        "rag": 0,
        "agents": 0,
        "coding": 0,
        "enterprise": 4,
        "on_prem": 5,
    },
    "estimated_test_effort": "1 hour",
    "suggested_test": "Run benchmark audio through the model.",
}


class TestAIAnalysisResultValidation:
    def test_valid_payload_parses(self):
        result = AIAnalysisResult.model_validate(VALID_PAYLOAD)
        assert result.title == VALID_PAYLOAD["title"]
        assert result.recommendation.value == "TEST"
        assert result.priority == 5

    def test_invalid_recommendation_rejected(self):
        payload = {**VALID_PAYLOAD, "recommendation": "MAYBE"}
        with pytest.raises(ValidationError):
            AIAnalysisResult.model_validate(payload)

    def test_priority_out_of_range_rejected(self):
        payload = {**VALID_PAYLOAD, "priority": 6}
        with pytest.raises(ValidationError):
            AIAnalysisResult.model_validate(payload)

    def test_priority_zero_rejected(self):
        payload = {**VALID_PAYLOAD, "priority": 0}
        with pytest.raises(ValidationError):
            AIAnalysisResult.model_validate(payload)

    def test_invalid_category_rejected(self):
        payload = {**VALID_PAYLOAD, "categories": ["NOT_A_REAL_CATEGORY"]}
        with pytest.raises(ValidationError):
            AIAnalysisResult.model_validate(payload)

    def test_empty_categories_rejected(self):
        payload = {**VALID_PAYLOAD, "categories": []}
        with pytest.raises(ValidationError):
            AIAnalysisResult.model_validate(payload)

    def test_score_out_of_range_rejected(self):
        payload = {**VALID_PAYLOAD, "scores": {**VALID_PAYLOAD["scores"], "novelty": 9}}
        with pytest.raises(ValidationError):
            AIAnalysisResult.model_validate(payload)

    def test_missing_required_field_rejected(self):
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "summary"}
        with pytest.raises(ValidationError):
            AIAnalysisResult.model_validate(payload)

    def test_invalid_test_effort_coerced_to_unknown(self):
        payload = {**VALID_PAYLOAD, "estimated_test_effort": "some random string"}
        result = AIAnalysisResult.model_validate(payload)
        assert result.estimated_test_effort == "unknown"

    def test_duplicate_categories_deduped(self):
        payload = {**VALID_PAYLOAD, "categories": ["STT", "STT", "MEETING_INTELLIGENCE"]}
        result = AIAnalysisResult.model_validate(payload)
        assert result.categories == ["STT", "MEETING_INTELLIGENCE"]
