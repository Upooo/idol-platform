"""Target resolver — resolve a user from reply, @username, or telegram ID.

Used by assign, revoke, and group management commands to accept
multiple input formats for targeting a user.
"""

from __future__ import annotations

import re

import structlog
from aiogram import Bot
from aiogram.types import Message

log = structlog.get_logger()


class TargetInfo:
    """Resolved target user information."""

    def __init__(
        self,
        telegram_id: int,
        first_name: str | None = None,
        last_name: str | None = None,
        username: str | None = None,
    ) -> None:
        self.telegram_id = telegram_id
        self.first_name = first_name
        self.last_name = last_name
        self.username = username

    @property
    def full_name(self) -> str:
        parts = [p for p in (self.first_name, self.last_name) if p]
        return " ".join(parts) or self.username or str(self.telegram_id)

    @property
    def display_tag(self) -> str:
        """Formatted display: Name (@username) · ID."""
        name = self.full_name
        parts = [f"<b>{name}</b>"]
        if self.username:
            parts.append(f"(@{self.username})")
        parts.append(f"· <code>{self.telegram_id}</code>")
        return " ".join(parts)


async def resolve_target(
    message: Message,
    bot: Bot,
    args_text: str | None = None,
) -> TargetInfo | None:
    """Resolve target user from:
    1. Reply to a message (highest priority)
    2. @username argument
    3. Numeric telegram ID argument

    Returns TargetInfo or None if unresolvable.
    """
    # 1. Reply
    if message.reply_to_message and message.reply_to_message.from_user:
        u = message.reply_to_message.from_user
        return TargetInfo(
            telegram_id=u.id,
            first_name=u.first_name,
            last_name=u.last_name,
            username=u.username,
        )

    # 2. Parse args
    if not args_text:
        return None

    arg = args_text.strip().split()[0] if args_text.strip() else ""
    if not arg:
        return None

    # @username
    if arg.startswith("@"):
        username = arg[1:]
        # Try to get chat info via bot
        try:
            chat = await bot.get_chat(f"@{username}")
            return TargetInfo(
                telegram_id=chat.id,
                first_name=chat.first_name,
                last_name=chat.last_name,
                username=chat.username,
            )
        except Exception:
            log.debug("username_resolve_failed", username=username)
            return None

    # Numeric ID
    if re.match(r"^\d+$", arg):
        tg_id = int(arg)
        # Try to get user info
        try:
            chat = await bot.get_chat(tg_id)
            return TargetInfo(
                telegram_id=chat.id,
                first_name=chat.first_name,
                last_name=chat.last_name,
                username=chat.username,
            )
        except Exception:
            # User exists but bot can't resolve — return with ID only
            return TargetInfo(telegram_id=tg_id)

    return None
