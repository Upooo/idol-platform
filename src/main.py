"""IDOL Platform — Entry Point."""

import asyncio
import sys

import structlog

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

    log.info("idol_platform_ready", founder_id=settings.founder_telegram_id)

    # Phase 5+: bot startup will go here
    log.info("no_bot_yet", hint="Phase 5+ will add bot startup")

    # --- Shutdown ---
    from src.infrastructure.database.engine import dispose_engine

    await dispose_engine()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        log.info("shutdown")
        sys.exit(0)
