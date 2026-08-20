"""IDOL Platform — Entry Point."""

import asyncio
import sys

import structlog

from src.config import settings

log = structlog.get_logger()


async def main() -> None:
    """Application bootstrap."""
    log.info(
        "starting",
        app=settings.app_name,
        env=settings.app_env,
        debug=settings.debug,
    )

    log.info("idol_platform_ready", founder_id=settings.founder_telegram_id)
    log.info("no_bot_yet", hint="Phase 2+ will add database and bot startup")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("shutdown")
        sys.exit(0)
