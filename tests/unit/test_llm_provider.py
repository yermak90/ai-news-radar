import json

import httpx
import pytest
import respx

from app.ai.provider import (
    JSON_SCHEMA,
    GeminiProvider,
    LLMResponseError,
    MockLLMProvider,
    NewsAnalysisInput,
    OpenAIProvider,
    _json_schema_for_gemini,
    get_llm_provider,
)
from app.ai.schemas import AIAnalysisResult
from app.config.settings import Settings

SAMPLE_ITEM = NewsAnalysisInput(
    source_name="OpenAI Blog",
    source_type="OFFICIAL",
    url="https://openai.com/blog/example",
    title="New model released",
    content="Details about the new model release.",
)

VALID_RESULT_PAYLOAD = {
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


class TestGeminiProvider:
    @respx.mock
    async def test_analyze_parses_valid_structured_response(self):
        route = respx.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "candidates": [
                        {"content": {"parts": [{"text": json.dumps(VALID_RESULT_PAYLOAD)}]}}
                    ]
                },
            )
        )
        provider = GeminiProvider(api_key="test-key", model="gemini-2.0-flash")

        result = await provider.analyze(SAMPLE_ITEM)

        assert route.called
        assert isinstance(result, AIAnalysisResult)
        assert result.title == VALID_RESULT_PAYLOAD["title"]
        assert result.recommendation.value == "TEST"

    @respx.mock
    async def test_analyze_sends_api_key_and_response_schema(self):
        route = respx.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "candidates": [
                        {"content": {"parts": [{"text": json.dumps(VALID_RESULT_PAYLOAD)}]}}
                    ]
                },
            )
        )
        provider = GeminiProvider(api_key="secret-key", model="gemini-2.0-flash")

        await provider.analyze(SAMPLE_ITEM)

        request = route.calls.last.request
        assert request.url.params["key"] == "secret-key"
        body = json.loads(request.content)
        assert body["generationConfig"]["responseMimeType"] == "application/json"
        assert "responseSchema" in body["generationConfig"]
        assert body["system_instruction"]["parts"][0]["text"]
        # System prompt must always carry the prompt-injection guard (PRD section 51).
        assert "НЕДОВЕРЕННЫМИ ДАННЫМИ" in body["system_instruction"]["parts"][0]["text"]
        # The article content must be passed as untrusted data in the user turn, not the system prompt.
        assert SAMPLE_ITEM.title in body["contents"][0]["parts"][0]["text"]

    @respx.mock
    async def test_analyze_raises_llm_response_error_on_malformed_json(self):
        respx.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        ).mock(
            return_value=httpx.Response(
                200,
                json={"candidates": [{"content": {"parts": [{"text": "not valid json"}]}}]},
            )
        )
        provider = GeminiProvider(api_key="test-key", model="gemini-2.0-flash")

        with pytest.raises(LLMResponseError):
            await provider.analyze(SAMPLE_ITEM)

    @respx.mock
    async def test_analyze_raises_on_http_error(self):
        respx.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        ).mock(return_value=httpx.Response(500, json={"error": "internal"}))
        provider = GeminiProvider(api_key="test-key", model="gemini-2.0-flash")

        with pytest.raises(httpx.HTTPStatusError):
            await provider.analyze(SAMPLE_ITEM)

    @respx.mock
    async def test_analyze_uses_custom_api_base(self):
        route = respx.post(
            "https://custom.example.com/v1beta/models/gemini-2.0-flash:generateContent"
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "candidates": [
                        {"content": {"parts": [{"text": json.dumps(VALID_RESULT_PAYLOAD)}]}}
                    ]
                },
            )
        )
        provider = GeminiProvider(
            api_key="test-key", model="gemini-2.0-flash", api_base="https://custom.example.com/v1beta"
        )

        await provider.analyze(SAMPLE_ITEM)

        assert route.called

    @respx.mock
    async def test_classify_and_score_reuse_the_same_analyze_call(self):
        # classify()/score() are inherited from LLMProvider and both funnel through
        # analyze() — GeminiProvider gets them for free, keeping one paid call per cluster.
        route = respx.post(
            "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent"
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "candidates": [
                        {"content": {"parts": [{"text": json.dumps(VALID_RESULT_PAYLOAD)}]}}
                    ]
                },
            )
        )
        provider = GeminiProvider(api_key="test-key", model="gemini-2.0-flash")

        categories = await provider.classify(SAMPLE_ITEM)
        score_result = await provider.score(SAMPLE_ITEM)

        assert route.call_count == 2
        assert categories == ["STT", "MEETING_INTELLIGENCE"]
        assert isinstance(score_result, AIAnalysisResult)


class TestJsonSchemaForGemini:
    def test_strips_minimum_and_maximum(self):
        converted = _json_schema_for_gemini(JSON_SCHEMA)
        priority = converted["properties"]["priority"]
        assert "minimum" not in priority
        assert "maximum" not in priority
        novelty = converted["properties"]["scores"]["properties"]["novelty"]
        assert "minimum" not in novelty
        assert "maximum" not in novelty

    def test_converts_nullable_union_type(self):
        converted = _json_schema_for_gemini(JSON_SCHEMA)
        test_effort = converted["properties"]["estimated_test_effort"]
        assert test_effort["type"] == "string"
        assert test_effort["nullable"] is True

    def test_preserves_enum_and_required(self):
        converted = _json_schema_for_gemini(JSON_SCHEMA)
        assert converted["properties"]["recommendation"]["enum"] == ["TEST", "WATCH", "SKIP"]
        assert "title" in converted["required"]


class TestGetLLMProvider:
    def test_gemini_provider_selected_with_api_key(self):
        settings = Settings(llm_provider="gemini", llm_api_key="k", llm_model="gemini-2.0-flash")
        provider = get_llm_provider(settings)
        assert isinstance(provider, GeminiProvider)

    def test_gemini_without_api_key_falls_back_to_mock(self):
        settings = Settings(llm_provider="gemini", llm_api_key="", llm_model="gemini-2.0-flash")
        provider = get_llm_provider(settings)
        assert isinstance(provider, MockLLMProvider)

    def test_gemini_provider_case_insensitive(self):
        settings = Settings(llm_provider="GEMINI", llm_api_key="k", llm_model="gemini-2.0-flash")
        provider = get_llm_provider(settings)
        assert isinstance(provider, GeminiProvider)

    def test_openai_provider_still_selected(self):
        settings = Settings(llm_provider="openai", llm_api_key="k", llm_model="gpt-4o-mini")
        provider = get_llm_provider(settings)
        assert isinstance(provider, OpenAIProvider)

    def test_unknown_provider_falls_back_to_mock(self):
        settings = Settings(llm_provider="mock", llm_api_key="", llm_model="")
        provider = get_llm_provider(settings)
        assert isinstance(provider, MockLLMProvider)
