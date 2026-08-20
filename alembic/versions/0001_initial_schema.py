"""Initial schema — foundation tables + seed data.

Revision ID: 0001
Revises: None
Create Date: 2026-08-21

Creates:
- users
- roles (seeded with 5 built-in roles)
- permissions (seeded with 16 permission keys)
- user_roles
- role_permissions (seeded with default mappings)
- audit_logs
"""

from typing import Sequence, Union
import uuid
from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

# ── Seed data ──

ROLES = [
    ("founder", "Root identity. Implicit ALL permissions.", 1),
    ("owner", "Operational lead. Permissions via RBAC config.", 2),
    ("admin", "Group/staff management. Permissions via RBAC config.", 3),
    ("worker", "Operational staff. Permissions via RBAC config.", 4),
    ("customer", "End user. Minimal permissions.", 5),
]

PERMISSION_KEYS = [
    "users.view",
    "users.create",
    "users.update",
    "users.delete",
    "staff.view",
    "staff.manage",
    "roles.view",
    "roles.manage",
    "roles.assign",
    "permissions.view",
    "permissions.manage",
    "group.manage",
    "group.moderate",
    "group.invite",
    "system.settings",
    "system.audit",
]

# Default role-permission mappings (Founder gets ALL implicitly, not via table)
DEFAULT_ROLE_PERMISSIONS = {
    "owner": [
        "users.view", "users.create", "users.update",
        "staff.view", "staff.manage",
        "roles.view", "roles.assign",
        "permissions.view",
        "group.manage", "group.moderate", "group.invite",
        "system.settings", "system.audit",
    ],
    "admin": [
        "users.view",
        "staff.view",
        "roles.view",
        "group.moderate", "group.invite",
    ],
    "worker": [
        "users.view",
    ],
    "customer": [],
}


def _genuuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


def upgrade() -> None:
    # ── users ──
    op.create_table(
        "users",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger, unique=True, nullable=False, index=True),
        sa.Column("username", sa.String(255), nullable=True),
        sa.Column("first_name", sa.String(255), nullable=True),
        sa.Column("last_name", sa.String(255), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    # ── roles ──
    op.create_table(
        "roles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(50), unique=True, nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("hierarchy_level", sa.Integer, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # ── permissions ──
    op.create_table(
        "permissions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("key", sa.String(100), unique=True, nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    # ── user_roles ──
    op.create_table(
        "user_roles",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role_id", UUID(as_uuid=True), sa.ForeignKey("roles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("assigned_by", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("assigned_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("user_id", "role_id", name="uq_user_role"),
    )

    # ── role_permissions ──
    op.create_table(
        "role_permissions",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("role_id", UUID(as_uuid=True), sa.ForeignKey("roles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("permission_id", UUID(as_uuid=True), sa.ForeignKey("permissions.id", ondelete="CASCADE"), nullable=False),
        sa.UniqueConstraint("role_id", "permission_id", name="uq_role_permission"),
    )

    # ── audit_logs ──
    op.create_table(
        "audit_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("actor_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("target_type", sa.String(50), nullable=True),
        sa.Column("target_id", sa.String(255), nullable=True),
        sa.Column("metadata", JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, index=True),
    )

    # ── Seed roles ──
    now = _now()
    roles_table = sa.table(
        "roles",
        sa.column("id", UUID(as_uuid=True)),
        sa.column("name", sa.String),
        sa.column("description", sa.Text),
        sa.column("hierarchy_level", sa.Integer),
        sa.column("created_at", sa.DateTime(timezone=True)),
    )
    role_ids = {}
    for name, desc, level in ROLES:
        rid = _genuuid()
        role_ids[name] = rid
        op.execute(
            roles_table.insert().values(
                id=rid, name=name, description=desc,
                hierarchy_level=level, created_at=now,
            )
        )

    # ── Seed permissions ──
    perms_table = sa.table(
        "permissions",
        sa.column("id", UUID(as_uuid=True)),
        sa.column("key", sa.String),
        sa.column("description", sa.Text),
        sa.column("created_at", sa.DateTime(timezone=True)),
    )
    perm_ids = {}
    for key in PERMISSION_KEYS:
        pid = _genuuid()
        perm_ids[key] = pid
        op.execute(
            perms_table.insert().values(
                id=pid, key=key, description=None, created_at=now,
            )
        )

    # ── Seed role-permission mappings ──
    rp_table = sa.table(
        "role_permissions",
        sa.column("id", UUID(as_uuid=True)),
        sa.column("role_id", UUID(as_uuid=True)),
        sa.column("permission_id", UUID(as_uuid=True)),
    )
    for role_name, perm_keys in DEFAULT_ROLE_PERMISSIONS.items():
        for perm_key in perm_keys:
            op.execute(
                rp_table.insert().values(
                    id=_genuuid(),
                    role_id=role_ids[role_name],
                    permission_id=perm_ids[perm_key],
                )
            )


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("role_permissions")
    op.drop_table("user_roles")
    op.drop_table("permissions")
    op.drop_table("roles")
    op.drop_table("users")
