from pydantic import BaseModel, Field, field_validator

from app.models.enums import Category, Recommendation

VALID_TEST_EFFORTS = {"15 min", "1 hour", "half-day", "1 day+", "unknown"}


class Scores(BaseModel):
    novelty: int = Field(ge=0, le=5)
    practical_value: int = Field(ge=0, le=5)
    technical_significance: int = Field(ge=0, le=5)
    enterprise_relevance: int = Field(ge=0, le=5)
    personal_relevance: int = Field(ge=0, le=5)
    source_reliability: int = Field(ge=0, le=5)


class Relevance(BaseModel):
    stt: int = Field(ge=0, le=5, default=0)
    meeting: int = Field(ge=0, le=5, default=0)
    rag: int = Field(ge=0, le=5, default=0)
    agents: int = Field(ge=0, le=5, default=0)
    coding: int = Field(ge=0, le=5, default=0)
    enterprise: int = Field(ge=0, le=5, default=0)
    on_prem: int = Field(ge=0, le=5, default=0)


class AIAnalysisResult(BaseModel):
    """Structured LLM output for one news cluster (PRD section 36)."""

    title: str = Field(min_length=1, max_length=512)
    summary: str = Field(min_length=1)
    categories: list[Category] = Field(min_length=1)
    why_it_matters: str = Field(min_length=1)
    practical_use: str = Field(min_length=1)
    risks: list[str] = Field(default_factory=list)
    recommendation: Recommendation
    priority: int = Field(ge=1, le=5)
    scores: Scores
    relevance: Relevance
    estimated_test_effort: str | None = None
    suggested_test: str | None = None

    @field_validator("estimated_test_effort")
    @classmethod
    def validate_test_effort(cls, value: str | None) -> str | None:
        if value is not None and value not in VALID_TEST_EFFORTS:
            return "unknown"
        return value

    @field_validator("categories")
    @classmethod
    def dedupe_categories(cls, value: list[Category]) -> list[Category]:
        seen: list[Category] = []
        for category in value:
            if category not in seen:
                seen.append(category)
        return seen
