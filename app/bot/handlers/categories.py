from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import async_sessionmaker

from app.bot.formatters import format_news_list
from app.models.enums import Category, Recommendation
from app.repositories.news_repository import NewsRepository

router = Router(name="categories")

_CATEGORY_COMMANDS: dict[str, tuple[Category, str]] = {
    "stt": (Category.STT, "🎙 STT / Speech / Transcription"),
    "meeting": (Category.MEETING_INTELLIGENCE, "🗓 Meeting Intelligence"),
    "agents": (Category.AI_AGENTS, "🤖 AI Agents & Automation"),
    "coding": (Category.PROGRAMMING, "💻 Programming / Vibe Coding"),
    "rag": (Category.DOCUMENTS_RAG, "📄 AI for Documents / RAG"),
    "enterprise": (Category.ENTERPRISE_AI, "🏢 Enterprise AI"),
    "models": (Category.LLM_MODELS, "🧠 LLM & Models"),
}


def _make_category_handler(category: Category, title: str):
    async def handler(message: Message, session_factory: async_sessionmaker) -> None:
        async with session_factory() as session:
            news_repo = NewsRepository(session)
            items = await news_repo.list_by_category(category, min_priority=1, limit=15)
        for chunk in format_news_list(items, title=title):
            await message.answer(chunk, parse_mode="HTML", disable_web_page_preview=True)

    return handler


for command_name, (category, title) in _CATEGORY_COMMANDS.items():
    router.message(Command(command_name))(_make_category_handler(category, title))


@router.message(Command("testing"))
async def handle_testing(message: Message, session_factory: async_sessionmaker) -> None:
    async with session_factory() as session:
        news_repo = NewsRepository(session)
        items = await news_repo.list_by_recommendation(Recommendation.TEST, limit=15)
    for chunk in format_news_list(items, title="🧪 Worth Testing"):
        await message.answer(chunk, parse_mode="HTML", disable_web_page_preview=True)
