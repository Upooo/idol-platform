"""Test domain models — User permission logic."""

import uuid

from src.domain.enums import PermissionKey, RoleType
from src.domain.models import Role, User


def _make_role(role_type: RoleType) -> Role:
    return Role(id=uuid.uuid4(), role_type=role_type)


def test_founder_has_all_permissions():
    """Founder has implicit ALL permissions."""
    user = User(
        id=uuid.uuid4(),
        telegram_id=123,
        roles=[_make_role(RoleType.FOUNDER)],
    )
    assert user.is_founder is True
    assert user.has_permission(PermissionKey.USERS_VIEW) is True
    assert user.has_permission(PermissionKey.SYSTEM_SETTINGS) is True
    assert user.has_permission(PermissionKey.PERMISSIONS_MANAGE) is True


def test_non_founder_needs_explicit_permission():
    """Non-founder requires explicit permission."""
    user = User(
        id=uuid.uuid4(),
        telegram_id=456,
        roles=[_make_role(RoleType.OWNER)],
        permissions={PermissionKey.USERS_VIEW},
    )
    assert user.is_founder is False
    assert user.has_permission(PermissionKey.USERS_VIEW) is True
    assert user.has_permission(PermissionKey.SYSTEM_SETTINGS) is False


def test_user_with_no_roles():
    """User with no roles has no permissions."""
    user = User(id=uuid.uuid4(), telegram_id=789)
    assert user.is_founder is False
    assert user.has_permission(PermissionKey.USERS_VIEW) is False
    assert user.highest_role is None


def test_highest_role():
    """Highest role returns the one with lowest hierarchy level."""
    user = User(
        id=uuid.uuid4(),
        telegram_id=101,
        roles=[
            _make_role(RoleType.WORKER),
            _make_role(RoleType.ADMIN),
        ],
    )
    assert user.highest_role is not None
    assert user.highest_role.role_type == RoleType.ADMIN


def test_full_name_fallbacks():
    """Full name falls back: first+last > username > telegram_id."""
    u1 = User(id=uuid.uuid4(), telegram_id=1, first_name="Nathan", last_name="Idol")
    assert u1.full_name == "Nathan Idol"

    u2 = User(id=uuid.uuid4(), telegram_id=2, username="nathanidol")
    assert u2.full_name == "nathanidol"

    u3 = User(id=uuid.uuid4(), telegram_id=3)
    assert u3.full_name == "3"
