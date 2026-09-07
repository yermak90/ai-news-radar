import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.bot.formatters import format_digest, format_news_list
from app.config.settings import Settings
from app.repositories.news_repository import NewsRepository
from app.services.digest_service import build_digest
from app.services.time_utils import start_of_today_utc

logger = logging.getLogger(__name__)
router = Router(name="digest")


@router.message(Command("today"))
async def handle_today(message: Message, session_factory: async_sessionmaker, settings: Settings) -> None:
    async with session_factory() as session:
        news_repo = NewsRepository(session)
        since = start_of_today_utc(settings.timezone)
        items = await news_repo.list_recent(since=since, min_priority=1, limit=200)
        if not items:
            # Nothing processed yet today — fall back to the latest available items
            items = await news_repo.list_recent(min_priority=1, limit=200)

    digest = build_digest(items)
    for chunk in format_digest(digest):
        await message.answer(chunk, parse_mode="HTML", disable_web_page_preview=True)


@router.message(Command("top"))
async def handle_top(message: Message, session_factory: async_sessionmaker) -> None:
    async with session_factory() as session:
        news_repo = NewsRepository(session)
        items = await news_repo.list_top(limit=10, min_priority=2)

    for chunk in format_news_list(items, title="🏆 Top новости"):
        await message.answer(chunk, parse_mode="HTML", disable_web_page_preview=True)
