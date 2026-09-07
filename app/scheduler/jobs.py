import logging
from datetime import UTC, datetime

from aiogram import Bot
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.ai.provider import LLMProvider
from app.bot.formatters import format_digest
from app.config.settings import Settings
from app.models.enums import DigestStatus
from app.repositories.digest_repository import DigestRepository
from app.repositories.news_repository import NewsRepository
from app.repositories.user_repository import UserRepository
from app.services.digest_service import build_digest
from app.services.pipeline_service import run_pipeline
from app.services.time_utils import now_in_timezone, start_of_today_utc

logger = logging.getLogger(__name__)


async def collection_job(session_factory: async_sessionmaker, llm_provider: LLMProvider) -> None:
    logger.info("Scheduled collection job starting")
    async with session_factory() as session:
        await run_pipeline(session, llm_provider)
    logger.info("Scheduled collection job finished")


async def daily_digest_job(session_factory: async_sessionmaker, bot: Bot, settings: Settings) -> None:
    """Sends the daily digest to every active user, at most once per calendar day (PRD section 48)."""
    logger.info("Daily digest job starting")
    today = now_in_timezone(settings.timezone).date()
    since = start_of_today_utc(settings.timezone)

    async with session_factory() as session:
        user_repo = UserRepository(session)
        digest_repo = DigestRepository(session)
        news_repo = NewsRepository(session)

        users = await user_repo.list_active()
        if not users:
            logger.info("No active users to send the daily digest to")
            return

        items = await news_repo.list_recent(since=since, min_priority=1, limit=200)
        digest = build_digest(items)
        messages = format_digest(digest)

        for user in users:
            existing_delivery = await digest_repo.get_delivery(user.id, today)
            if existing_delivery is not None:
                logger.info("Digest already sent to user %s for %s, skipping", user.telegram_user_id, today)
                continue

            status = DigestStatus.SENT
            try:
                for message_text in messages:
                    await bot.send_message(
                        chat_id=user.telegram_chat_id,
                        text=message_text,
                        parse_mode="HTML",
                        disable_web_page_preview=True,
                    )
            except Exception:
                logger.warning("Failed to send digest to user %s", user.telegram_user_id, exc_info=True)
                status = DigestStatus.FAILED

            await digest_repo.record_delivery(user.id, today, datetime.now(UTC), status)
            await session.commit()

    logger.info("Daily digest job finished")
