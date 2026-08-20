"""Audit repository — data access for audit_logs table."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.tables import AuditLogTable


class AuditRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def log(
        self,
        action: str,
        actor_id: uuid.UUID | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
        metadata: dict | None = None,
    ) -> AuditLogTable:
        entry = AuditLogTable(
            id=uuid.uuid4(),
            actor_id=actor_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            metadata_=metadata,
            created_at=datetime.now(timezone.utc),
        )
        self._session.add(entry)
        await self._session.flush()
        return entry
