"""Core bot handlers — /start, /help, /cancel, profile, main menu."""

from __future__ import annotations

import structlog
from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from src.application.target_resolver import ROLE_ICONS
from src.domain.enums import ROLE_HIERARCHY, PermissionKey, RoleType
from src.domain.models import User
from src.presentation.keyboards.main_menu import (
    back_button,
    main_menu_keyboard,
)

log = structlog.get_logger()
router = Router(name="core")


def _role_label(user: User) -> str:
    """Format role label with icon."""
    if not user.roles:
        return "No role"
    labels = []
    for r in user.roles:
        icon = ROLE_ICONS.get(r.role_type.value, "")
        labels.append(f"{icon} {r.role_type.value.title()}")
    return " · ".join(labels)


@router.message(CommandStart())
async def cmd_start(message: Message, platform_user: User) -> None:
    """Welcome message with role-aware menu."""
    name = platform_user.first_name or platform_user.full_name
    role = _role_label(platform_user)

    text = (
        f"Welcome to <b>IDOL</b> 👋\n\n"
        f"<b>{name}</b>\n"
        f"{role}\n\n"
        f"Manage your workspace from here."
    )

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(platform_user),
    )


@router.message(Command("help"))
async def cmd_help(message: Message, platform_user: User) -> None:
    """Role-aware command list."""
    lines = [
        "<b>Commands</b>\n",
        "<b>General</b>",
        "/start — Main menu",
        "/help — This list",
        "/id — Check ID",
        "/cancel — Cancel operation",
    ]

    if platform_user.has_permission(PermissionKey.STAFF_VIEW):
        lines.append("\n<b>Team</b>")
        lines.append("/staff — View team")

    if platform_user.has_permission(PermissionKey.ROLES_ASSIGN):
        lines.append("\n<b>Roles</b>")
        lines.append("/assign — Assign role")
        lines.append("/revoke — Revoke role")

    if platform_user.has_permission(PermissionKey.GROUP_MODERATE):
        lines.append("\n<b>Group</b>")
        lines.append("/info — Group info")
        lines.append("/promote · /demote — Admin")
        lines.append("/ban · /unban — Ban")
        lines.append("/mute · /unmute — Mute")
        lines.append("/kick — Kick")
        lines.append("/pin · /unpin — Pin")

    lines.append("\n<i>Commands adapt to your role.</i>")

    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("cancel"))
async def cmd_cancel(message: Message) -> None:
    await message.answer("Cancelled.")


@router.message(Command("myid"))
async def cmd_myid(message: Message, platform_user: User) -> None:
    await message.answer(
        f"Your ID: <code>{platform_user.telegram_id}</code>",
        parse_mode="HTML",
    )


@router.message(Command("myroles"))
async def cmd_myroles(message: Message, platform_user: User) -> None:
    if not platform_user.roles:
        await message.answer(
            "<b>My Roles</b>\n\n"
            "No roles assigned yet.",
            parse_mode="HTML",
        )
        return

    lines = ["<b>My Roles</b>\n"]
    for role in platform_user.roles:
        icon = ROLE_ICONS.get(role.role_type.value, "")
        lines.append(f"{icon} <b>{role.role_type.value.title()}</b>")

    if platform_user.is_founder:
        lines.append("\n<i>All permissions (Founder)</i>")
    elif platform_user.permissions:
        lines.append("\n<b>Permissions</b>")
        for p in sorted(platform_user.permissions, key=lambda x: x.value):
            lines.append(f"  <code>{p.value}</code>")
    else:
        lines.append("\n<i>No explicit permissions</i>")

    await message.answer("\n".join(lines), parse_mode="HTML")


# ━━━ Callback: Main Menu ━━━

@router.callback_query(lambda c: c.data == "main_menu")
async def cb_main_menu(
    callback: CallbackQuery, platform_user: User
) -> None:
    name = platform_user.first_name or platform_user.full_name
    role = _role_label(platform_user)

    text = (
        f"Welcome to <b>IDOL</b> 👋\n\n"
        f"<b>{name}</b>\n"
        f"{role}\n\n"
        f"Manage your workspace from here."
    )

    if callback.message:
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(platform_user),
        )
    await callback.answer()


# ━━━ Callback: Profile ━━━

@router.callback_query(lambda c: c.data == "profile")
async def cb_profile(
    callback: CallbackQuery, platform_user: User
) -> None:
    u = platform_user
    role = _role_label(u)
    uname = f"@{u.username}" if u.username else "—"

    text = (
        f"👤 <b>Profile</b>\n\n"
        f"Name: <b>{u.full_name}</b>\n"
        f"Username: {uname}\n"
        f"ID: <code>{u.telegram_id}</code>\n"
        f"Role: {role}"
    )

    if callback.message:
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=back_button(),
        )
    await callback.answer()


# ━━━ Callback: Staff List ━━━

@router.callback_query(lambda c: c.data == "staff_list")
async def cb_staff_list(
    callback: CallbackQuery,
    platform_user: User,
    db_session_factory: async_sessionmaker[AsyncSession],
) -> None:
    from src.application import auth_service
    auth_service.require_permission(platform_user, PermissionKey.STAFF_VIEW)

    async with db_session_factory() as session:
        from src.infrastructure.database.repositories import RoleRepository
        from sqlalchemy import select
        from src.infrastructure.database.tables import UserRoleTable, UserTable

        role_repo = RoleRepository(session)
        all_roles = await role_repo.get_all()
        lines = ["👥 <b>Team</b>\n"]

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
                icon = ROLE_ICONS.get(role_row.name, "")
                lines.append(f"<b>{icon} {role_row.name.title()}</b>")
                for u in users:
                    name = u.first_name or u.username or str(u.telegram_id)
                    uname = f" · @{u.username}" if u.username else ""
                    lines.append(
                        f"  {name}{uname}"
                    )
                lines.append("")  # spacing

        if not has_staff:
            lines.append("No team members yet.\n")
            lines.append("Use /assign to add someone.")

    if callback.message:
        await callback.message.edit_text(
            "\n".join(lines),
            parse_mode="HTML",
            reply_markup=back_button(),
        )
    await callback.answer()


# ━━━ Callback: Roles Manage ━━━

@router.callback_query(lambda c: c.data == "roles_manage")
async def cb_roles_manage(
    callback: CallbackQuery, platform_user: User
) -> None:
    from src.application import auth_service
    auth_service.require_permission(platform_user, PermissionKey.ROLES_ASSIGN)

    text = (
        "🔑 <b>Role Management</b>\n\n"
        "<code>/assign</code> — reply, @user, or ID\n"
        "<code>/revoke</code> — reply, @user, or ID\n"
        "<code>/staff</code> — view team\n\n"
        "<i>Supports reply, @username, and numeric ID.</i>"
    )

    if callback.message:
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=back_button(),
        )
    await callback.answer()


# ━━━ Callback: Audit Log ━━━

@router.callback_query(lambda c: c.data == "audit_log")
async def cb_audit_log(
    callback: CallbackQuery, platform_user: User
) -> None:
    from src.application import auth_service
    auth_service.require_permission(platform_user, PermissionKey.SYSTEM_AUDIT)

    text = (
        "📋 <b>Audit Log</b>\n\n"
        "Coming soon.\n\n"
        "<i>Activity history will appear here.</i>"
    )

    if callback.message:
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=back_button(),
        )
    await callback.answer()


# ━━━ Callback: Settings ━━━

@router.callback_query(lambda c: c.data == "settings")
async def cb_settings(
    callback: CallbackQuery, platform_user: User
) -> None:
    from src.application import auth_service
    auth_service.require_permission(platform_user, PermissionKey.SYSTEM_SETTINGS)

    text = (
        "⚙️ <b>Settings</b>\n\n"
        "Coming soon.\n\n"
        "<i>Bot configuration will be here.</i>"
    )

    if callback.message:
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=back_button(),
        )
    await callback.answer()
