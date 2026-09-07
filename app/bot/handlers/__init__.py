from aiogram import Router

from app.bot.handlers import admin, categories, digest, start


def build_root_router() -> Router:
    root = Router(name="root")
    root.include_router(start.router)
    root.include_router(digest.router)
    root.include_router(categories.router)
    root.include_router(admin.router)
    return root
