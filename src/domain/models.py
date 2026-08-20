"""Domain models.

Pure data structures representing the core business entities.
No framework dependencies, no database logic.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

from src.domain.enums import (
    AuditAction,
    PermissionKey,
    RoleType,
    UserStatus,
)


@dataclass
class User:
    """A platform user identified by Telegram ID."""

    id: UUID
    telegram_id: int
    username: str | None = None
    first_name: str | None = None
    last_name: str | None = None
    status: UserStatus = UserStatus.ACTIVE
    created_at: datetime | None = None
    updated_at: datetime | None = None

    # Populated by services, not stored directly
    roles: list[Role] = field(default_factory=list)
    permissions: set[PermissionKey] = field(default_factory=set)

    @property
    def full_name(self) -> str:
        parts = [p for p in (self.first_name, self.last_name) if p]
        return " ".join(parts) or self.username or str(self.telegram_id)

    @property
    def is_founder(self) -> bool:
        return any(r.role_type == RoleType.FOUNDER for r in self.roles)

    @property
    def highest_role(self) -> Role | None:
        """Return the role with the lowest hierarchy_level (= highest authority)."""
        if not self.roles:
            return None
        from src.domain.enums import ROLE_HIERARCHY
        return min(self.roles, key=lambda r: ROLE_HIERARCHY.get(r.role_type, 999))

    def has_permission(self, perm: PermissionKey) -> bool:
        """Check if user has a specific permission.

        Founder has ALL permissions implicitly.
        Everyone else must have the permission explicitly assigned.
        """
        if self.is_founder:
            return True
        return perm in self.permissions


@dataclass
class Role:
    """A role in the RBAC system."""

    id: UUID
    role_type: RoleType
    description: str | None = None
    created_at: datetime | None = None

    # Populated by services
    permissions: set[PermissionKey] = field(default_factory=set)


@dataclass
class AuditEntry:
    """An audit log entry."""

    id: UUID
    actor_id: UUID | None  # None for system actions
    action: AuditAction
    target_type: str | None = None  # 'user', 'role', etc.
    target_id: str | None = None
    metadata: dict | None = None  # JSONB — no secrets
    created_at: datetime | None = None
