"""Cheap keyword-based pre-filter, applied before the paid LLM call (PRD section 14).

Official/Research sources are AI-focused by construction and always pass.
Broader discovery sources (Hacker News, tech media) need keyword filtering
to drop the large fraction of stories that have nothing to do with AI.
"""

_AI_KEYWORDS = (
    "ai",
    "a.i.",
    "artificial intelligence",
    "llm",
    "large language model",
    "gpt",
    "claude",
    "gemini",
    "copilot",
    "chatbot",
    "machine learning",
    "neural",
    "transformer",
    "deep learning",
    "diffusion",
    "generative",
    "openai",
    "anthropic",
    "deepmind",
    "hugging face",
    "huggingface",
    "mistral",
    "deepseek",
    "qwen",
    "llama",
    "nvidia",
    "agent",
    "rag",
    "speech-to-text",
    "speech to text",
    "transcription",
    "asr",
    "embedding",
    "inference",
    "fine-tun",
    "reasoning model",
    "multimodal",
    "text-to-image",
    "text-to-video",
    "tts",
)

# Sources at these tiers are AI-focused by construction — skip keyword filtering.
_ALWAYS_RELEVANT_SOURCE_TYPES = {"OFFICIAL", "RESEARCH"}


def is_relevant(*, title: str, text: str, source_type: str) -> bool:
    if source_type in _ALWAYS_RELEVANT_SOURCE_TYPES:
        return True
    haystack = f"{title} {text[:1000]}".lower()
    return any(keyword in haystack for keyword in _AI_KEYWORDS)
