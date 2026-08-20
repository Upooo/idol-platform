# Security

## Founder Protection

1. Founder identity is set **exclusively** via `FOUNDER_TELEGRAM_ID` environment variable.
2. Founder **cannot** be deleted, demoted, transferred, or replaced via bot operations.
3. Founder has **implicit ALL permissions** — no explicit assignment needed.
4. All operations targeting a Founder user raise `FounderProtectionError`.

## Authentication

- Every request passes through auth middleware.
- Middleware resolves Telegram user → platform User with roles + permissions.
- Unknown users are auto-registered as Customer (lowest role).

## Authorization

- Backend ALWAYS verifies permissions — keyboard visibility is just a UI hint.
- Permission check: `user.has_permission(PermissionKey.X)`
- Hierarchy check: actor's highest role must be ABOVE target's highest role.
- Both checks must pass for role management operations.

## Audit

- Every state-changing operation is logged to `audit_logs`.
- Log contains: who (actor), what (action), on whom (target), when, metadata.
- Metadata is JSONB — never contains secrets (passwords, tokens).
- Denied attempts are also logged (`AUTH_DENIED`).

## Secrets

- All secrets use `SecretStr` in configuration — masked in logs/repr.
- No `os.getenv()` calls outside `src/config.py`.
- `.env` file is in `.gitignore`.
