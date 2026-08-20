# Database Design

## Tables (V1 Foundation)

### users
- id (UUID, PK)
- telegram_id (BIGINT, UNIQUE, NOT NULL)
- username (VARCHAR, nullable)
- first_name (VARCHAR, nullable)
- last_name (VARCHAR, nullable)
- status (VARCHAR, NOT NULL, default 'active')
- created_at (TIMESTAMPTZ, NOT NULL)
- updated_at (TIMESTAMPTZ, NOT NULL)

### roles
- id (UUID, PK)
- name (VARCHAR, UNIQUE, NOT NULL)
- description (TEXT, nullable)
- hierarchy_level (INTEGER, NOT NULL)
- created_at (TIMESTAMPTZ, NOT NULL)

Seeded with: founder(1), owner(2), admin(3), worker(4), customer(5)

### permissions
- id (UUID, PK)
- key (VARCHAR, UNIQUE, NOT NULL)
- description (TEXT, nullable)
- created_at (TIMESTAMPTZ, NOT NULL)

Seeded from `PermissionKey` enum.

### user_roles
- user_id (UUID, FK users.id, NOT NULL)
- role_id (UUID, FK roles.id, NOT NULL)
- assigned_by (UUID, FK users.id, nullable)
- assigned_at (TIMESTAMPTZ, NOT NULL)

Composite UNIQUE on (user_id, role_id). Multi-role supported.

### role_permissions
- role_id (UUID, FK roles.id, NOT NULL)
- permission_id (UUID, FK permissions.id, NOT NULL)

Composite UNIQUE on (role_id, permission_id).

### audit_logs
- id (UUID, PK)
- actor_id (UUID, FK users.id, nullable)
- action (VARCHAR, NOT NULL)
- target_type (VARCHAR, nullable)
- target_id (VARCHAR, nullable)
- metadata (JSONB, nullable, no secrets)
- created_at (TIMESTAMPTZ, NOT NULL)

## Migration Strategy

- All migrations via Alembic
- Auto-generate from SQLAlchemy models
- Run with `make migrate`
- Seed data (roles, permissions) in initial migration
