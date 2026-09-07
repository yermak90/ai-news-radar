"""LLM provider abstraction (PRD section 35).

A single `analyze()` call returns classification + analysis + scoring in one
structured response (PRD section 36 already bundles categories/scores/
relevance into one JSON schema) — this keeps one paid LLM call per news
cluster instead of three, per the "Cost Control" principle in section 61.
"""

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass

import httpx
from pydantic import ValidationError
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from app.ai.prompts import SYSTEM_PROMPT, build_user_prompt
from app.ai.schemas import AIAnalysisResult
from app.config.settings import Settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class NewsAnalysisInput:
    source_name: str
    source_type: str
    url: str
    title: str
    content: str


class LLMResponseError(Exception):
    """Raised when the LLM output cannot be parsed into a valid AIAnalysisResult."""


class LLMProvider(ABC):
    @abstractmethod
    async def analyze(self, item: NewsAnalysisInput) -> AIAnalysisResult:
        """Classify, analyze and score a single news cluster."""

    async def classify(self, item: NewsAnalysisInput) -> list[str]:
        result = await self.analyze(item)
        return [c.value for c in result.categories]

    async def score(self, item: NewsAnalysisInput) -> AIAnalysisResult:
        return await self.analyze(item)


JSON_SCHEMA = {
    "type": "object",
    "properties": {
        "title": {"type": "string"},
        "summary": {"type": "string"},
        "categories": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": [
                    "LLM_MODELS",
                    "PROGRAMMING",
                    "STT",
                    "MEETING_INTELLIGENCE",
                    "DOCUMENTS_RAG",
                    "AI_AGENTS",
                    "ENTERPRISE_AI",
                    "MULTIMEDIA",
                    "OTHER",
                ],
            },
        },
        "why_it_matters": {"type": "string"},
        "practical_use": {"type": "string"},
        "risks": {"type": "array", "items": {"type": "string"}},
        "recommendation": {"type": "string", "enum": ["TEST", "WATCH", "SKIP"]},
        "priority": {"type": "integer", "minimum": 1, "maximum": 5},
        "scores": {
            "type": "object",
            "properties": {
                "novelty": {"type": "integer", "minimum": 0, "maximum": 5},
                "practical_value": {"type": "integer", "minimum": 0, "maximum": 5},
                "technical_significance": {"type": "integer", "minimum": 0, "maximum": 5},
                "enterprise_relevance": {"type": "integer", "minimum": 0, "maximum": 5},
                "personal_relevance": {"type": "integer", "minimum": 0, "maximum": 5},
                "source_reliability": {"type": "integer", "minimum": 0, "maximum": 5},
            },
            "required": [
                "novelty",
                "practical_value",
                "technical_significance",
                "enterprise_relevance",
                "personal_relevance",
                "source_reliability",
            ],
        },
        "relevance": {
            "type": "object",
            "properties": {
                "stt": {"type": "integer", "minimum": 0, "maximum": 5},
                "meeting": {"type": "integer", "minimum": 0, "maximum": 5},
                "rag": {"type": "integer", "minimum": 0, "maximum": 5},
                "agents": {"type": "integer", "minimum": 0, "maximum": 5},
                "coding": {"type": "integer", "minimum": 0, "maximum": 5},
                "enterprise": {"type": "integer", "minimum": 0, "maximum": 5},
                "on_prem": {"type": "integer", "minimum": 0, "maximum": 5},
            },
        },
        "estimated_test_effort": {"type": ["string", "null"]},
        "suggested_test": {"type": ["string", "null"]},
    },
    "required": [
        "title",
        "summary",
        "categories",
        "why_it_matters",
        "practical_use",
        "risks",
        "recommendation",
        "priority",
        "scores",
        "relevance",
    ],
}


class OpenAIProvider(LLMProvider):
    """Talks to any OpenAI-compatible chat.completions endpoint.

    Works with api.openai.com by default; point `api_base` at Azure OpenAI,
    a local vLLM/Ollama-compatible server, OpenRouter, etc.
    """

    def __init__(self, api_key: str, model: str, api_base: str = "") -> None:
        self._api_key = api_key
        self._model = model
        self._base_url = (api_base or "https://api.openai.com/v1").rstrip("/")

    @retry(
        reraise=True,
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type((httpx.HTTPError, LLMResponseError)),
    )
    async def analyze(self, item: NewsAnalysisInput) -> AIAnalysisResult:
        user_prompt = build_user_prompt(
            source_name=item.source_name,
            source_type=item.source_type,
            url=item.url,
            title=item.title,
            content=item.content,
        )
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "response_format": {
                "type": "json_schema",
                "json_schema": {"name": "ai_news_analysis", "schema": JSON_SCHEMA, "strict": False},
            },
        }
        headers = {"Authorization": f"Bearer {self._api_key}", "Content-Type": "application/json"}

        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{self._base_url}/chat/completions", json=payload, headers=headers
            )
            response.raise_for_status()
            data = response.json()

        try:
            raw_content = data["choices"][0]["message"]["content"]
            parsed = json.loads(raw_content)
            return AIAnalysisResult.model_validate(parsed)
        except (KeyError, IndexError, json.JSONDecodeError, ValidationError) as exc:
            logger.warning("LLM returned an invalid structured response: %s", exc)
            raise LLMResponseError(str(exc)) from exc


class MockLLMProvider(LLMProvider):
    """Deterministic offline provider — used when LLM_PROVIDER=mock and in tests.

    Applies simple keyword heuristics so the pipeline is exercisable end to
    end without any real API key.
    """

    _KEYWORD_CATEGORIES: dict[str, list[str]] = {
        "STT": ["speech", "transcri", "asr", "voice", "diariz", "распозна"],
        "MEETING_INTELLIGENCE": ["meeting", "protocol", "minutes", "совещан", "протокол"],
        "DOCUMENTS_RAG": ["rag", "retrieval", "embedding", "vector", "document", "ocr"],
        "AI_AGENTS": ["agent", "mcp", "orchestrat", "workflow", "automation"],
        "PROGRAMMING": ["code", "coding", "copilot", "cursor", "developer", "ide"],
        "ENTERPRISE_AI": ["enterprise", "on-prem", "on prem", "compliance", "governance", "security"],
        "MULTIMEDIA": ["image", "video", "avatar", "tts", "voice clon", "animation"],
        "LLM_MODELS": ["model", "llm", "reasoning", "benchmark", "fine-tun", "quantiz"],
    }

    async def analyze(self, item: NewsAnalysisInput) -> AIAnalysisResult:
        text = f"{item.title} {item.content}".lower()

        categories: list[str] = []
        for category, keywords in self._KEYWORD_CATEGORIES.items():
            if any(keyword in text for keyword in keywords):
                categories.append(category)
        if not categories:
            categories.append("OTHER")

        is_official = item.source_type == "OFFICIAL"
        priority = 4 if is_official else 3
        recommendation = "TEST" if is_official and "STT" in categories else "WATCH"

        return AIAnalysisResult.model_validate(
            {
                "title": item.title[:200],
                "summary": f"{item.title}. Материал собран из источника {item.source_name}.",
                "categories": categories,
                "why_it_matters": "Автоматически сгенерированный анализ (mock LLM provider, без реального LLM API).",
                "practical_use": "Оценить материал вручную — используется mock-провайдер.",
                "risks": ["Анализ выполнен mock-провайдером, не заменяет ручную проверку."],
                "recommendation": recommendation,
                "priority": priority,
                "scores": {
                    "novelty": 3,
                    "practical_value": 3,
                    "technical_significance": 3,
                    "enterprise_relevance": 2,
                    "personal_relevance": 3,
                    "source_reliability": 5 if item.source_type == "OFFICIAL" else 3,
                },
                "relevance": {
                    "stt": 5 if "STT" in categories else 0,
                    "meeting": 5 if "MEETING_INTELLIGENCE" in categories else 0,
                    "rag": 4 if "DOCUMENTS_RAG" in categories else 0,
                    "agents": 4 if "AI_AGENTS" in categories else 0,
                    "coding": 4 if "PROGRAMMING" in categories else 0,
                    "enterprise": 4 if "ENTERPRISE_AI" in categories else 0,
                    "on_prem": 0,
                },
                "estimated_test_effort": "1 hour" if recommendation == "TEST" else None,
                "suggested_test": "Прогнать тестовый набор данных и сравнить с текущим решением."
                if recommendation == "TEST"
                else None,
            }
        )


def get_llm_provider(settings: Settings) -> LLMProvider:
    if settings.llm_provider.lower() == "openai":
        if not settings.llm_api_key:
            logger.warning("LLM_PROVIDER=openai but LLM_API_KEY is empty — falling back to mock provider")
            return MockLLMProvider()
        return OpenAIProvider(
            api_key=settings.llm_api_key, model=settings.llm_model, api_base=settings.llm_api_base
        )
    return MockLLMProvider()
