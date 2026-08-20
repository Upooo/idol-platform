"""User repository — data access for the users table."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.tables import UserTable


class UserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_telegram_id(self, telegram_id: int) -> UserTable | None:
        stmt = select(UserTable).where(UserTable.telegram_id == telegram_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_by_id(self, user_id: uuid.UUID) -> UserTable | None:
        stmt = select(UserTable).where(UserTable.id == user_id)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def create(
        self,
        telegram_id: int,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
        status: str = "active",
    ) -> UserTable:
        user = UserTable(
            id=uuid.uuid4(),
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
            status=status,
        )
        self._session.add(user)
        await self._session.flush()
        return user

    async def update_profile(
        self,
        user_id: uuid.UUID,
        username: str | None = None,
        first_name: str | None = None,
        last_name: str | None = None,
    ) -> None:
        values: dict = {"updated_at": datetime.now(timezone.utc)}
        if username is not None:
            values["username"] = username
        if first_name is not None:
            values["first_name"] = first_name
        if last_name is not None:
            values["last_name"] = last_name
        stmt = update(UserTable).where(UserTable.id == user_id).values(**values)
        await self._session.execute(stmt)
