"""Core bot handlers — /start, /help, /cancel, profile, main menu.

Redesigned with futuristic, elegant UI formatting.
"""

from __future__ import annotations

import structlog
from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession

from src.domain.enums import ROLE_HIERARCHY, PermissionKey, RoleType
from src.domain.models import User
from src.presentation.keyboards.main_menu import (
    back_button,
    main_menu_keyboard,
)

log = structlog.get_logger()
router = Router(name="core")

# ━━━ UI Constants ━━━
LINE = "─" * 28
HEADER_LINE = "━" * 28


def _role_badge(user: User) -> str:
    """Generate role badge string."""
    if not user.roles:
        return "<i>No role assigned</i>"
    badges = []
    for r in user.roles:
        level = ROLE_HIERARCHY.get(r.role_type, "?")
        badges.append(f"{r.role_type.value.upper()} ⌊{level}⌋")
    return " · ".join(badges)


def _user_tag(user: User) -> str:
    """Format user display tag."""
    parts = [f"<b>{user.full_name}</b>"]
    if user.username:
        parts.append(f"<code>@{user.username}</code>")
    return " ".join(parts)


@router.message(CommandStart())
async def cmd_start(message: Message, platform_user: User) -> None:
    """Welcome message with role-aware menu."""
    text = (
        f"┌{'━' * 26}┐\n"
        f"   ◈  <b>I D O L</b>  ◈\n"
        f"└{'━' * 26}┘\n\n"
        f"Welcome, {_user_tag(platform_user)}\n"
        f"{LINE}\n"
        f"◉ Role: {_role_badge(platform_user)}\n"
        f"{LINE}\n\n"
        f"<i>Select an option below</i>"
    )

    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=main_menu_keyboard(platform_user),
    )


@router.message(Command("help"))
async def cmd_help(message: Message, platform_user: User) -> None:
    """Help text — role-aware command list."""
    lines = [
        f"┌{'━' * 26}┐\n"
        f"   ◈  <b>COMMAND LIST</b>  ◈\n"
        f"└{'━' * 26}┘\n",
        f"<b>▸ General</b>",
        "  /start — Main menu",
        "  /help — This message",
        "  /id — Check ID (yours / reply / group)",
        "  /cancel — Cancel operation",
    ]

    if platform_user.has_permission(PermissionKey.STAFF_VIEW):
        lines.append(f"\n<b>▸ Staff</b>")
        lines.append("  /staff — List all staff")

    if platform_user.has_permission(PermissionKey.ROLES_ASSIGN):
        lines.append(f"\n<b>▸ Roles</b>")
        lines.append("  /assign — Assign role (reply / @user / ID)")
        lines.append("  /revoke — Revoke role (reply / @user / ID)")

    if platform_user.has_permission(PermissionKey.GROUP_MODERATE):
        lines.append(f"\n<b>▸ Group</b>")
        lines.append("  /info — Group info")
        lines.append("  /promote — Promote to admin")
        lines.append("  /demote — Demote from admin")
        lines.append("  /ban — Ban user")
        lines.append("  /unban — Unban user")
        lines.append("  /mute — Mute user")
        lines.append("  /unmute — Unmute user")
        lines.append("  /kick — Kick user")
        lines.append("  /pin — Pin message")
        lines.append("  /unpin — Unpin message")

    lines.append(f"\n{LINE}")
    lines.append("<i>Commands adapt to your role</i>")

    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("cancel"))
async def cmd_cancel(message: Message) -> None:
    """Cancel current operation."""
    await message.answer("◈ Operation cancelled.")


@router.message(Command("myid"))
async def cmd_myid(message: Message, platform_user: User) -> None:
    """Show user's Telegram ID."""
    await message.answer(
        f"◉ Your ID: <code>{platform_user.telegram_id}</code>",
        parse_mode="HTML",
    )


@router.message(Command("myroles"))
async def cmd_myroles(message: Message, platform_user: User) -> None:
    """Show user's assigned roles and permissions."""
    if not platform_user.roles:
        await message.answer(
            f"{LINE}\n"
            f"◈ <b>Your Roles</b>\n"
            f"{LINE}\n\n"
            f"<i>No roles assigned</i>",
            parse_mode="HTML",
        )
        return

    lines = [
        f"{LINE}",
        f"◈ <b>Your Roles</b>",
        f"{LINE}\n",
    ]
    for role in platform_user.roles:
        level = ROLE_HIERARCHY.get(role.role_type, "?")
        lines.append(f"  ▸ <b>{role.role_type.value.upper()}</b> ⌊level {level}⌋")

    if platform_user.is_founder:
        lines.append(f"\n<i>◉ Founder — all permissions implicit</i>")
    elif platform_user.permissions:
        lines.append(f"\n<b>Permissions:</b>")
        for p in sorted(platform_user.permissions, key=lambda x: x.value):
            lines.append(f"  ◦ <code>{p.value}</code>")
    else:
        lines.append(f"\n<i>No explicit permissions</i>")

    await message.answer("\n".join(lines), parse_mode="HTML")


# ━━━ Callback: Main Menu ━━━

@router.callback_query(lambda c: c.data == "main_menu")
async def cb_main_menu(
    callback: CallbackQuery, platform_user: User
) -> None:
    """Return to main menu."""
    text = (
        f"┌{'━' * 26}┐\n"
        f"   ◈  <b>I D O L</b>  ◈\n"
        f"└{'━' * 26}┘\n\n"
        f"Welcome, {_user_tag(platform_user)}\n"
        f"{LINE}\n"
        f"◉ Role: {_role_badge(platform_user)}\n"
        f"{LINE}\n\n"
        f"<i>Select an option below</i>"
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
    """Show user profile."""
    u = platform_user
    role_str = _role_badge(u)

    text = (
        f"{LINE}\n"
        f"◈ <b>Profile</b>\n"
        f"{LINE}\n\n"
        f"▸ Name: <b>{u.full_name}</b>\n"
        f"▸ Username: {('@' + u.username) if u.username else '<i>N/A</i>'}\n"
        f"▸ ID: <code>{u.telegram_id}</code>\n"
        f"▸ Roles: {role_str}\n"
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
    """Show staff list via callback button."""
    from src.application import auth_service
    auth_service.require_permission(platform_user, PermissionKey.STAFF_VIEW)

    async with db_session_factory() as session:
        from src.infrastructure.database.repositories import (
            RoleRepository,
            UserRepository,
        )
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

    if callback.message:
        await callback.message.edit_text(
            "\n".join(lines),
            parse_mode="HTML",
            reply_markup=back_button(),
        )
    await callback.answer()


# ━━━ Callback: Roles Manage (placeholder) ━━━

@router.callback_query(lambda c: c.data == "roles_manage")
async def cb_roles_manage(
    callback: CallbackQuery, platform_user: User
) -> None:
    """Roles management menu."""
    from src.application import auth_service
    auth_service.require_permission(platform_user, PermissionKey.ROLES_ASSIGN)

    text = (
        f"{LINE}\n"
        f"◈ <b>Role Management</b>\n"
        f"{LINE}\n\n"
        f"Use commands to manage roles:\n\n"
        f"▸ <code>/assign</code> — reply, @username, or ID\n"
        f"▸ <code>/revoke</code> — reply, @username, or ID\n"
        f"▸ <code>/staff</code> — view all staff\n\n"
        f"<i>Assign supports: reply to message,\n"
        f"@username, or numeric Telegram ID</i>"
    )

    if callback.message:
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=back_button(),
        )
    await callback.answer()


# ━━━ Callback: Audit Log (placeholder) ━━━

@router.callback_query(lambda c: c.data == "audit_log")
async def cb_audit_log(
    callback: CallbackQuery, platform_user: User
) -> None:
    """Audit log placeholder."""
    from src.application import auth_service
    auth_service.require_permission(platform_user, PermissionKey.SYSTEM_AUDIT)

    text = (
        f"{LINE}\n"
        f"◈ <b>Audit Log</b>\n"
        f"{LINE}\n\n"
        f"<i>Coming soon — audit log viewer</i>"
    )

    if callback.message:
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=back_button(),
        )
    await callback.answer()


# ━━━ Callback: Settings (placeholder) ━━━

@router.callback_query(lambda c: c.data == "settings")
async def cb_settings(
    callback: CallbackQuery, platform_user: User
) -> None:
    """Settings placeholder."""
    from src.application import auth_service
    auth_service.require_permission(platform_user, PermissionKey.SYSTEM_SETTINGS)

    text = (
        f"{LINE}\n"
        f"◈ <b>Settings</b>\n"
        f"{LINE}\n\n"
        f"<i>Coming soon — system settings</i>"
    )

    if callback.message:
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=back_button(),
        )
    await callback.answer()
