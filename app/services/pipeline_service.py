"""Runs the full collection -> extraction -> dedup -> AI analysis pipeline once.

Used by both the scheduler's periodic collection job and the /refresh
admin command, so the two never drift apart.
"""

import logging
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.provider import LLMProvider
from app.services.collection_service import CollectionStats, run_collection
from app.services.processing_service import ProcessingStats, extract_and_dedup, run_ai_analysis

logger = logging.getLogger(__name__)


@dataclass
class PipelineResult:
    collection: CollectionStats
    extraction: ProcessingStats
    analysis: ProcessingStats


async def run_pipeline(session: AsyncSession, llm_provider: LLMProvider) -> PipelineResult:
    collection_stats = await run_collection(session)
    extraction_stats = await extract_and_dedup(session)
    analysis_stats = await run_ai_analysis(session, llm_provider)

    logger.info(
        "Pipeline run complete: %d new raw items, %d queued for AI, %d analyzed, %d AI failures",
        collection_stats.items_new,
        extraction_stats.queued_for_ai,
        analysis_stats.analyzed,
        analysis_stats.ai_failed,
    )
    return PipelineResult(collection=collection_stats, extraction=extraction_stats, analysis=analysis_stats)
