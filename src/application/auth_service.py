"""Authorization service — RBAC enforcement.

Centralized permission + hierarchy + founder protection checks.
Handlers call this instead of checking roles directly.
"""

from __future__ import annotations

import uuid

from src.domain.enums import ROLE_HIERARCHY, PermissionKey, RoleType
from src.domain.exceptions import (
    FounderProtectionError,
    PermissionDeniedError,
    RoleHierarchyError,
)
from src.domain.models import User


def require_permission(actor: User, permission: PermissionKey) -> None:
    """Raise PermissionDeniedError if actor lacks the permission."""
    if not actor.has_permission(permission):
        raise PermissionDeniedError(permission.value)


def check_hierarchy(actor: User, target: User) -> None:
    """Raise RoleHierarchyError if actor cannot manage target.

    Rule: actor's highest role must have a LOWER level number
    (= higher authority) than target's highest role.
    Equal levels cannot manage each other.
    """
    actor_role = actor.highest_role
    target_role = target.highest_role

    if actor_role is None:
        raise RoleHierarchyError("Actor has no role")

    actor_level = ROLE_HIERARCHY.get(actor_role.role_type, 999)

    if target_role is None:
        # Target has no role — anyone with a role can manage
        return

    target_level = ROLE_HIERARCHY.get(target_role.role_type, 999)

    if actor_level >= target_level:
        raise RoleHierarchyError(
            f"Cannot manage role at level {target_level} "
            f"(your level: {actor_level})"
        )


def check_founder_protection(target: User) -> None:
    """Raise FounderProtectionError if target is the Founder.

    V1: Founder cannot be deleted, demoted, transferred,
    or modified via normal bot operations.
    """
    if target.is_founder:
        raise FounderProtectionError(
            "Founder identity is protected and cannot be modified."
        )


def authorize_role_change(
    actor: User,
    target: User,
    permission: PermissionKey,
) -> None:
    """Full authorization check for role management operations.

    Combines: permission check + founder protection + hierarchy check.
    """
    require_permission(actor, permission)
    check_founder_protection(target)
    check_hierarchy(actor, target)
