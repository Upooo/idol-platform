"""Identity service — user lifecycle and founder bootstrap."""

from __future__ import annotations

import structlog

from src.config import settings
from src.domain.enums import AuditAction, RoleType
from src.infrastructure.database.engine import get_session_factory
from src.infrastructure.database.repositories import (
    AuditRepository,
    RoleRepository,
    UserRepository,
)

log = structlog.get_logger()


async def bootstrap_founder() -> None:
    """Ensure the Founder user exists and has the Founder role.

    This runs on every application startup. It is idempotent:
    - If the user doesn't exist, create it.
    - If the user exists but lacks the Founder role, assign it.
    - If everything is already in place, do nothing.

    The Founder is identified EXCLUSIVELY by FOUNDER_TELEGRAM_ID.
    """
    session_factory = get_session_factory()
    async with session_factory() as session:
        async with session.begin():
            user_repo = UserRepository(session)
            role_repo = RoleRepository(session)
            audit_repo = AuditRepository(session)

            founder_tg_id = settings.founder_telegram_id

            # Find or create user
            user = await user_repo.get_by_telegram_id(founder_tg_id)
            if user is None:
                user = await user_repo.create(
                    telegram_id=founder_tg_id,
                    first_name="Founder",
                )
                log.info("founder_user_created", telegram_id=founder_tg_id)

            # Find founder role
            founder_role = await role_repo.get_by_name(RoleType.FOUNDER.value)
            if founder_role is None:
                log.error(
                    "founder_role_missing",
                    hint="Run migrations first: make migrate",
                )
                return

            # Assign founder role if not already assigned
            has_founder = await role_repo.has_role(
                user.id, RoleType.FOUNDER.value
            )
            if not has_founder:
                await role_repo.assign_role(
                    user_id=user.id,
                    role_id=founder_role.id,
                    assigned_by=None,  # System action
                )
                await audit_repo.log(
                    action=AuditAction.FOUNDER_BOOTSTRAP.value,
                    target_type="user",
                    target_id=str(user.telegram_id),
                    metadata={"telegram_id": founder_tg_id},
                )
                log.info(
                    "founder_role_assigned",
                    telegram_id=founder_tg_id,
                    user_id=str(user.id),
                )
            else:
                log.info(
                    "founder_already_bootstrapped",
                    telegram_id=founder_tg_id,
                )


async def bootstrap_owners() -> None:
    """Ensure pre-configured Owner users exist and have the Owner role.

    Owner Telegram IDs come from OWNER_TELEGRAM_IDS in config.
    This is optional and idempotent.
    """
    if not settings.owner_telegram_ids:
        return

    session_factory = get_session_factory()
    async with session_factory() as session:
        async with session.begin():
            user_repo = UserRepository(session)
            role_repo = RoleRepository(session)
            audit_repo = AuditRepository(session)

            owner_role = await role_repo.get_by_name(RoleType.OWNER.value)
            if owner_role is None:
                log.error("owner_role_missing")
                return

            # Get founder user for assigned_by
            founder_user = await user_repo.get_by_telegram_id(
                settings.founder_telegram_id
            )

            for tg_id in settings.owner_telegram_ids:
                if tg_id == settings.founder_telegram_id:
                    continue  # Founder is not an Owner

                user = await user_repo.get_by_telegram_id(tg_id)
                if user is None:
                    user = await user_repo.create(telegram_id=tg_id)
                    log.info("owner_user_created", telegram_id=tg_id)

                has_owner = await role_repo.has_role(
                    user.id, RoleType.OWNER.value
                )
                if not has_owner:
                    await role_repo.assign_role(
                        user_id=user.id,
                        role_id=owner_role.id,
                        assigned_by=(
                            founder_user.id if founder_user else None
                        ),
                    )
                    await audit_repo.log(
                        action=AuditAction.ROLE_ASSIGNED.value,
                        actor_id=(
                            founder_user.id if founder_user else None
                        ),
                        target_type="user",
                        target_id=str(user.telegram_id),
                        metadata={
                            "role": RoleType.OWNER.value,
                            "source": "env_bootstrap",
                        },
                    )
                    log.info(
                        "owner_role_assigned",
                        telegram_id=tg_id,
                    )
