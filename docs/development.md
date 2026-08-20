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
make migrate  # Run migrations (creates tables + seeds roles/permissions)
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
2. ✅ Phase 2 — Database (engine, tables, repositories, seed, founder bootstrap)
3. ✅ Phase 3 — Auth service (permission, hierarchy, founder protection)
4. ✅ Phase 4 — Auth middleware + user resolver
5. ✅ Phase 5 — HQ Bot (/start, /help, /myid, /myroles, keyboards, callbacks)
6. ✅ Phase 6 — Error middleware + audit service
7. ✅ Phase 7 — Tests (domain models, auth service, config)

## V1 Foundation Complete

The platform is ready for:
- Bot startup with full RBAC
- Founder bootstrap from env
- Permission-based menu visibility
- Role management (Founder/Owner only)
- Centralized error handling
- Audit logging

Next steps (beyond V1 Foundation):
- Business domain (orders, products, payments)
- AI integration
- IDOL TEAM group features
- Customer-facing flows
