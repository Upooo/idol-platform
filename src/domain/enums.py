"""Domain enumerations.

These enums define the vocabulary of the RBAC system.
They are referenced by domain models, services, and infrastructure.
"""

from __future__ import annotations

from enum import Enum, unique


@unique
class RoleType(str, Enum):
    """Built-in role types with fixed hierarchy.

    hierarchy_level determines the ceiling of authority:
    - A user can only manage roles with a HIGHER level number
      (lower authority) than their own highest role.
    - Founder (level 1) can manage everyone.
    - Roles at the same level cannot manage each other.
    """

    FOUNDER = "founder"
    OWNER = "owner"
    ADMIN = "admin"
    WORKER = "worker"
    CUSTOMER = "customer"


# Fixed hierarchy levels — not configurable at runtime.
# Lower number = higher authority.
ROLE_HIERARCHY: dict[RoleType, int] = {
    RoleType.FOUNDER: 1,
    RoleType.OWNER: 2,
    RoleType.ADMIN: 3,
    RoleType.WORKER: 4,
    RoleType.CUSTOMER: 5,
}


@unique
class PermissionKey(str, Enum):
    """Permission keys used in the RBAC system.

    Permissions are explicit and granular.
    A role has ONLY the permissions assigned to it via role_permissions.
    Founder is the sole exception: Founder has ALL permissions implicitly.

    Naming convention: <resource>.<action>
    """

    # ── Users ─────────────────────────────────────
    USERS_VIEW = "users.view"
    USERS_CREATE = "users.create"
    USERS_UPDATE = "users.update"
    USERS_DELETE = "users.delete"

    # ── Staff ─────────────────────────────────────
    STAFF_VIEW = "staff.view"
    STAFF_MANAGE = "staff.manage"        # assign/remove staff roles

    # ── Roles ─────────────────────────────────────
    ROLES_VIEW = "roles.view"
    ROLES_MANAGE = "roles.manage"        # create/edit/delete roles
    ROLES_ASSIGN = "roles.assign"        # assign roles to users

    # ── Permissions ───────────────────────────────
    PERMISSIONS_VIEW = "permissions.view"
    PERMISSIONS_MANAGE = "permissions.manage"  # edit role-permission mappings

    # ── Group ─────────────────────────────────────
    GROUP_MANAGE = "group.manage"        # group settings, title, description
    GROUP_MODERATE = "group.moderate"    # ban, mute, warn, delete messages
    GROUP_INVITE = "group.invite"        # create invite links

    # ── System ────────────────────────────────────
    SYSTEM_SETTINGS = "system.settings"  # bot-level settings
    SYSTEM_AUDIT = "system.audit"        # view audit logs


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

    # Auth
    AUTH_DENIED = "auth.denied"

    # System
    SYSTEM_BOOTSTRAP = "system.bootstrap"
    FOUNDER_BOOTSTRAP = "founder.bootstrap"
