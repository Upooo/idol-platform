"""Domain exceptions.

Custom exceptions for business rule violations.
These are caught by the presentation layer and converted to user messages.
"""

from __future__ import annotations


class DomainError(Exception):
    """Base domain error."""


class PermissionDeniedError(DomainError):
    """User lacks required permission."""

    def __init__(self, permission: str, message: str | None = None):
        self.permission = permission
        super().__init__(message or f"Permission denied: {permission}")


class RoleHierarchyError(DomainError):
    """User tried to manage a role at or above their own level."""


class FounderProtectionError(DomainError):
    """Attempted to modify the protected Founder identity.

    Founder cannot be:
    - Deleted
    - Demoted
    - Transferred
    - Modified via normal bot operations
    """


class UserNotFoundError(DomainError):
    """User not found."""


class UserAlreadyExistsError(DomainError):
    """User already exists."""


class InvalidOperationError(DomainError):
    """Generic invalid operation."""
