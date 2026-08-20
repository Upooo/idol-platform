"""Audit service — convenience wrapper for audit logging."""

from __future__ import annotations

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.enums import AuditAction
from src.infrastructure.database.repositories import AuditRepository


class AuditService:
    """Thin wrapper around AuditRepository for use in handlers."""

    def __init__(self, session: AsyncSession) -> None:
        self._repo = AuditRepository(session)

    async def log(
        self,
        action: AuditAction,
        actor_id: uuid.UUID | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        await self._repo.log(
            action=action.value,
            actor_id=actor_id,
            target_type=target_type,
            target_id=target_id,
            metadata=metadata,
        )
