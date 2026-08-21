"""Group management handlers — promote, demote, ban, mute, kick, info, pin.

Bot must be admin in the group for these to work.
All operations check RBAC permissions.
"""

from __future__ import annotations

import re
from datetime import timedelta

import structlog
from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import (
    ChatPermissions,
    Message,
)

from src.application import auth_service
from src.application.target_resolver import resolve_target
from src.domain.enums import PermissionKey
from src.domain.models import User

log = structlog.get_logger()
router = Router(name="group")

LINE = "─" * 28


def _parse_duration(text: str | None) -> timedelta | None:
    """Parse duration string like 1h, 30m, 2d. Default None = 1 hour."""
    if not text:
        return timedelta(hours=1)
    match = re.match(r"^(\d+)([mhd])$", text.strip().lower())
    if not match:
        return timedelta(hours=1)
    val = int(match.group(1))
    unit = match.group(2)
    if unit == "m":
        return timedelta(minutes=val)
    elif unit == "h":
        return timedelta(hours=val)
    elif unit == "d":
        return timedelta(days=val)
    return timedelta(hours=1)


# ━━━ /id — check ID ━━━

@router.message(Command("id"))
async def cmd_id(message: Message, platform_user: User) -> None:
    """Check ID: own, replied user, or group."""
    lines = [
        f"{LINE}",
        f"◈ <b>ID Info</b>",
        f"{LINE}",
        "",
    ]

    # Own ID
    lines.append(f"▸ You: <code>{platform_user.telegram_id}</code>")
    if platform_user.username:
        lines.append(f"  @{platform_user.username}")

    # Replied user
    if message.reply_to_message and message.reply_to_message.from_user:
        ru = message.reply_to_message.from_user
        name = ru.first_name or ru.username or str(ru.id)
        uname = f" (@{ru.username})" if ru.username else ""
        lines.append(f"\n▸ Reply: <b>{name}</b>{uname}")
        lines.append(f"  ID: <code>{ru.id}</code>")

    # Chat/Group
    if message.chat.type in ("group", "supergroup"):
        lines.append(f"\n▸ Group: <b>{message.chat.title}</b>")
        lines.append(f"  ID: <code>{message.chat.id}</code>")
        lines.append(f"  Type: <code>{message.chat.type}</code>")
    elif message.chat.type == "private":
        lines.append(f"\n▸ Chat: <i>Private</i>")

    await message.answer("\n".join(lines), parse_mode="HTML")


# ━━━ /info — group info ━━━

@router.message(Command("info"))
async def cmd_info(
    message: Message, platform_user: User, bot: Bot
) -> None:
    """Show group information."""
    if message.chat.type not in ("group", "supergroup"):
        await message.answer("◈ This command works in groups only.")
        return

    chat = await bot.get_chat(message.chat.id)
    member_count = await bot.get_chat_member_count(message.chat.id)

    # Count admins
    admins = await bot.get_chat_administrators(message.chat.id)
    admin_count = len([a for a in admins if not a.user.is_bot])
    bot_count = len([a for a in admins if a.user.is_bot])

    lines = [
        f"{LINE}",
        f"◈ <b>Group Info</b>",
        f"{LINE}",
        "",
        f"▸ Title: <b>{chat.title}</b>",
        f"▸ ID: <code>{chat.id}</code>",
        f"▸ Type: <code>{chat.type}</code>",
        f"▸ Members: <b>{member_count}</b>",
        f"▸ Admins: <b>{admin_count}</b> human · <b>{bot_count}</b> bot",
    ]

    if chat.description:
        desc = chat.description[:200]
        lines.append(f"\n▸ Description:\n<i>{desc}</i>")

    if chat.invite_link:
        lines.append(f"\n▸ Invite: {chat.invite_link}")

    await message.answer("\n".join(lines), parse_mode="HTML")


# ━━━ /promote — promote to admin ━━━

@router.message(Command("promote"))
async def cmd_promote(
    message: Message, platform_user: User, bot: Bot
) -> None:
    """Promote user to group admin."""
    auth_service.require_permission(
        platform_user, PermissionKey.GROUP_MANAGE
    )

    if message.chat.type not in ("group", "supergroup"):
        await message.answer("◈ This command works in groups only.")
        return

    args = message.text.split(maxsplit=1) if message.text else []
    args_text = args[1] if len(args) > 1 else None
    target = await resolve_target(message, bot, args_text)

    if target is None:
        await message.answer(
            f"{LINE}\n"
            f"◈ <b>Promote</b>\n"
            f"{LINE}\n\n"
            f"Reply to user or: <code>/promote @user</code>",
            parse_mode="HTML",
        )
        return

    try:
        await bot.promote_chat_member(
            chat_id=message.chat.id,
            user_id=target.telegram_id,
            can_manage_chat=True,
            can_delete_messages=True,
            can_restrict_members=True,
            can_pin_messages=True,
            can_invite_users=True,
        )
        await message.answer(
            f"{LINE}\n"
            f"◈ <b>Promoted</b>\n"
            f"{LINE}\n\n"
            f"▸ {target.display_tag}\n"
            f"  → Group Admin",
            parse_mode="HTML",
        )
    except Exception as e:
        await message.answer(f"◈ Failed to promote: <code>{e}</code>", parse_mode="HTML")


# ━━━ /demote — demote from admin ━━━

@router.message(Command("demote"))
async def cmd_demote(
    message: Message, platform_user: User, bot: Bot
) -> None:
    """Demote user from group admin."""
    auth_service.require_permission(
        platform_user, PermissionKey.GROUP_MANAGE
    )

    if message.chat.type not in ("group", "supergroup"):
        await message.answer("◈ This command works in groups only.")
        return

    args = message.text.split(maxsplit=1) if message.text else []
    args_text = args[1] if len(args) > 1 else None
    target = await resolve_target(message, bot, args_text)

    if target is None:
        await message.answer(
            f"{LINE}\n"
            f"◈ <b>Demote</b>\n"
            f"{LINE}\n\n"
            f"Reply to user or: <code>/demote @user</code>",
            parse_mode="HTML",
        )
        return

    try:
        await bot.promote_chat_member(
            chat_id=message.chat.id,
            user_id=target.telegram_id,
            can_manage_chat=False,
            can_delete_messages=False,
            can_restrict_members=False,
            can_pin_messages=False,
            can_invite_users=False,
        )
        await message.answer(
            f"{LINE}\n"
            f"◈ <b>Demoted</b>\n"
            f"{LINE}\n\n"
            f"▸ {target.display_tag}\n"
            f"  → Member",
            parse_mode="HTML",
        )
    except Exception as e:
        await message.answer(f"◈ Failed to demote: <code>{e}</code>", parse_mode="HTML")


# ━━━ /ban — ban user ━━━

@router.message(Command("ban"))
async def cmd_ban(
    message: Message, platform_user: User, bot: Bot
) -> None:
    """Ban user from group."""
    auth_service.require_permission(
        platform_user, PermissionKey.GROUP_MODERATE
    )

    if message.chat.type not in ("group", "supergroup"):
        await message.answer("◈ This command works in groups only.")
        return

    args = message.text.split(maxsplit=1) if message.text else []
    args_text = args[1] if len(args) > 1 else None
    target = await resolve_target(message, bot, args_text)

    if target is None:
        await message.answer(
            f"{LINE}\n"
            f"◈ <b>Ban</b>\n"
            f"{LINE}\n\n"
            f"Reply to user or: <code>/ban @user</code>",
            parse_mode="HTML",
        )
        return

    try:
        await bot.ban_chat_member(
            chat_id=message.chat.id,
            user_id=target.telegram_id,
        )
        await message.answer(
            f"{LINE}\n"
            f"◈ <b>Banned</b>\n"
            f"{LINE}\n\n"
            f"▸ {target.display_tag}\n"
            f"  ✕ Removed from group",
            parse_mode="HTML",
        )
    except Exception as e:
        await message.answer(f"◈ Failed to ban: <code>{e}</code>", parse_mode="HTML")


# ━━━ /unban — unban user ━━━

@router.message(Command("unban"))
async def cmd_unban(
    message: Message, platform_user: User, bot: Bot
) -> None:
    """Unban user from group."""
    auth_service.require_permission(
        platform_user, PermissionKey.GROUP_MODERATE
    )

    if message.chat.type not in ("group", "supergroup"):
        await message.answer("◈ This command works in groups only.")
        return

    args = message.text.split(maxsplit=1) if message.text else []
    args_text = args[1] if len(args) > 1 else None
    target = await resolve_target(message, bot, args_text)

    if target is None:
        await message.answer(
            f"{LINE}\n"
            f"◈ <b>Unban</b>\n"
            f"{LINE}\n\n"
            f"<code>/unban @user</code> or <code>/unban 123456789</code>",
            parse_mode="HTML",
        )
        return

    try:
        await bot.unban_chat_member(
            chat_id=message.chat.id,
            user_id=target.telegram_id,
            only_if_banned=True,
        )
        await message.answer(
            f"{LINE}\n"
            f"◈ <b>Unbanned</b>\n"
            f"{LINE}\n\n"
            f"▸ {target.display_tag}\n"
            f"  ◉ Can rejoin",
            parse_mode="HTML",
        )
    except Exception as e:
        await message.answer(f"◈ Failed to unban: <code>{e}</code>", parse_mode="HTML")


# ━━━ /mute — mute user ━━━

@router.message(Command("mute"))
async def cmd_mute(
    message: Message, platform_user: User, bot: Bot
) -> None:
    """Mute user. Usage: /mute [reply|@user|ID] [30m|1h|2d]"""
    auth_service.require_permission(
        platform_user, PermissionKey.GROUP_MODERATE
    )

    if message.chat.type not in ("group", "supergroup"):
        await message.answer("◈ This command works in groups only.")
        return

    args = message.text.split() if message.text else []
    # /mute @user 1h  or  /mute 123 30m
    args_text = args[1] if len(args) > 1 else None
    duration_text = args[2] if len(args) > 2 else None

    target = await resolve_target(message, bot, args_text)

    if target is None:
        await message.answer(
            f"{LINE}\n"
            f"◈ <b>Mute</b>\n"
            f"{LINE}\n\n"
            f"Reply + <code>/mute [30m|1h|2d]</code>\n"
            f"or: <code>/mute @user 1h</code>\n\n"
            f"<i>Default: 1 hour</i>",
            parse_mode="HTML",
        )
        return

    # If target was resolved from reply, duration could be in args[1]
    if message.reply_to_message and duration_text is None and args_text:
        duration_text = args_text

    duration = _parse_duration(duration_text)
    from datetime import datetime, timezone
    until = datetime.now(timezone.utc) + duration

    # Format duration
    total_mins = int(duration.total_seconds() / 60)
    if total_mins >= 1440:
        dur_str = f"{total_mins // 1440}d"
    elif total_mins >= 60:
        dur_str = f"{total_mins // 60}h"
    else:
        dur_str = f"{total_mins}m"

    try:
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=target.telegram_id,
            permissions=ChatPermissions(
                can_send_messages=False,
                can_send_media_messages=False,
                can_send_other_messages=False,
            ),
            until_date=until,
        )
        await message.answer(
            f"{LINE}\n"
            f"◈ <b>Muted</b>\n"
            f"{LINE}\n\n"
            f"▸ {target.display_tag}\n"
            f"  ◉ Duration: <b>{dur_str}</b>",
            parse_mode="HTML",
        )
    except Exception as e:
        await message.answer(f"◈ Failed to mute: <code>{e}</code>", parse_mode="HTML")


# ━━━ /unmute — unmute user ━━━

@router.message(Command("unmute"))
async def cmd_unmute(
    message: Message, platform_user: User, bot: Bot
) -> None:
    """Unmute user."""
    auth_service.require_permission(
        platform_user, PermissionKey.GROUP_MODERATE
    )

    if message.chat.type not in ("group", "supergroup"):
        await message.answer("◈ This command works in groups only.")
        return

    args = message.text.split(maxsplit=1) if message.text else []
    args_text = args[1] if len(args) > 1 else None
    target = await resolve_target(message, bot, args_text)

    if target is None:
        await message.answer(
            f"{LINE}\n"
            f"◈ <b>Unmute</b>\n"
            f"{LINE}\n\n"
            f"Reply to user or: <code>/unmute @user</code>",
            parse_mode="HTML",
        )
        return

    try:
        await bot.restrict_chat_member(
            chat_id=message.chat.id,
            user_id=target.telegram_id,
            permissions=ChatPermissions(
                can_send_messages=True,
                can_send_media_messages=True,
                can_send_other_messages=True,
                can_add_web_page_previews=True,
            ),
        )
        await message.answer(
            f"{LINE}\n"
            f"◈ <b>Unmuted</b>\n"
            f"{LINE}\n\n"
            f"▸ {target.display_tag}\n"
            f"  ◉ Can speak again",
            parse_mode="HTML",
        )
    except Exception as e:
        await message.answer(f"◈ Failed to unmute: <code>{e}</code>", parse_mode="HTML")


# ━━━ /kick — kick user (ban + unban) ━━━

@router.message(Command("kick"))
async def cmd_kick(
    message: Message, platform_user: User, bot: Bot
) -> None:
    """Kick user from group (ban + immediate unban)."""
    auth_service.require_permission(
        platform_user, PermissionKey.GROUP_MODERATE
    )

    if message.chat.type not in ("group", "supergroup"):
        await message.answer("◈ This command works in groups only.")
        return

    args = message.text.split(maxsplit=1) if message.text else []
    args_text = args[1] if len(args) > 1 else None
    target = await resolve_target(message, bot, args_text)

    if target is None:
        await message.answer(
            f"{LINE}\n"
            f"◈ <b>Kick</b>\n"
            f"{LINE}\n\n"
            f"Reply to user or: <code>/kick @user</code>",
            parse_mode="HTML",
        )
        return

    try:
        await bot.ban_chat_member(
            chat_id=message.chat.id,
            user_id=target.telegram_id,
        )
        await bot.unban_chat_member(
            chat_id=message.chat.id,
            user_id=target.telegram_id,
            only_if_banned=True,
        )
        await message.answer(
            f"{LINE}\n"
            f"◈ <b>Kicked</b>\n"
            f"{LINE}\n\n"
            f"▸ {target.display_tag}\n"
            f"  ◉ Removed (can rejoin)",
            parse_mode="HTML",
        )
    except Exception as e:
        await message.answer(f"◈ Failed to kick: <code>{e}</code>", parse_mode="HTML")


# ━━━ /pin — pin message ━━━

@router.message(Command("pin"))
async def cmd_pin(
    message: Message, platform_user: User, bot: Bot
) -> None:
    """Pin replied message."""
    auth_service.require_permission(
        platform_user, PermissionKey.GROUP_MODERATE
    )

    if not message.reply_to_message:
        await message.answer(
            "◈ Reply to a message to pin it."
        )
        return

    try:
        await bot.pin_chat_message(
            chat_id=message.chat.id,
            message_id=message.reply_to_message.message_id,
        )
        await message.answer("◈ Message pinned.")
    except Exception as e:
        await message.answer(f"◈ Failed to pin: <code>{e}</code>", parse_mode="HTML")


# ━━━ /unpin — unpin message ━━━

@router.message(Command("unpin"))
async def cmd_unpin(
    message: Message, platform_user: User, bot: Bot
) -> None:
    """Unpin replied message or latest pinned."""
    auth_service.require_permission(
        platform_user, PermissionKey.GROUP_MODERATE
    )

    try:
        if message.reply_to_message:
            await bot.unpin_chat_message(
                chat_id=message.chat.id,
                message_id=message.reply_to_message.message_id,
            )
        else:
            await bot.unpin_chat_message(chat_id=message.chat.id)
        await message.answer("◈ Message unpinned.")
    except Exception as e:
        await message.answer(f"◈ Failed to unpin: <code>{e}</code>", parse_mode="HTML")
