"""Core bot handlers — /start, /help, /cancel, profile, main menu."""

from __future__ import annotations

import structlog
from aiogram import Router
from aiogram.filters import CommandStart, Command
from aiogram.types import CallbackQuery, Message

from src.domain.enums import ROLE_HIERARCHY, PermissionKey
from src.domain.models import User
from src.presentation.keyboards.main_menu import (
    back_button,
    main_menu_keyboard,
)

log = structlog.get_logger()
router = Router(name="core")


@router.message(CommandStart())
async def cmd_start(message: Message, platform_user: User) -> None:
    """Welcome message with role-aware menu."""
    name = platform_user.full_name
    role_names = [
        r.role_type.value.title() for r in platform_user.roles
    ]
    role_str = ", ".join(role_names) if role_names else "No role assigned"

    text = (
        f"🌟 <b>Welcome to IDOL Platform</b>\n\n"
        f"Hello, <b>{name}</b>!\n"
        f"Role: <b>{role_str}</b>\n\n"
        f"Select an option below:"
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
        "📖 <b>IDOL Platform — Help</b>\n",
        "<b>Everyone:</b>",
        "/start — Main menu",
        "/help — This message",
        "/myid — Your Telegram ID",
        "/myroles — Your assigned roles",
        "/cancel — Cancel current operation",
    ]

    if platform_user.has_permission(PermissionKey.STAFF_VIEW):
        lines.append("\n<b>Staff Management:</b>")
        lines.append("/staff — List all staff")

    if platform_user.has_permission(PermissionKey.ROLES_ASSIGN):
        lines.append("/assign &lt;id&gt; — Assign role to user")
        lines.append("/revoke &lt;id&gt; — Remove role from user")

    await message.answer("\n".join(lines), parse_mode="HTML")


@router.message(Command("cancel"))
async def cmd_cancel(message: Message) -> None:
    """Cancel current operation."""
    await message.answer("✅ Operation cancelled.")


@router.message(Command("myid"))
async def cmd_myid(message: Message, platform_user: User) -> None:
    """Show user's Telegram ID."""
    await message.answer(
        f"🆔 Your Telegram ID: <code>{platform_user.telegram_id}</code>",
        parse_mode="HTML",
    )


@router.message(Command("myroles"))
async def cmd_myroles(message: Message, platform_user: User) -> None:
    """Show user's assigned roles and permissions."""
    if not platform_user.roles:
        await message.answer("👤 You have no roles assigned.")
        return

    lines = ["🛡 <b>Your Roles:</b>\n"]
    for role in platform_user.roles:
        level = ROLE_HIERARCHY.get(role.role_type, "?")
        lines.append(f"• <b>{role.role_type.value.title()}</b> (level {level})")

    if platform_user.is_founder:
        lines.append("\n🔑 <i>Founder has ALL permissions implicitly.</i>")
    elif platform_user.permissions:
        lines.append("\n🔐 <b>Permissions:</b>")
        for p in sorted(platform_user.permissions, key=lambda x: x.value):
            lines.append(f"  • {p.value}")
    else:
        lines.append("\n<i>No explicit permissions assigned.</i>")

    await message.answer("\n".join(lines), parse_mode="HTML")


@router.callback_query(lambda c: c.data == "main_menu")
async def cb_main_menu(
    callback: CallbackQuery, platform_user: User
) -> None:
    """Return to main menu."""
    name = platform_user.full_name
    role_names = [
        r.role_type.value.title() for r in platform_user.roles
    ]
    role_str = ", ".join(role_names) if role_names else "No role assigned"

    text = (
        f"🌟 <b>IDOL Platform</b>\n\n"
        f"Hello, <b>{name}</b>!\n"
        f"Role: <b>{role_str}</b>\n\n"
        f"Select an option below:"
    )

    if callback.message:
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(platform_user),
        )
    await callback.answer()


@router.callback_query(lambda c: c.data == "profile")
async def cb_profile(
    callback: CallbackQuery, platform_user: User
) -> None:
    """Show user profile."""
    u = platform_user
    role_names = [r.role_type.value.title() for r in u.roles]
    role_str = ", ".join(role_names) if role_names else "None"

    text = (
        "👤 <b>Your Profile</b>\n\n"
        f"Name: <b>{u.full_name}</b>\n"
        f"Username: @{u.username or 'N/A'}\n"
        f"Telegram ID: <code>{u.telegram_id}</code>\n"
        f"Roles: <b>{role_str}</b>\n"
    )

    if callback.message:
        await callback.message.edit_text(
            text,
            parse_mode="HTML",
            reply_markup=back_button(),
        )
    await callback.answer()
