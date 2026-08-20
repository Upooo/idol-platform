"""Notification service — send messages to IDOL TEAM group topics.

Centralized routing for all bot-to-group notifications.
All notifications go through here, never directly via bot.send_message.
"""

from __future__ import annotations

import structlog
from aiogram import Bot

from src.config import settings

log = structlog.get_logger()


class NotificationService:
    """Send notifications to IDOL TEAM group topics."""

    def __init__(self, bot: Bot) -> None:
        self._bot = bot

    async def _send_to_topic(
        self,
        topic_id: int | None,
        text: str,
        fallback_topic: str = "system",
    ) -> bool:
        """Send a message to a specific forum topic.

        Returns True if sent successfully, False if topic not configured.
        """
        if not settings.has_team_group:
            log.debug("notification_skipped", reason="no_team_group")
            return False

        if topic_id is None:
            log.debug(
                "notification_skipped",
                reason=f"topic_{fallback_topic}_not_configured",
            )
            return False

        try:
            await self._bot.send_message(
                chat_id=settings.idol_team_group_id,  # type: ignore
                message_thread_id=topic_id,
                text=text,
                parse_mode="HTML",
            )
            return True
        except Exception:
            log.exception(
                "notification_failed",
                topic=fallback_topic,
                topic_id=topic_id,
            )
            return False

    async def notify_system(self, text: str) -> bool:
        """Send to #system topic."""
        return await self._send_to_topic(
            settings.topic_system_id, text, "system"
        )

    async def notify_orders(self, text: str) -> bool:
        """Send to #orders topic."""
        return await self._send_to_topic(
            settings.topic_orders_id, text, "orders"
        )

    async def notify_staff(self, text: str) -> bool:
        """Send to #staff topic."""
        return await self._send_to_topic(
            settings.topic_staff_id, text, "staff"
        )

    async def send_startup_notification(self) -> None:
        """Announce bot startup to system topic."""
        text = (
            "🟢 <b>IDOL Platform Online</b>\n\n"
            f"Environment: <b>{settings.app_env}</b>\n"
            f"Bot: @{settings.hq_bot_username}\n"
            f"AI: {'Enabled' if settings.enable_ai else 'Disabled'}"
        )
        sent = await self.notify_system(text)
        if sent:
            log.info("startup_notification_sent")
