"""IDOL Platform — Entry Point.

Full application bootstrap: logging, database, founder bootstrap, bot startup.
"""

import asyncio
import sys

import structlog
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from src.config import settings
from src.infrastructure.logging import setup_logging

log = structlog.get_logger()


async def main() -> None:
    """Application bootstrap."""
    setup_logging(
        log_level=settings.log_level,
        json_output=settings.is_production,
    )

    log.info(
        "starting",
        app=settings.app_name,
        env=settings.app_env,
        debug=settings.debug,
    )

    # --- Database bootstrap ---
    from src.application.identity_service import (
        bootstrap_founder,
        bootstrap_owners,
    )

    await bootstrap_founder()
    await bootstrap_owners()
    log.info("identity_bootstrap_complete")

    # --- Bot setup ---
    bot = Bot(
        token=settings.hq_bot_token.get_secret_value(),
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()

    # Register middlewares
    from src.presentation.middlewares.auth import AuthMiddleware
    from src.presentation.middlewares.error import ErrorMiddleware

    dp.message.middleware(ErrorMiddleware())
    dp.message.middleware(AuthMiddleware())
    dp.callback_query.middleware(ErrorMiddleware())
    dp.callback_query.middleware(AuthMiddleware())

    # Register routers
    from src.presentation.handlers.start import router as start_router

    dp.include_router(start_router)

    # --- Start polling ---
    log.info(
        "bot_starting",
        username=settings.hq_bot_username,
        founder_id=settings.founder_telegram_id,
    )

    try:
        await dp.start_polling(bot)
    finally:
        log.info("shutting_down")
        from src.infrastructure.database.engine import dispose_engine

        await dispose_engine()
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("shutdown")
        sys.exit(0)
