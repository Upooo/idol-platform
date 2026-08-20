# IDOL Platform

Enterprise-grade Telegram platform with RBAC, audit logging, and modular architecture.

## Architecture

```
Presentation (aiogram handlers, middlewares)
       ↓
Application (services, use cases)
       ↓
Domain (models, enums, business rules)
       ↓
Infrastructure (database repos, notifications)
```

**Principles:**
- Handlers have NO business logic — they receive input, call services, send responses
- Services orchestrate domain logic + repositories
- Domain is pure business rules, no framework dependency
- Infrastructure handles external systems (DB, Telegram API, etc.)

## Tech Stack

- **Python 3.11+** with asyncio
- **aiogram 3.x** — async Telegram bot framework
- **PostgreSQL** — production database
- **SQLAlchemy 2.0** (async) — ORM / query builder
- **Alembic** — database migrations
- **pydantic-settings** — centralized configuration
- **structlog** — structured logging
- **Docker** — containerization

## Quick Start

```bash
# 1. Copy environment config
cp .env.example .env
# Edit .env with your values (BOT_TOKEN, FOUNDER_TELEGRAM_ID, etc.)

# 2. Start services
make up

# 3. Run database migrations
make migrate

# 4. Start the bot
make run
```

## Development

```bash
# Install dependencies
make install

# Run tests
make test

# Create a new migration
make migration msg="add users table"

# View logs
make logs
```

## Project Structure

See [docs/architecture.md](docs/architecture.md) for detailed explanation.

## RBAC Model

See [docs/permissions.md](docs/permissions.md) for the full permission model.

## Founder Setup

See [docs/setup-founder.md](docs/setup-founder.md) for initial bootstrap.
