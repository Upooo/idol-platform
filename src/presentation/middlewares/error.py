"""Error handler middleware — catches domain exceptions."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

import structlog
from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message, TelegramObject

from src.domain.exceptions import (
    DomainError,
    FounderProtectionError,
    PermissionDeniedError,
    RoleHierarchyError,
)

log = structlog.get_logger()

ERROR_MESSAGES = {
    PermissionDeniedError: "⚠️ You don't have permission for this.",
    RoleHierarchyError: "⚠️ Can't manage users at or above your role.",
    FounderProtectionError: "⚠️ Founder identity is protected.",
}


class ErrorMiddleware(BaseMiddleware):
    """Catch domain exceptions and show user-friendly messages."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        try:
            return await handler(event, data)
        except DomainError as e:
            msg = ERROR_MESSAGES.get(type(e), f"⚠️ {e}")
            log.warning(
                "domain_error",
                error_type=type(e).__name__,
                detail=str(e),
            )

            if isinstance(event, Message):
                await event.answer(msg)
            elif isinstance(event, CallbackQuery):
                await event.answer(msg, show_alert=True)

            return None
        except Exception:
            log.exception("unhandled_error")

            msg = (
                "⚠️ Something went wrong.\n\n"
                "Please try again."
            )

            if isinstance(event, Message):
                await event.answer(msg)
            elif isinstance(event, CallbackQuery):
                await event.answer("Something went wrong.", show_alert=True)

            return None
