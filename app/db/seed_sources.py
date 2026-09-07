"""Initial source list (PRD section 8).

Feed URLs for company blogs (OpenAI, Anthropic, Google AI, Meta AI, NVIDIA,
GitHub Changelog) are best-effort: this sandboxed build environment has no
general internet egress, so these could not be curl-verified while writing
this seed list. GitHub Releases and the official arXiv/Hacker News APIs use
stable, well-documented URL shapes and are high-confidence. If a blog RSS
URL has moved, that one source will just log a fetch error and contribute
zero items — it will not break collection for the other sources (PRD
section 46). See README for how to fix/replace a feed URL.
"""

import logging

from app.models.enums import CollectionMethod, SourceType
from app.repositories.source_repository import SourceRepository

logger = logging.getLogger(__name__)

SEED_SOURCES: list[dict] = [
    # --- Tier 1: Official blogs (RSS) ---
    {
        "name": "OpenAI Blog",
        "type": SourceType.OFFICIAL,
        "url": "https://openai.com/blog",
        "feed_url": "https://openai.com/blog/rss.xml",
        "priority": 5,
        "collection_method": CollectionMethod.RSS,
        "category_hint": "LLM_MODELS",
    },
    {
        "name": "Anthropic News",
        "type": SourceType.OFFICIAL,
        "url": "https://www.anthropic.com/news",
        "feed_url": "https://www.anthropic.com/rss.xml",
        "priority": 5,
        "collection_method": CollectionMethod.RSS,
        "category_hint": "LLM_MODELS",
    },
    {
        "name": "Google AI Blog",
        "type": SourceType.OFFICIAL,
        "url": "https://blog.google/technology/ai/",
        "feed_url": "https://blog.google/technology/ai/rss/",
        "priority": 5,
        "collection_method": CollectionMethod.RSS,
        "category_hint": "LLM_MODELS",
    },
    {
        "name": "Meta AI Blog",
        "type": SourceType.OFFICIAL,
        "url": "https://ai.meta.com/blog/",
        "feed_url": "https://ai.meta.com/blog/rss/",
        "priority": 5,
        "collection_method": CollectionMethod.RSS,
        "category_hint": "LLM_MODELS",
    },
    {
        "name": "NVIDIA Blog",
        "type": SourceType.OFFICIAL,
        "url": "https://blogs.nvidia.com/",
        "feed_url": "https://blogs.nvidia.com/feed/",
        "priority": 4,
        "collection_method": CollectionMethod.RSS,
        "category_hint": "LLM_MODELS",
    },
    {
        "name": "Hugging Face Blog",
        "type": SourceType.OFFICIAL,
        "url": "https://huggingface.co/blog",
        "feed_url": "https://huggingface.co/blog/feed.xml",
        "priority": 5,
        "collection_method": CollectionMethod.RSS,
        "category_hint": "LLM_MODELS",
    },
    {
        "name": "GitHub Changelog",
        "type": SourceType.OFFICIAL,
        "url": "https://github.blog/changelog/",
        "feed_url": "https://github.blog/changelog/feed/",
        "priority": 4,
        "collection_method": CollectionMethod.RSS,
        "category_hint": "PROGRAMMING",
    },
    # --- Tier 2: Research ---
    {
        "name": "arXiv (cs.AI/cs.CL/cs.LG)",
        "type": SourceType.RESEARCH,
        "url": "https://arxiv.org",
        "feed_url": None,  # ArxivCollector uses its own default search_query
        "priority": 4,
        "collection_method": CollectionMethod.API,
        "category_hint": "LLM_MODELS",
    },
    # --- Tier 3: Community / GitHub Releases ---
    {
        "name": "Hacker News (AI)",
        "type": SourceType.COMMUNITY,
        "url": "https://news.ycombinator.com",
        "feed_url": None,  # HackerNewsCollector uses its own default AI query
        "priority": 2,
        "collection_method": CollectionMethod.API,
        "category_hint": "OTHER",
    },
    {
        "name": "Hugging Face Transformers Releases",
        "type": SourceType.OFFICIAL,
        "url": "https://github.com/huggingface/transformers/releases",
        "feed_url": "https://api.github.com/repos/huggingface/transformers/releases",
        "priority": 5,
        "collection_method": CollectionMethod.GITHUB,
        "category_hint": "LLM_MODELS",
    },
    {
        "name": "llama.cpp Releases",
        "type": SourceType.COMMUNITY,
        "url": "https://github.com/ggerganov/llama.cpp/releases",
        "feed_url": "https://api.github.com/repos/ggerganov/llama.cpp/releases",
        "priority": 4,
        "collection_method": CollectionMethod.GITHUB,
        "category_hint": "LLM_MODELS",
    },
    {
        "name": "vLLM Releases",
        "type": SourceType.COMMUNITY,
        "url": "https://github.com/vllm-project/vllm/releases",
        "feed_url": "https://api.github.com/repos/vllm-project/vllm/releases",
        "priority": 4,
        "collection_method": CollectionMethod.GITHUB,
        "category_hint": "LLM_MODELS",
    },
    {
        "name": "LangChain Releases",
        "type": SourceType.COMMUNITY,
        "url": "https://github.com/langchain-ai/langchain/releases",
        "feed_url": "https://api.github.com/repos/langchain-ai/langchain/releases",
        "priority": 3,
        "collection_method": CollectionMethod.GITHUB,
        "category_hint": "AI_AGENTS",
    },
    {
        "name": "Microsoft AutoGen Releases",
        "type": SourceType.OFFICIAL,
        "url": "https://github.com/microsoft/autogen/releases",
        "feed_url": "https://api.github.com/repos/microsoft/autogen/releases",
        "priority": 5,
        "collection_method": CollectionMethod.GITHUB,
        "category_hint": "AI_AGENTS",
    },
    {
        "name": "DeepSeek-V3 Releases",
        "type": SourceType.OFFICIAL,
        "url": "https://github.com/deepseek-ai/DeepSeek-V3/releases",
        "feed_url": "https://api.github.com/repos/deepseek-ai/DeepSeek-V3/releases",
        "priority": 5,
        "collection_method": CollectionMethod.GITHUB,
        "category_hint": "LLM_MODELS",
    },
    {
        "name": "Qwen Releases",
        "type": SourceType.OFFICIAL,
        "url": "https://github.com/QwenLM/Qwen2.5/releases",
        "feed_url": "https://api.github.com/repos/QwenLM/Qwen2.5/releases",
        "priority": 5,
        "collection_method": CollectionMethod.GITHUB,
        "category_hint": "LLM_MODELS",
    },
    {
        "name": "Mistral Inference Releases",
        "type": SourceType.OFFICIAL,
        "url": "https://github.com/mistralai/mistral-inference/releases",
        "feed_url": "https://api.github.com/repos/mistralai/mistral-inference/releases",
        "priority": 4,
        "collection_method": CollectionMethod.GITHUB,
        "category_hint": "LLM_MODELS",
    },
    {
        "name": "NVIDIA TensorRT-LLM Releases",
        "type": SourceType.OFFICIAL,
        "url": "https://github.com/NVIDIA/TensorRT-LLM/releases",
        "feed_url": "https://api.github.com/repos/NVIDIA/TensorRT-LLM/releases",
        "priority": 4,
        "collection_method": CollectionMethod.GITHUB,
        "category_hint": "LLM_MODELS",
    },
]


async def seed_sources(session) -> int:
    """Idempotently insert/update the initial source list. Safe to call on every startup."""
    repo = SourceRepository(session)
    for entry in SEED_SOURCES:
        await repo.upsert(**entry)
    await session.commit()
    logger.info("Seeded %d sources", len(SEED_SOURCES))
    return len(SEED_SOURCES)
