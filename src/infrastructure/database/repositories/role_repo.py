"""Role repository — data access for roles and user_roles tables."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.tables import RoleTable, UserRoleTable


class RoleRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_name(self, name: str) -> RoleTable | None:
        stmt = select(RoleTable).where(RoleTable.name == name)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self) -> list[RoleTable]:
        stmt = select(RoleTable).order_by(RoleTable.hierarchy_level)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_user_roles(self, user_id: uuid.UUID) -> list[RoleTable]:
        stmt = (
            select(RoleTable)
            .join(UserRoleTable, UserRoleTable.role_id == RoleTable.id)
            .where(UserRoleTable.user_id == user_id)
            .order_by(RoleTable.hierarchy_level)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def assign_role(
        self,
        user_id: uuid.UUID,
        role_id: uuid.UUID,
        assigned_by: uuid.UUID | None = None,
    ) -> UserRoleTable:
        entry = UserRoleTable(
            id=uuid.uuid4(),
            user_id=user_id,
            role_id=role_id,
            assigned_by=assigned_by,
            assigned_at=datetime.now(timezone.utc),
        )
        self._session.add(entry)
        await self._session.flush()
        return entry

    async def has_role(self, user_id: uuid.UUID, role_name: str) -> bool:
        stmt = (
            select(UserRoleTable.id)
            .join(RoleTable, RoleTable.id == UserRoleTable.role_id)
            .where(
                UserRoleTable.user_id == user_id,
                RoleTable.name == role_name,
            )
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def remove_role(
        self, user_id: uuid.UUID, role_id: uuid.UUID
    ) -> None:
        stmt = delete(UserRoleTable).where(
            UserRoleTable.user_id == user_id,
            UserRoleTable.role_id == role_id,
        )
        await self._session.execute(stmt)
