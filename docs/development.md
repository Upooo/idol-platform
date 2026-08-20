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

make up       # Start PostgreSQL
make install  # Install Python dependencies
make migrate  # Run migrations
make run      # Start the bot
```

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
make shell         # Python REPL with config loaded
```

## Development Phases

1. ✅ Phase 1 — Repository structure + config + Docker
2. ⬜ Phase 2 — Database (engine, tables, Alembic, seed)
3. ⬜ Phase 3 — Identity (user repo, identity service, founder bootstrap)
4. ⬜ Phase 4 — Roles + Permissions (RBAC, auth service, auth middleware)
5. ⬜ Phase 5 — HQ Bot foundation (/start, keyboards, callbacks)
6. ⬜ Phase 6 — IDOL TEAM integration (notifications, topic routing)
7. ⬜ Phase 7 — Audit + logging
8. ⬜ Phase 8 — Testing (full test suite)
