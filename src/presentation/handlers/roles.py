"""Role management handlers — assign/revoke roles via bot.

Only Founder and Owner (with ROLES_ASSIGN permission) can use these.
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


# ── /staff — list all staff ──

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
        user_repo = UserRepository(session)

        all_roles = await role_repo.get_all()
        lines = ["👥 <b>IDOL Staff</b>\n"]

        for role_row in all_roles:
            if role_row.name == "customer":
                continue

            # Get users with this role
            from sqlalchemy import select
            from src.infrastructure.database.tables import (
                UserRoleTable,
                UserTable,
            )

            stmt = (
                select(UserTable)
                .join(
                    UserRoleTable,
                    UserRoleTable.user_id == UserTable.id,
                )
                .where(UserRoleTable.role_id == role_row.id)
                .order_by(UserTable.first_name)
            )
            result = await session.execute(stmt)
            users = list(result.scalars().all())

            if users:
                level = ROLE_HIERARCHY.get(
                    RoleType(role_row.name), 99
                )
                lines.append(
                    f"\n<b>{role_row.name.title()}</b> (level {level}):"
                )
                for u in users:
                    name = u.first_name or u.username or str(u.telegram_id)
                    lines.append(
                        f"  • {name} — <code>{u.telegram_id}</code>"
                    )

    if len(lines) == 1:
        lines.append("\n<i>No staff assigned yet.</i>")

    await message.answer("\n".join(lines), parse_mode="HTML")


# ── /assign <telegram_id> — start role assignment ──

@router.message(Command("assign"))
async def cmd_assign(
    message: Message,
    platform_user: User,
) -> None:
    """Assign a role to a user. Usage: /assign <telegram_id>"""
    auth_service.require_permission(
        platform_user, PermissionKey.ROLES_ASSIGN
    )

    args = message.text.split() if message.text else []
    if len(args) < 2:
        await message.answer(
            "📋 <b>Usage:</b> <code>/assign &lt;telegram_id&gt;</code>\n\n"
            "Example: <code>/assign 123456789</code>",
            parse_mode="HTML",
        )
        return

    try:
        target_tg_id = int(args[1])
    except ValueError:
        await message.answer("⚠️ Telegram ID must be a number.")
        return

    # Build role selection keyboard
    # Show only roles the actor can assign (below their level)
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
            continue  # Can't assign roles at or above own level
        if role_type == RoleType.CUSTOMER:
            continue  # Customer is default, no need to assign

        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"{role_type.value.title()} (level {level})",
                    callback_data=f"assign:{target_tg_id}:{role_type.value}",
                )
            ]
        )

    if not buttons:
        await message.answer("⚠️ No assignable roles available.")
        return

    buttons.append(
        [
            InlineKeyboardButton(
                text="❌ Cancel", callback_data="main_menu"
            )
        ]
    )

    await message.answer(
        f"🛠 <b>Assign role to user</b> <code>{target_tg_id}</code>\n\n"
        "Select a role:",
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
                # Auto-create if they haven't /start'd yet
                target_row = await user_repo.create(
                    telegram_id=target_tg_id
                )
                await session.flush()

            # Resolve target as domain User for auth checks
            target_user = await resolve_user(
                session, target_tg_id
            )

            # Auth: permission + hierarchy + founder protection
            auth_service.authorize_role_change(
                platform_user,
                target_user,
                PermissionKey.ROLES_ASSIGN,
            )

            # Check if already has this role
            has_role = await role_repo.has_role(
                target_row.id, role_name
            )
            if has_role:
                await callback.answer(
                    f"User already has {role_name} role.",
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

    # Notify via group
    from src.infrastructure.notification.service import NotificationService

    notif = NotificationService(bot)
    target_name = target_user.full_name
    actor_name = platform_user.full_name
    await notif.notify_staff(
        f"🛡 <b>Role Assigned</b>\n\n"
        f"<b>{target_name}</b> (<code>{target_tg_id}</code>)\n"
        f"→ <b>{role_name.title()}</b>\n"
        f"By: {actor_name}"
    )

    if callback.message:
        await callback.message.edit_text(
            f"✅ <b>{role_name.title()}</b> role assigned to "
            f"<code>{target_tg_id}</code>",
            parse_mode="HTML",
        )
    await callback.answer("Role assigned!")


# ── /revoke <telegram_id> — start role removal ──

@router.message(Command("revoke"))
async def cmd_revoke(
    message: Message,
    platform_user: User,
    db_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    """Remove a role from a user. Usage: /revoke <telegram_id>"""
    auth_service.require_permission(
        platform_user, PermissionKey.ROLES_ASSIGN
    )

    args = message.text.split() if message.text else []
    if len(args) < 2:
        await message.answer(
            "📋 <b>Usage:</b> <code>/revoke &lt;telegram_id&gt;</code>",
            parse_mode="HTML",
        )
        return

    try:
        target_tg_id = int(args[1])
    except ValueError:
        await message.answer("⚠️ Telegram ID must be a number.")
        return

    # Load target's current roles
    async with db_session_factory() as session:
        user_repo = UserRepository(session)
        role_repo = RoleRepository(session)

        target_row = await user_repo.get_by_telegram_id(target_tg_id)
        if target_row is None:
            await message.answer("⚠️ User not found.")
            return

        user_roles = await role_repo.get_user_roles(target_row.id)

    if not user_roles:
        await message.answer("ℹ️ User has no roles to revoke.")
        return

    # Build role selection keyboard (only show roles user actually has)
    buttons: list[list[InlineKeyboardButton]] = []
    for role_row in user_roles:
        buttons.append(
            [
                InlineKeyboardButton(
                    text=f"❌ {role_row.name.title()}",
                    callback_data=f"revoke:{target_tg_id}:{role_row.name}",
                )
            ]
        )

    buttons.append(
        [
            InlineKeyboardButton(
                text="↩️ Cancel", callback_data="main_menu"
            )
        ]
    )

    target_name = (
        target_row.first_name
        or target_row.username
        or str(target_tg_id)
    )
    await message.answer(
        f"🗑 <b>Revoke role from {target_name}</b>\n"
        f"ID: <code>{target_tg_id}</code>\n\n"
        "Select role to remove:",
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

            # Auth check
            auth_service.authorize_role_change(
                platform_user,
                target_user,
                PermissionKey.ROLES_ASSIGN,
            )

            # Find role
            role = await role_repo.get_by_name(role_name)
            if role is None:
                await callback.answer(
                    "Role not found.", show_alert=True
                )
                return

            # Check they actually have it
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

            # Revoke
            await role_repo.remove_role(
                user_id=target_row.id, role_id=role.id
            )

            # Audit
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

    # Notify
    from src.infrastructure.notification.service import NotificationService

    notif = NotificationService(bot)
    await notif.notify_staff(
        f"🔻 <b>Role Revoked</b>\n\n"
        f"<code>{target_tg_id}</code>\n"
        f"✖ <b>{role_name.title()}</b>\n"
        f"By: {platform_user.full_name}"
    )

    if callback.message:
        await callback.message.edit_text(
            f"✅ <b>{role_name.title()}</b> role removed from "
            f"<code>{target_tg_id}</code>",
            parse_mode="HTML",
        )
    await callback.answer("Role revoked!")
