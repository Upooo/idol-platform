# Permissions Model

## Design Principles

1. **Centralized RBAC** — No `if role == "founder"` checks in handlers.
2. **Explicit Permissions** — Every action requires a specific `PermissionKey`.
3. **Role Hierarchy** — Limits management scope (can't manage roles at or above your level).
4. **Founder Wildcard** — Founder has ALL permissions implicitly, no explicit assignment needed.
5. **Everyone else is explicit** — Owner, Admin, Worker, Customer have ONLY what's assigned.

## Authorization Flow

```
Request
  → Auth Middleware: inject user + roles + permissions
  → Handler: auth_service.require_permission(user, PermissionKey.STAFF_MANAGE)
  → AuthService:
      1. Check user.has_permission(key)  → PermissionDeniedError if no
      2. If managing a role: check hierarchy  → RoleHierarchyError if violates
      3. If target is Founder: check FounderProtection  → FounderProtectionError
      4. Audit log the attempt (success or failure)
  → Execute action
```

## Founder Protection (V1)

- Founder **cannot** be deleted.
- Founder **cannot** be demoted.
- Founder **cannot** be transferred.
- Founder **cannot** be modified via normal bot operations.
- Founder identity comes **exclusively** from `FOUNDER_TELEGRAM_ID` env var.

## Permission Keys

See `src/domain/enums.py` → `PermissionKey` for the complete list.
