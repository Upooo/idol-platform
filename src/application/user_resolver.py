"""User resolver — loads a platform User from Telegram context.

Used by the auth middleware to hydrate the user on every request.
"""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.enums import PermissionKey, RoleType
from src.domain.models import Role, User
from src.infrastructure.database.repositories import (
    PermissionRepository,
    RoleRepository,
    UserRepository,
)


async def resolve_user(
    session: AsyncSession,
    telegram_id: int,
    username: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
) -> User:
    """Find or create a platform User, fully hydrated with roles + permissions.

    New users are auto-registered with no role (treated as Customer-level).
    Profile fields (username, first_name, last_name) are updated if changed.
    """
    user_repo = UserRepository(session)
    role_repo = RoleRepository(session)
    perm_repo = PermissionRepository(session)

    # Find or create
    row = await user_repo.get_by_telegram_id(telegram_id)
    if row is None:
        row = await user_repo.create(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name,
        )
        await session.flush()
    else:
        # Update profile if changed
        changed = False
        if username and row.username != username:
            changed = True
        if first_name and row.first_name != first_name:
            changed = True
        if last_name and row.last_name != last_name:
            changed = True
        if changed:
            await user_repo.update_profile(
                user_id=row.id,
                username=username,
                first_name=first_name,
                last_name=last_name,
            )

    # Load roles
    role_rows = await role_repo.get_user_roles(row.id)
    roles = [
        Role(
            id=r.id,
            role_type=RoleType(r.name),
            description=r.description,
        )
        for r in role_rows
    ]

    # Load permissions (across all roles)
    perm_keys = await perm_repo.get_user_permission_keys(row.id)
    permissions = set()
    for key in perm_keys:
        try:
            permissions.add(PermissionKey(key))
        except ValueError:
            pass  # Unknown permission key in DB — skip

    return User(
        id=row.id,
        telegram_id=row.telegram_id,
        username=row.username,
        first_name=row.first_name,
        last_name=row.last_name,
        roles=roles,
        permissions=permissions,
    )
