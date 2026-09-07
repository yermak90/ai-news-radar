from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_by_telegram_id(self, telegram_user_id: int) -> User | None:
        result = await self.session.execute(select(User).where(User.telegram_user_id == telegram_user_id))
        return result.scalar_one_or_none()

    async def get_or_create(
        self,
        *,
        telegram_user_id: int,
        telegram_chat_id: int,
        username: str | None,
        timezone: str,
        is_admin: bool = False,
    ) -> User:
        user = await self.get_by_telegram_id(telegram_user_id)
        if user is not None:
            user.telegram_chat_id = telegram_chat_id
            user.username = username
            if is_admin:
                user.is_admin = True
            return user

        user = User(
            telegram_user_id=telegram_user_id,
            telegram_chat_id=telegram_chat_id,
            username=username,
            timezone=timezone,
            is_admin=is_admin,
        )
        self.session.add(user)
        await self.session.flush()
        return user

    async def list_active(self) -> list[User]:
        result = await self.session.execute(select(User).where(User.is_active.is_(True)))
        return list(result.scalars().all())
