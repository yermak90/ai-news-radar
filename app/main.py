import asyncio
import logging

from app.ai.provider import get_llm_provider
from app.bot.bot import build_bot, build_dispatcher
from app.config.logging_config import configure_logging
from app.config.settings import get_settings
from app.db.seed_sources import seed_sources
from app.db.session import get_sessionmaker, init_engine
from app.scheduler.scheduler import build_scheduler

logger = logging.getLogger(__name__)


async def main() -> None:
    settings = get_settings()
    configure_logging(settings.log_level)

    if not settings.is_configured_for_telegram:
        logger.error(
            "TELEGRAM_BOT_TOKEN is not set. Fill in .env (see .env.example) before starting the bot."
        )
        return

    logger.info("Starting AI News Radar (timezone=%s)", settings.timezone)

    init_engine(settings.database_url)
    session_factory = get_sessionmaker()

    async with session_factory() as session:
        await seed_sources(session)

    llm_provider = get_llm_provider(settings)
    if settings.llm_provider.lower() == "mock":
        logger.warning(
            "LLM_PROVIDER=mock — running with a deterministic offline analyzer, no real LLM calls will be made"
        )

    bot = build_bot(settings)
    dp = build_dispatcher(settings=settings, session_factory=session_factory, llm_provider=llm_provider)

    scheduler = build_scheduler(
        settings=settings, session_factory=session_factory, llm_provider=llm_provider, bot=bot
    )
    scheduler.start()

    try:
        logger.info("Bot polling started")
        await dp.start_polling(bot)
    finally:
        scheduler.shutdown(wait=False)
        await bot.session.close()


if __name__ == "__main__":
    asyncio.run(main())
