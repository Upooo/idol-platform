"""Group management handlers — promote, demote, ban, mute, kick, info, pin."""

from __future__ import annotations

import re
from datetime import timedelta

import structlog
from aiogram import Bot, Router
from aiogram.filters import Command
from aiogram.types import ChatPermissions, Message

from src.application import auth_service
from src.application.target_resolver import resolve_target
from src.domain.enums import PermissionKey
from src.domain.models import User

log = structlog.get_logger()
router = Router(name="group")


def _parse_duration(text: str | None) -> timedelta:
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


def _group_only_msg() -> str:
    return "This command works in groups only."


def _fmt_duration(d: timedelta) -> str:
    total_mins = int(d.total_seconds() / 60)
    if total_mins >= 1440:
        return f"{total_mins // 1440}d"
    elif total_mins >= 60:
        return f"{total_mins // 60}h"
    return f"{total_mins}m"


# ━━━ /id ━━━

@router.message(Command("id"))
async def cmd_id(message: Message, platform_user: User) -> None:
    lines = []

    # Own
    uname = f" · @{platform_user.username}" if platform_user.username else ""
    lines.append(f"You: <code>{platform_user.telegram_id}</code>{uname}")

    # Replied
    if message.reply_to_message and message.reply_to_message.from_user:
        ru = message.reply_to_message.from_user
        name = ru.first_name or ru.username or str(ru.id)
        ru_uname = f" · @{ru.username}" if ru.username else ""
        lines.append(f"\nReply: <b>{name}</b>{ru_uname}")
        lines.append(f"ID: <code>{ru.id}</code>")

    # Group
    if message.chat.type in ("group", "supergroup"):
        lines.append(f"\nGroup: <b>{message.chat.title}</b>")
        lines.append(f"ID: <code>{message.chat.id}</code>")
    elif message.chat.type == "private":
        lines.append(f"\nChat: Private")

    await message.answer("\n".join(lines), parse_mode="HTML")


# ━━━ /info ━━━

@router.message(Command("info"))
async def cmd_info(
    message: Message, platform_user: User, bot: Bot
) -> None:
    if message.chat.type not in ("group", "supergroup"):
        await message.answer(_group_only_msg())
        return

    chat = await bot.get_chat(message.chat.id)
    member_count = await bot.get_chat_member_count(message.chat.id)
    admins = await bot.get_chat_administrators(message.chat.id)
    admin_count = len([a for a in admins if not a.user.is_bot])
    bot_count = len([a for a in admins if a.user.is_bot])

    lines = [
        f"ℹ️ <b>{chat.title}</b>\n",
        f"ID: <code>{chat.id}</code>",
        f"Type: {chat.type}",
        f"Members: {member_count}",
        f"Admins: {admin_count} · Bots: {bot_count}",
    ]

    if chat.description:
        lines.append(f"\n<i>{chat.description[:200]}</i>")

    await message.answer("\n".join(lines), parse_mode="HTML")


# ━━━ /promote ━━━

@router.message(Command("promote"))
async def cmd_promote(
    message: Message, platform_user: User, bot: Bot
) -> None:
    auth_service.require_permission(
        platform_user, PermissionKey.GROUP_MANAGE
    )

    if message.chat.type not in ("group", "supergroup"):
        await message.answer(_group_only_msg())
        return

    args = message.text.split(maxsplit=1) if message.text else []
    target = await resolve_target(message, bot, args[1] if len(args) > 1 else None)

    if target is None:
        await message.answer(
            "<b>Promote</b>\n\n"
            "Reply to user or <code>/promote @user</code>",
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
            f"✅ <b>Promoted</b>\n\n"
            f"{target.display_tag}\n"
            f"→ Group Admin",
            parse_mode="HTML",
        )
    except Exception as e:
        log.exception("promote_failed")
        await message.answer(
            "⚠️ Couldn't promote this user.\n\n"
            "<i>Check bot permissions and try again.</i>",
            parse_mode="HTML",
        )


# ━━━ /demote ━━━

@router.message(Command("demote"))
async def cmd_demote(
    message: Message, platform_user: User, bot: Bot
) -> None:
    auth_service.require_permission(
        platform_user, PermissionKey.GROUP_MANAGE
    )

    if message.chat.type not in ("group", "supergroup"):
        await message.answer(_group_only_msg())
        return

    args = message.text.split(maxsplit=1) if message.text else []
    target = await resolve_target(message, bot, args[1] if len(args) > 1 else None)

    if target is None:
        await message.answer(
            "<b>Demote</b>\n\n"
            "Reply to user or <code>/demote @user</code>",
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
            f"✅ <b>Demoted</b>\n\n"
            f"{target.display_tag}\n"
            f"→ Member",
            parse_mode="HTML",
        )
    except Exception as e:
        log.exception("demote_failed")
        await message.answer(
            "⚠️ Couldn't demote this user.\n\n"
            "<i>Check bot permissions and try again.</i>",
            parse_mode="HTML",
        )


# ━━━ /ban ━━━

@router.message(Command("ban"))
async def cmd_ban(
    message: Message, platform_user: User, bot: Bot
) -> None:
    auth_service.require_permission(
        platform_user, PermissionKey.GROUP_MODERATE
    )

    if message.chat.type not in ("group", "supergroup"):
        await message.answer(_group_only_msg())
        return

    args = message.text.split(maxsplit=1) if message.text else []
    target = await resolve_target(message, bot, args[1] if len(args) > 1 else None)

    if target is None:
        await message.answer(
            "<b>Ban</b>\n\nReply to user or <code>/ban @user</code>",
            parse_mode="HTML",
        )
        return

    try:
        await bot.ban_chat_member(
            chat_id=message.chat.id,
            user_id=target.telegram_id,
        )
        await message.answer(
            f"🚫 <b>Banned</b>\n\n"
            f"{target.display_tag}\n"
            f"Removed from group.",
            parse_mode="HTML",
        )
    except Exception as e:
        log.exception("ban_failed")
        await message.answer(
            "⚠️ Couldn't ban this user.\n\n"
            "<i>Check bot permissions and try again.</i>",
            parse_mode="HTML",
        )


# ━━━ /unban ━━━

@router.message(Command("unban"))
async def cmd_unban(
    message: Message, platform_user: User, bot: Bot
) -> None:
    auth_service.require_permission(
        platform_user, PermissionKey.GROUP_MODERATE
    )

    if message.chat.type not in ("group", "supergroup"):
        await message.answer(_group_only_msg())
        return

    args = message.text.split(maxsplit=1) if message.text else []
    target = await resolve_target(message, bot, args[1] if len(args) > 1 else None)

    if target is None:
        await message.answer(
            "<b>Unban</b>\n\n"
            "<code>/unban @user</code> or <code>/unban 123456789</code>",
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
            f"✅ <b>Unbanned</b>\n\n"
            f"{target.display_tag}\n"
            f"Can rejoin the group.",
            parse_mode="HTML",
        )
    except Exception as e:
        log.exception("unban_failed")
        await message.answer(
            "⚠️ Couldn't unban this user.\n\n"
            "<i>Check bot permissions and try again.</i>",
            parse_mode="HTML",
        )


# ━━━ /mute ━━━

@router.message(Command("mute"))
async def cmd_mute(
    message: Message, platform_user: User, bot: Bot
) -> None:
    auth_service.require_permission(
        platform_user, PermissionKey.GROUP_MODERATE
    )

    if message.chat.type not in ("group", "supergroup"):
        await message.answer(_group_only_msg())
        return

    args = message.text.split() if message.text else []
    args_text = args[1] if len(args) > 1 else None
    duration_text = args[2] if len(args) > 2 else None

    target = await resolve_target(message, bot, args_text)

    if target is None:
        await message.answer(
            "🔇 <b>Mute</b>\n\n"
            "Reply + <code>/mute [30m|1h|2d]</code>\n"
            "or <code>/mute @user 1h</code>\n\n"
            "<i>Default: 1 hour</i>",
            parse_mode="HTML",
        )
        return

    if message.reply_to_message and duration_text is None and args_text:
        duration_text = args_text

    duration = _parse_duration(duration_text)
    from datetime import datetime, timezone
    until = datetime.now(timezone.utc) + duration

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
            f"🔇 <b>Muted</b>\n\n"
            f"{target.display_tag}\n"
            f"Duration: {_fmt_duration(duration)}",
            parse_mode="HTML",
        )
    except Exception as e:
        log.exception("mute_failed")
        await message.answer(
            "⚠️ Couldn't mute this user.\n\n"
            "<i>Check bot permissions and try again.</i>",
            parse_mode="HTML",
        )


# ━━━ /unmute ━━━

@router.message(Command("unmute"))
async def cmd_unmute(
    message: Message, platform_user: User, bot: Bot
) -> None:
    auth_service.require_permission(
        platform_user, PermissionKey.GROUP_MODERATE
    )

    if message.chat.type not in ("group", "supergroup"):
        await message.answer(_group_only_msg())
        return

    args = message.text.split(maxsplit=1) if message.text else []
    target = await resolve_target(message, bot, args[1] if len(args) > 1 else None)

    if target is None:
        await message.answer(
            "<b>Unmute</b>\n\nReply to user or <code>/unmute @user</code>",
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
            f"🔊 <b>Unmuted</b>\n\n"
            f"{target.display_tag}",
            parse_mode="HTML",
        )
    except Exception as e:
        log.exception("unmute_failed")
        await message.answer(
            "⚠️ Couldn't unmute this user.\n\n"
            "<i>Check bot permissions and try again.</i>",
            parse_mode="HTML",
        )


# ━━━ /kick ━━━

@router.message(Command("kick"))
async def cmd_kick(
    message: Message, platform_user: User, bot: Bot
) -> None:
    auth_service.require_permission(
        platform_user, PermissionKey.GROUP_MODERATE
    )

    if message.chat.type not in ("group", "supergroup"):
        await message.answer(_group_only_msg())
        return

    args = message.text.split(maxsplit=1) if message.text else []
    target = await resolve_target(message, bot, args[1] if len(args) > 1 else None)

    if target is None:
        await message.answer(
            "<b>Kick</b>\n\nReply to user or <code>/kick @user</code>",
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
            f"👢 <b>Kicked</b>\n\n"
            f"{target.display_tag}\n"
            f"Removed. Can rejoin.",
            parse_mode="HTML",
        )
    except Exception as e:
        log.exception("kick_failed")
        await message.answer(
            "⚠️ Couldn't kick this user.\n\n"
            "<i>Check bot permissions and try again.</i>",
            parse_mode="HTML",
        )


# ━━━ /pin ━━━

@router.message(Command("pin"))
async def cmd_pin(
    message: Message, platform_user: User, bot: Bot
) -> None:
    auth_service.require_permission(
        platform_user, PermissionKey.GROUP_MODERATE
    )

    if not message.reply_to_message:
        await message.answer("Reply to a message to pin it.")
        return

    try:
        await bot.pin_chat_message(
            chat_id=message.chat.id,
            message_id=message.reply_to_message.message_id,
        )
        await message.answer("📌 Pinned.")
    except Exception as e:
        log.exception("pin_failed")
        await message.answer(
            "⚠️ Couldn't pin this message.\n\n"
            "<i>Check bot permissions and try again.</i>",
            parse_mode="HTML",
        )


# ━━━ /unpin ━━━

@router.message(Command("unpin"))
async def cmd_unpin(
    message: Message, platform_user: User, bot: Bot
) -> None:
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
        await message.answer("📌 Unpinned.")
    except Exception as e:
        log.exception("unpin_failed")
        await message.answer(
            "⚠️ Couldn't unpin.\n\n"
            "<i>Check bot permissions and try again.</i>",
            parse_mode="HTML",
        )
