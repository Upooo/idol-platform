# Architecture

## Layered Architecture

```
Presentation Layer (src/presentation/)
├── handlers/     — aiogram message & callback handlers
├── middlewares/  — auth, logging, error handling
└── keyboards/    — inline keyboard builders
         ↓
Application Layer (src/application/)
├── identity_service.py  — user CRUD + identity bootstrap
├── auth_service.py      — RBAC authorization checks
└── audit_service.py     — audit log recording
         ↓
Domain Layer (src/domain/)
├── models.py      — User, Role, AuditEntry dataclasses
├── enums.py       — RoleType, PermissionKey, UserStatus, AuditAction
└── exceptions.py  — domain-specific exceptions
         ↓
Infrastructure Layer (src/infrastructure/)
├── database/
│   ├── engine.py       — async SQLAlchemy engine
│   ├── tables.py       — SA table definitions
│   └── repositories/   — data access objects
├── notification/
│   └── service.py      — Telegram group notifications
└── logging.py          — structlog configuration
```

## Rules

1. **Handlers have NO business logic.** They receive input, call a service, send a response.
2. **Services orchestrate.** They call domain logic and repositories.
3. **Domain is pure.** No framework imports, no I/O.
4. **Infrastructure is replaceable.** Swap PostgreSQL for MySQL by changing only infrastructure.

## Dependencies flow DOWNWARD only

- Presentation → Application → Domain ← Infrastructure
- Domain NEVER imports from Presentation or Infrastructure
- Application MAY import from Infrastructure (via dependency injection)
