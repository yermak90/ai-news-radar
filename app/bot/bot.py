from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.ai.provider import LLMProvider
from app.bot.handlers import build_root_router
from app.config.settings import Settings


def build_bot(settings: Settings) -> Bot:
    return Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )


def build_dispatcher(
    *, settings: Settings, session_factory: async_sessionmaker, llm_provider: LLMProvider
) -> Dispatcher:
    dp = Dispatcher()
    dp.include_router(build_root_router())

    # Injected into every handler as kwargs matching these parameter names.
    dp["settings"] = settings
    dp["session_factory"] = session_factory
    dp["llm_provider"] = llm_provider

    return dp
