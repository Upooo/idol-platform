"""Repository convenience imports."""

from src.infrastructure.database.repositories.audit_repo import AuditRepository
from src.infrastructure.database.repositories.permission_repo import PermissionRepository
from src.infrastructure.database.repositories.role_repo import RoleRepository
from src.infrastructure.database.repositories.user_repo import UserRepository

__all__ = [
    "AuditRepository",
    "PermissionRepository",
    "RoleRepository",
    "UserRepository",
]
