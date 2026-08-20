# Founder Setup

## How It Works

The Founder is the root identity of the IDOL Platform. There is exactly ONE Founder.

## Setting the Founder

The Founder is set **exclusively** through the environment variable:

```env
FOUNDER_TELEGRAM_ID=7714463332
```

This is the ONLY mechanism. There is no bot command, no UI, no database flag.

## Bootstrap Flow

```
Application starts
  → Read FOUNDER_TELEGRAM_ID from config
  → Find or create User with that telegram_id
  → Assign Founder role (if not already assigned)
  → Log: AuditAction.FOUNDER_BOOTSTRAP
  → Founder is ready
```

## What Founder Can Do

- ALL permissions (implicit wildcard)
- Manage all roles and permissions
- Assign/remove Owner, Admin, Worker, Customer roles
- Configure role-permission mappings without code changes
- View all audit logs
- Manage system settings

## What Cannot Be Done to Founder

- Cannot be deleted
- Cannot be demoted
- Cannot be transferred to another user
- Cannot be replaced via bot operations
