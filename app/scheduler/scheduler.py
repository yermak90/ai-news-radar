import logging

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.ai.provider import LLMProvider
from app.config.settings import Settings
from app.scheduler.jobs import collection_job, daily_digest_job

logger = logging.getLogger(__name__)


def build_scheduler(
    *,
    settings: Settings,
    session_factory: async_sessionmaker,
    llm_provider: LLMProvider,
    bot: Bot,
) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=settings.timezone)

    scheduler.add_job(
        collection_job,
        trigger=IntervalTrigger(minutes=settings.collection_interval_minutes),
        args=[session_factory, llm_provider],
        id="collection_job",
        max_instances=1,
        coalesce=True,
    )

    scheduler.add_job(
        daily_digest_job,
        trigger=CronTrigger(
            hour=settings.digest_hour, minute=settings.digest_minute, timezone=settings.timezone
        ),
        args=[session_factory, bot, settings],
        id="daily_digest_job",
        max_instances=1,
        coalesce=True,
    )

    logger.info(
        "Scheduler configured: collection every %d min, daily digest at %02d:%02d %s",
        settings.collection_interval_minutes,
        settings.digest_hour,
        settings.digest_minute,
        settings.timezone,
    )
    return scheduler
