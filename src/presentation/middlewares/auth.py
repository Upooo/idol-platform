"""Auth middleware — injects platform User into every handler.

Runs before every message/callback. Resolves the Telegram user
to a hydrated platform User with roles and permissions,
then stores it in handler data as `platform_user`.
"""

from __future__ import annotations

from typing import Any, Awaitable, Callable

import structlog
from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from src.infrastructure.database.engine import get_session_factory
from src.application.user_resolver import resolve_user

log = structlog.get_logger()


class AuthMiddleware(BaseMiddleware):
    """Resolve Telegram user → platform User on every request."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        # Extract Telegram user from event
        tg_user = None
        if isinstance(event, Message) and event.from_user:
            tg_user = event.from_user
        elif isinstance(event, CallbackQuery) and event.from_user:
            tg_user = event.from_user

        if tg_user is None:
            return await handler(event, data)

        # Resolve to platform user with roles + permissions
        session_factory = get_session_factory()
        async with session_factory() as session:
            async with session.begin():
                platform_user = await resolve_user(
                    session=session,
                    telegram_id=tg_user.id,
                    username=tg_user.username,
                    first_name=tg_user.first_name,
                    last_name=tg_user.last_name,
                )

            data["platform_user"] = platform_user
            data["db_session_factory"] = session_factory

            return await handler(event, data)
