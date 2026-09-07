import enum


class SourceType(str, enum.Enum):
    """Source reliability tier, per PRD section 7."""

    OFFICIAL = "OFFICIAL"  # Tier 1
    RESEARCH = "RESEARCH"  # Tier 2
    COMMUNITY = "COMMUNITY"  # Tier 3
    MEDIA = "MEDIA"  # Tier 4


class CollectionMethod(str, enum.Enum):
    RSS = "RSS"
    ATOM = "ATOM"
    API = "API"
    GITHUB = "GITHUB"
    HTML = "HTML"
    OTHER = "OTHER"


class ProcessingStatus(str, enum.Enum):
    NEW = "NEW"
    EXTRACTED = "EXTRACTED"
    DUPLICATE = "DUPLICATE"
    FILTERED = "FILTERED"
    QUEUED_FOR_AI = "QUEUED_FOR_AI"
    PROCESSED = "PROCESSED"
    FAILED = "FAILED"


class Category(str, enum.Enum):
    LLM_MODELS = "LLM_MODELS"
    PROGRAMMING = "PROGRAMMING"
    STT = "STT"
    MEETING_INTELLIGENCE = "MEETING_INTELLIGENCE"
    DOCUMENTS_RAG = "DOCUMENTS_RAG"
    AI_AGENTS = "AI_AGENTS"
    ENTERPRISE_AI = "ENTERPRISE_AI"
    MULTIMEDIA = "MULTIMEDIA"
    OTHER = "OTHER"


class Recommendation(str, enum.Enum):
    TEST = "TEST"
    WATCH = "WATCH"
    SKIP = "SKIP"


class DigestStatus(str, enum.Enum):
    SENT = "SENT"
    FAILED = "FAILED"
