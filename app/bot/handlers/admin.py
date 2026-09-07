import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.ai.provider import LLMProvider
from app.config.settings import Settings
from app.services.pipeline_service import run_pipeline

logger = logging.getLogger(__name__)
router = Router(name="admin")


def _is_admin(message: Message, settings: Settings) -> bool:
    return (
        settings.admin_telegram_user_id is not None
        and message.from_user is not None
        and message.from_user.id == settings.admin_telegram_user_id
    )


@router.message(Command("refresh"))
async def handle_refresh(
    message: Message,
    session_factory: async_sessionmaker,
    settings: Settings,
    llm_provider: LLMProvider,
) -> None:
    if not _is_admin(message, settings):
        await message.answer("Эта команда доступна только администратору.")
        return

    await message.answer("🔄 Запускаю сбор и обработку новостей...")

    async with session_factory() as session:
        result = await run_pipeline(session, llm_provider)

    text = (
        "✅ Обновление завершено.\n\n"
        f"Источники: {result.collection.sources_ok} ok, {result.collection.sources_failed} failed\n"
        f"Новых материалов: {result.collection.items_new}\n"
        f"Отфильтровано: {result.extraction.filtered}\n"
        f"Дублей: {result.extraction.duplicates}\n"
        f"Отправлено в AI-анализ: {result.extraction.queued_for_ai}\n"
        f"Проанализировано: {result.analysis.analyzed} (ошибок: {result.analysis.ai_failed})"
    )
    await message.answer(text)
