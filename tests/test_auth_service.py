"""Test auth service — permission, hierarchy, founder protection."""

import uuid

import pytest

from src.domain.enums import PermissionKey, RoleType
from src.domain.exceptions import (
    FounderProtectionError,
    PermissionDeniedError,
    RoleHierarchyError,
)
from src.domain.models import Role, User
from src.application.auth_service import (
    authorize_role_change,
    check_founder_protection,
    check_hierarchy,
    require_permission,
)


def _user(
    role_type: RoleType | None = None,
    permissions: set[PermissionKey] | None = None,
) -> User:
    roles = [Role(id=uuid.uuid4(), role_type=role_type)] if role_type else []
    return User(
        id=uuid.uuid4(),
        telegram_id=1,
        roles=roles,
        permissions=permissions or set(),
    )


# --- require_permission ---

def test_founder_always_passes_permission():
    founder = _user(RoleType.FOUNDER)
    require_permission(founder, PermissionKey.SYSTEM_SETTINGS)


def test_explicit_permission_passes():
    owner = _user(RoleType.OWNER, {PermissionKey.STAFF_MANAGE})
    require_permission(owner, PermissionKey.STAFF_MANAGE)


def test_missing_permission_raises():
    owner = _user(RoleType.OWNER)
    with pytest.raises(PermissionDeniedError):
        require_permission(owner, PermissionKey.SYSTEM_SETTINGS)


# --- check_hierarchy ---

def test_founder_can_manage_owner():
    founder = _user(RoleType.FOUNDER)
    owner = _user(RoleType.OWNER)
    check_hierarchy(founder, owner)  # Should not raise


def test_owner_cannot_manage_founder():
    owner = _user(RoleType.OWNER)
    founder = _user(RoleType.FOUNDER)
    with pytest.raises(RoleHierarchyError):
        check_hierarchy(owner, founder)


def test_same_level_cannot_manage():
    admin1 = _user(RoleType.ADMIN)
    admin2 = _user(RoleType.ADMIN)
    with pytest.raises(RoleHierarchyError):
        check_hierarchy(admin1, admin2)


def test_higher_can_manage_lower():
    owner = _user(RoleType.OWNER)
    worker = _user(RoleType.WORKER)
    check_hierarchy(owner, worker)  # Should not raise


# --- check_founder_protection ---

def test_founder_is_protected():
    founder = _user(RoleType.FOUNDER)
    with pytest.raises(FounderProtectionError):
        check_founder_protection(founder)


def test_non_founder_not_protected():
    owner = _user(RoleType.OWNER)
    check_founder_protection(owner)  # Should not raise


# --- authorize_role_change (combined) ---

def test_authorize_full_pass():
    """Founder changing a Worker's role: permission + hierarchy + protection all pass."""
    founder = _user(RoleType.FOUNDER)
    worker = _user(RoleType.WORKER)
    authorize_role_change(founder, worker, PermissionKey.ROLES_ASSIGN)


def test_authorize_fails_on_permission():
    worker = _user(RoleType.WORKER)
    customer = _user(RoleType.CUSTOMER)
    with pytest.raises(PermissionDeniedError):
        authorize_role_change(worker, customer, PermissionKey.ROLES_ASSIGN)


def test_authorize_fails_on_founder_target():
    """Even a Founder trying to modify themselves via normal ops is blocked."""
    founder = _user(RoleType.FOUNDER)
    founder2 = _user(RoleType.FOUNDER)
    with pytest.raises(FounderProtectionError):
        authorize_role_change(founder, founder2, PermissionKey.ROLES_ASSIGN)
