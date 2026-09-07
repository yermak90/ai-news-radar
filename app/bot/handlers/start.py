import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.config.settings import Settings
from app.repositories.user_repository import UserRepository

logger = logging.getLogger(__name__)
router = Router(name="start")

HELP_TEXT = """\
🗞 <b>AI News Radar</b> — персональный дайджест AI-новостей.

<b>Команды:</b>
/today — дайджест за сегодня
/top — последние наиболее важные новости
/stt — STT / ASR / Speech
/meeting — Meeting Intelligence
/agents — AI Agents & Automation
/coding — Programming / Vibe Coding
/rag — Documents / RAG
/enterprise — Enterprise AI
/models — LLM & Models
/testing — материалы с рекомендацией TEST
/refresh — вручную запустить сбор новостей (только админ)
/help — это сообщение
"""


@router.message(Command("start"))
async def handle_start(message: Message, session_factory: async_sessionmaker, settings: Settings) -> None:
    if message.from_user is None or message.chat is None:
        return

    is_admin = (
        settings.admin_telegram_user_id is not None
        and message.from_user.id == settings.admin_telegram_user_id
    )

    async with session_factory() as session:
        user_repo = UserRepository(session)
        await user_repo.get_or_create(
            telegram_user_id=message.from_user.id,
            telegram_chat_id=message.chat.id,
            username=message.from_user.username,
            timezone=settings.timezone,
            is_admin=is_admin,
        )
        await session.commit()

    logger.info("User %s started the bot", message.from_user.id)
    await message.answer(
        "Привет! Я AI News Radar — буду присылать тебе аналитический дайджест AI-новостей раз в день.\n\n"
        + HELP_TEXT,
        parse_mode="HTML",
    )


@router.message(Command("help"))
async def handle_help(message: Message) -> None:
    await message.answer(HELP_TEXT, parse_mode="HTML")
