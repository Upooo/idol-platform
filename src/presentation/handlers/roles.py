"""Role management handlers — assign/revoke roles via bot.

Supports targeting via reply, @username, or telegram ID.
All operations enforce: permission check + hierarchy + founder protection.
"""

from __future__ import annotations

import structlog
from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from src.application import auth_service
from src.application.audit_service import AuditService
from src.application.target_resolver import resolve_target
from src.application.user_resolver import resolve_user
from src.domain.enums import (
    AuditAction,
    ROLE_HIERARCHY,
    PermissionKey,
    RoleType,
)
from src.domain.models import User
from src.infrastructure.database.repositories import (
    RoleRepository,
    UserRepository,
)

log = structlog.get_logger()
router = Router(name="roles")

LINE = "─" * 28


# ━━━ /staff — list all staff ━━━

@router.message(Command("staff"))
async def cmd_staff(
    message: Message,
    platform_user: User,
    db_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """List all users with roles above Customer."""
    auth_service.require_permission(platform_user, PermissionKey.STAFF_VIEW)

    async with db_session_factory() as session:
        role_repo = RoleRepository(session)

        from sqlalchemy import select
        from src.infrastructure.database.tables import UserRoleTable, UserTable

        all_roles = await role_repo.get_all()
        lines = [
            f"{LINE}",
            f"◈ <b>Staff Directory</b>",
            f"{LINE}",
        ]

        has_staff = False
        for role_row in all_roles:
            if role_row.name == "customer":
                continue

            stmt = (
                select(UserTable)
                .join(UserRoleTable, UserRoleTable.user_id == UserTable.id)
                .where(UserRoleTable.role_id == role_row.id)
                .order_by(UserTable.first_name)
            )
            result = await session.execute(stmt)
            users = list(result.scalars().all())

            if users:
                has_staff = True
                level = ROLE_HIERARCHY.get(RoleType(role_row.name), 99)
                lines.append(
                    f"\n<b>▸ {role_row.name.upper()}</b> ⌊{level}⌋"
                )
                for u in users:
                    name = u.first_name or u.username or str(u.telegram_id)
                    uname = f" (@{u.username})" if u.username else ""
                    lines.append(
                        f"  ◦ {name}{uname} · <code>{u.telegram_id}</code>"
                    )

    if not has_staff:
        lines.append("\n<i>No staff assigned yet</i>")

    await message.answer("\n".join(lines), parse_mode="HTML")


# ━━━ /assign — start role assignment ━━━

@router.message(Command("assign"))
async def cmd_assign(
    message: Message,
    platform_user: User,
    bot: Bot,
) -> None:
    """Assign a role. Usage: /assign (reply | @username | ID)"""
    auth_service.require_permission(
        platform_user, PermissionKey.ROLES_ASSIGN
    )

    # Parse args after /assign
    args = message.text.split(maxsplit=1) if message.text else []
    args_text = args[1] if len(args) > 1 else None

    target = await resolve_target(message, bot, args_text)
    if target is None:
        await message.answer(
            f"{LINE}\n"
            f"◈ <b>Assign Role</b>\n"
            f"{LINE}\n\n"
            f"<b>Usage:</b>\n"
            f"  ▸ Reply to a message + <code>/assign</code>\n"
            f"  ▸ <code>/assign @username</code>\n"
            f"  ▸ <code>/assign 123456789</code>",
            parse_mode="HTML",
        )
        return

    # Build role selection keyboard
    actor_role = platform_user.highest_role
    actor_level = (
        ROLE_HIERARCHY.get(actor_role.role_type, 999)
        if actor_role
        else 999
    )

    buttons: list[list[InlineKeyboardButton]] = []
    for role_type in RoleType:
        level = ROLE_HIERARCHY.get(role_type, 999)
        if level <= actor_level:
            continue
        if role_type == RoleType.CUSTOMER:
            continue

        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"{role_type.value.upper()} ⌊{level}⌋",
                    callback_data=f"assign:{target.telegram_id}:{role_type.value}",
                )
            ]
        )

    if not buttons:
        await message.answer("◈ No assignable roles available.")
        return

    buttons.append(
        [
            InlineKeyboardButton(
                text="◇ Cancel", callback_data="main_menu"
            )
        ]
    )

    await message.answer(
        f"{LINE}\n"
        f"◈ <b>Assign Role</b>\n"
        f"{LINE}\n\n"
        f"▸ Target: {target.display_tag}\n\n"
        f"<i>Select a role:</i>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@router.callback_query(lambda c: c.data and c.data.startswith("assign:"))
async def cb_assign_role(
    callback: CallbackQuery,
    platform_user: User,
    db_session_factory: async_sessionmaker[AsyncSession],
    bot: Bot,
) -> None:
    """Execute role assignment after selection."""
    parts = callback.data.split(":")  # type: ignore
    if len(parts) != 3:
        await callback.answer("Invalid action.", show_alert=True)
        return

    target_tg_id = int(parts[1])
    role_name = parts[2]

    async with db_session_factory() as session:
        async with session.begin():
            user_repo = UserRepository(session)
            role_repo = RoleRepository(session)
            audit = AuditService(session)

            # Resolve target user
            target_row = await user_repo.get_by_telegram_id(target_tg_id)
            if target_row is None:
                target_row = await user_repo.create(
                    telegram_id=target_tg_id
                )
                await session.flush()

            target_user = await resolve_user(session, target_tg_id)

            # Auth
            auth_service.authorize_role_change(
                platform_user,
                target_user,
                PermissionKey.ROLES_ASSIGN,
            )

            # Check if already has role
            has_role = await role_repo.has_role(
                target_row.id, role_name
            )
            if has_role:
                await callback.answer(
                    f"Already has {role_name} role.",
                    show_alert=True,
                )
                return

            # Find role
            role = await role_repo.get_by_name(role_name)
            if role is None:
                await callback.answer(
                    "Role not found.", show_alert=True
                )
                return

            # Assign
            await role_repo.assign_role(
                user_id=target_row.id,
                role_id=role.id,
                assigned_by=platform_user.id,
            )

            # Audit
            await audit.log(
                action=AuditAction.ROLE_ASSIGNED,
                actor_id=platform_user.id,
                target_type="user",
                target_id=str(target_tg_id),
                metadata={
                    "role": role_name,
                    "assigned_by": platform_user.telegram_id,
                },
            )

    # Resolve target info for display
    try:
        chat = await bot.get_chat(target_tg_id)
        target_name = chat.first_name or chat.username or str(target_tg_id)
        target_uname = f" (@{chat.username})" if chat.username else ""
    except Exception:
        target_name = str(target_tg_id)
        target_uname = ""

    actor_name = platform_user.full_name

    # Notify group
    from src.infrastructure.notification.service import NotificationService

    notif = NotificationService(bot)
    await notif.notify_staff(
        f"{LINE}\n"
        f"◈ <b>Role Assigned</b>\n"
        f"{LINE}\n\n"
        f"▸ User: <b>{target_name}</b>{target_uname}\n"
        f"  ID: <code>{target_tg_id}</code>\n"
        f"▸ Role: <b>{role_name.upper()}</b>\n"
        f"▸ By: {actor_name}"
    )

    if callback.message:
        await callback.message.edit_text(
            f"{LINE}\n"
            f"◈ <b>Role Assigned</b>\n"
            f"{LINE}\n\n"
            f"▸ <b>{target_name}</b>{target_uname}\n"
            f"  → <b>{role_name.upper()}</b>\n\n"
            f"<i>Assignment complete</i>",
            parse_mode="HTML",
        )
    await callback.answer("Role assigned!")


# ━━━ /revoke — start role removal ━━━

@router.message(Command("revoke"))
async def cmd_revoke(
    message: Message,
    platform_user: User,
    db_session_factory: async_sessionmaker[AsyncSession],
    bot: Bot,
) -> None:
    """Remove a role. Usage: /revoke (reply | @username | ID)"""
    auth_service.require_permission(
        platform_user, PermissionKey.ROLES_ASSIGN
    )

    args = message.text.split(maxsplit=1) if message.text else []
    args_text = args[1] if len(args) > 1 else None

    target = await resolve_target(message, bot, args_text)
    if target is None:
        await message.answer(
            f"{LINE}\n"
            f"◈ <b>Revoke Role</b>\n"
            f"{LINE}\n\n"
            f"<b>Usage:</b>\n"
            f"  ▸ Reply to a message + <code>/revoke</code>\n"
            f"  ▸ <code>/revoke @username</code>\n"
            f"  ▸ <code>/revoke 123456789</code>",
            parse_mode="HTML",
        )
        return

    # Load target's current roles
    async with db_session_factory() as session:
        user_repo = UserRepository(session)
        role_repo = RoleRepository(session)

        target_row = await user_repo.get_by_telegram_id(target.telegram_id)
        if target_row is None:
            await message.answer("◈ User not found.")
            return

        user_roles = await role_repo.get_user_roles(target_row.id)

    if not user_roles:
        await message.answer("◈ User has no roles to revoke.")
        return

    buttons: list[list[InlineKeyboardButton]] = []
    for role_row in user_roles:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"✕ {role_row.name.upper()}",
                    callback_data=f"revoke:{target.telegram_id}:{role_row.name}",
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text="◇ Cancel", callback_data="main_menu"
            )
        ]
    )

    await message.answer(
        f"{LINE}\n"
        f"◈ <b>Revoke Role</b>\n"
        f"{LINE}\n\n"
        f"▸ Target: {target.display_tag}\n\n"
        f"<i>Select role to remove:</i>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


@router.callback_query(lambda c: c.data and c.data.startswith("revoke:"))
async def cb_revoke_role(
    callback: CallbackQuery,
    platform_user: User,
    db_session_factory: async_sessionmaker[AsyncSession],
    bot: Bot,
) -> None:
    """Execute role removal after selection."""
    parts = callback.data.split(":")  # type: ignore
    if len(parts) != 3:
        await callback.answer("Invalid action.", show_alert=True)
        return

    target_tg_id = int(parts[1])
    role_name = parts[2]

    async with db_session_factory() as session:
        async with session.begin():
            user_repo = UserRepository(session)
            role_repo = RoleRepository(session)
            audit = AuditService(session)

            target_user = await resolve_user(session, target_tg_id)

            auth_service.authorize_role_change(
                platform_user,
                target_user,
                PermissionKey.ROLES_ASSIGN,
            )

            role = await role_repo.get_by_name(role_name)
            if role is None:
                await callback.answer(
                    "Role not found.", show_alert=True
                )
                return

            target_row = await user_repo.get_by_telegram_id(target_tg_id)
            if target_row is None:
                await callback.answer(
                    "User not found.", show_alert=True
                )
                return

            has_role = await role_repo.has_role(
                target_row.id, role_name
            )
            if not has_role:
                await callback.answer(
                    f"User doesn't have {role_name} role.",
                    show_alert=True,
                )
                return

            await role_repo.remove_role(
                user_id=target_row.id, role_id=role.id
            )

            await audit.log(
                action=AuditAction.ROLE_REMOVED,
                actor_id=platform_user.id,
                target_type="user",
                target_id=str(target_tg_id),
                metadata={
                    "role": role_name,
                    "revoked_by": platform_user.telegram_id,
                },
            )

    # Display info
    try:
        chat = await bot.get_chat(target_tg_id)
        target_name = chat.first_name or chat.username or str(target_tg_id)
        target_uname = f" (@{chat.username})" if chat.username else ""
    except Exception:
        target_name = str(target_tg_id)
        target_uname = ""

    from src.infrastructure.notification.service import NotificationService

    notif = NotificationService(bot)
    await notif.notify_staff(
        f"{LINE}\n"
        f"◈ <b>Role Revoked</b>\n"
        f"{LINE}\n\n"
        f"▸ User: <b>{target_name}</b>{target_uname}\n"
        f"  ID: <code>{target_tg_id}</code>\n"
        f"▸ Role: <b>✕ {role_name.upper()}</b>\n"
        f"▸ By: {platform_user.full_name}"
    )

    if callback.message:
        await callback.message.edit_text(
            f"{LINE}\n"
            f"◈ <b>Role Revoked</b>\n"
            f"{LINE}\n\n"
            f"▸ <b>{target_name}</b>{target_uname}\n"
            f"  ✕ <b>{role_name.upper()}</b>\n\n"
            f"<i>Revocation complete</i>",
            parse_mode="HTML",
        )
    await callback.answer("Role revoked!")
