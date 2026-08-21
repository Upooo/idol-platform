"""Domain enumerations.

These enums define the vocabulary of the RBAC system.
They are referenced by domain models, services, and infrastructure.
"""

from __future__ import annotations

from enum import Enum, unique


@unique
class RoleType(str, Enum):
    """Built-in role types with fixed hierarchy."""

    FOUNDER = "founder"
    OWNER = "owner"
    ADMIN = "admin"
    WORKER = "worker"
    CUSTOMER = "customer"


ROLE_HIERARCHY: dict[RoleType, int] = {
    RoleType.FOUNDER: 1,
    RoleType.OWNER: 2,
    RoleType.ADMIN: 3,
    RoleType.WORKER: 4,
    RoleType.CUSTOMER: 5,
}


@unique
class PermissionKey(str, Enum):
    """Permission keys used in the RBAC system."""

    # ── Users
    USERS_VIEW = "users.view"
    USERS_CREATE = "users.create"
    USERS_UPDATE = "users.update"
    USERS_DELETE = "users.delete"

    # ── Staff
    STAFF_VIEW = "staff.view"
    STAFF_MANAGE = "staff.manage"

    # ── Roles
    ROLES_VIEW = "roles.view"
    ROLES_MANAGE = "roles.manage"
    ROLES_ASSIGN = "roles.assign"

    # ── Permissions
    PERMISSIONS_VIEW = "permissions.view"
    PERMISSIONS_MANAGE = "permissions.manage"

    # ── Group
    GROUP_MANAGE = "group.manage"        # promote, demote, settings
    GROUP_MODERATE = "group.moderate"    # ban, mute, kick, pin, delete
    GROUP_INVITE = "group.invite"

    # ── System
    SYSTEM_SETTINGS = "system.settings"
    SYSTEM_AUDIT = "system.audit"


@unique
class UserStatus(str, Enum):
    """User account status."""

    ACTIVE = "active"
    INACTIVE = "inactive"
    BANNED = "banned"


@unique
class AuditAction(str, Enum):
    """Auditable actions."""

    # Identity
    USER_CREATED = "user.created"
    USER_UPDATED = "user.updated"
    USER_BANNED = "user.banned"
    USER_UNBANNED = "user.unbanned"

    # Roles
    ROLE_ASSIGNED = "role.assigned"
    ROLE_REMOVED = "role.removed"

    # Permissions
    PERMISSION_GRANTED = "permission.granted"
    PERMISSION_REVOKED = "permission.revoked"

    # Group
    GROUP_BAN = "group.ban"
    GROUP_KICK = "group.kick"
    GROUP_PROMOTE = "group.promote"
    GROUP_DEMOTE = "group.demote"

    # Auth
    AUTH_DENIED = "auth.denied"

    # System
    SYSTEM_BOOTSTRAP = "system.bootstrap"
    FOUNDER_BOOTSTRAP = "founder.bootstrap"
