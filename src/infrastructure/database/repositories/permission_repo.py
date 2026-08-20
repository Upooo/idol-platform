"""Permission repository — data access for permissions and role_permissions."""

from __future__ import annotations

import uuid

from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.tables import (
    PermissionTable,
    RolePermissionTable,
)


class PermissionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_by_key(self, key: str) -> PermissionTable | None:
        stmt = select(PermissionTable).where(PermissionTable.key == key)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(self) -> list[PermissionTable]:
        stmt = select(PermissionTable).order_by(PermissionTable.key)
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_role_permissions(
        self, role_id: uuid.UUID
    ) -> list[PermissionTable]:
        stmt = (
            select(PermissionTable)
            .join(
                RolePermissionTable,
                RolePermissionTable.permission_id == PermissionTable.id,
            )
            .where(RolePermissionTable.role_id == role_id)
            .order_by(PermissionTable.key)
        )
        result = await self._session.execute(stmt)
        return list(result.scalars().all())

    async def get_user_permission_keys(
        self, user_id: uuid.UUID
    ) -> set[str]:
        """Get all permission keys for a user across all their roles."""
        from src.infrastructure.database.tables import UserRoleTable

        stmt = (
            select(PermissionTable.key)
            .join(
                RolePermissionTable,
                RolePermissionTable.permission_id == PermissionTable.id,
            )
            .join(
                UserRoleTable,
                UserRoleTable.role_id == RolePermissionTable.role_id,
            )
            .where(UserRoleTable.user_id == user_id)
        )
        result = await self._session.execute(stmt)
        return set(result.scalars().all())

    async def grant(
        self, role_id: uuid.UUID, permission_id: uuid.UUID
    ) -> RolePermissionTable:
        entry = RolePermissionTable(
            id=uuid.uuid4(),
            role_id=role_id,
            permission_id=permission_id,
        )
        self._session.add(entry)
        await self._session.flush()
        return entry

    async def revoke(
        self, role_id: uuid.UUID, permission_id: uuid.UUID
    ) -> None:
        stmt = delete(RolePermissionTable).where(
            RolePermissionTable.role_id == role_id,
            RolePermissionTable.permission_id == permission_id,
        )
        await self._session.execute(stmt)
