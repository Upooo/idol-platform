# Development Guide

## Prerequisites

- Python 3.11+
- PostgreSQL 16+
- Docker & Docker Compose (recommended)

## Setup

```bash
cd idol-platform
cp .env.example .env
# Edit .env: HQ_BOT_TOKEN, FOUNDER_TELEGRAM_ID, DATABASE_URL
# Optional: IDOL_TEAM_GROUP_ID + topic IDs for group notifications

make up       # Start PostgreSQL
make install  # Install Python dependencies
make migrate  # Run migrations (creates tables + seeds roles/permissions)
make run      # Start the bot
```

## IDOL TEAM Group Setup

1. Create a Telegram supergroup with Topics enabled
2. Add the bot as admin
3. Create topics: #system, #orders, #staff
4. Get the group ID and topic IDs (use /myid in the group or check logs)
5. Set in .env:
   ```
   IDOL_TEAM_GROUP_ID=-100xxxxxxxxxx
   TOPIC_SYSTEM_ID=2
   TOPIC_ORDERS_ID=3
   TOPIC_STAFF_ID=4
   ```

## Bot Commands

**Everyone:**
- `/start` — Main menu with inline keyboard
- `/help` — Role-aware command list
- `/myid` — Show your Telegram ID
- `/myroles` — Show your roles + permissions
- `/cancel` — Cancel operation

**Founder / Owner (with ROLES_ASSIGN):**
- `/staff` — List all staff with roles
- `/assign <telegram_id>` — Assign a role to a user
- `/revoke <telegram_id>` — Remove a role from a user

## Common Commands

```bash
make test          # Run tests
make test-cov      # Tests with coverage
make lint          # Run ruff linter
make format        # Auto-format code
make typecheck     # Run mypy
make migration msg="add X table"  # Create new migration
make db-shell      # Open psql
make logs          # Docker logs
```

## Architecture

```
Presentation (handlers, middlewares, keyboards)
       ↓
Application (auth_service, audit_service, identity_service, user_resolver)
       ↓
Domain (models, enums, exceptions)
       ↓
Infrastructure (database, notification, logging)
```

## Development Status

1. ✅ Repository structure + config + Docker
2. ✅ Database (engine, tables, repositories, seed, founder bootstrap)
3. ✅ Auth service (permission, hierarchy, founder protection)
4. ✅ Auth middleware + user resolver
5. ✅ HQ Bot (/start, /help, /myid, /myroles, profile)
6. ✅ Role management (/assign, /revoke, /staff)
7. ✅ IDOL TEAM group integration (topic notifications)
8. ✅ Error middleware + audit service
9. ✅ Tests (domain models, auth service, config)

**V1 Foundation complete.** Next: Service Catalog → Orders → Payments.
