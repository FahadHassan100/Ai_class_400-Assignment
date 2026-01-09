---
name: sqlmodel
description: |
  Work with SQLModel - the Python ORM combining SQLAlchemy and Pydantic.
  Use when defining database models, creating relationships, performing CRUD operations,
  setting up async database connections, running Alembic migrations, or integrating with FastAPI.
  Covers PostgreSQL, SQLite, and MySQL databases.
---

# SQLModel Development

Build type-safe database applications with SQLModel - one model for both validation and database operations.

## Quick Start

```python
from sqlmodel import SQLModel, Field, create_engine, Session, select

class Hero(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    secret_name: str
    age: int | None = None

engine = create_engine("sqlite:///database.db")
SQLModel.metadata.create_all(engine)

# Create
with Session(engine) as session:
    hero = Hero(name="Spider-Boy", secret_name="Pedro")
    session.add(hero)
    session.commit()
```

## Workflow

```
┌─────────────────────────────────────────────────────────┐
│                   What do you need?                      │
└─────────────────────────────────────────────────────────┘
                          │
      ┌───────────┬───────┼───────┬───────────┐
      ▼           ▼       ▼       ▼           ▼
   Models    Relationships  CRUD   Async    Migrations
      │           │         │       │           │
      ▼           ▼         ▼       ▼           ▼
  models.md  relationships.md crud.md async.md migrations.md
```

## Reference Guides

| Task | Reference |
|------|-----------|
| Model definitions, fields, indexes | [references/models.md](references/models.md) |
| One-to-many, many-to-many relationships | [references/relationships.md](references/relationships.md) |
| Create, read, update, delete operations | [references/crud.md](references/crud.md) |
| Async engine, sessions, database drivers | [references/async.md](references/async.md) |
| Alembic setup and migration workflows | [references/migrations.md](references/migrations.md) |
| FastAPI integration patterns | [references/fastapi-integration.md](references/fastapi-integration.md) |

## Before Implementation

Gather context before implementing:

| Source | Gather |
|--------|--------|
| **Codebase** | Existing models, database setup, session patterns |
| **Conversation** | User's specific requirements, database choice |
| **Skill References** | Patterns from `references/` for the specific task |
| **User Guidelines** | Project conventions, naming standards |

## Key Concepts

### SQLModel = Pydantic + SQLAlchemy

```python
# One class serves both purposes:
# - Pydantic: validation, serialization, API schemas
# - SQLAlchemy: ORM, database operations

class User(SQLModel, table=True):  # table=True makes it a DB table
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True, index=True)
    name: str
```

### Table vs Data Model

```python
# Database table (table=True)
class HeroBase(SQLModel):
    name: str
    secret_name: str

class Hero(HeroBase, table=True):  # Actual DB table
    id: int | None = Field(default=None, primary_key=True)

class HeroCreate(HeroBase):  # For creating (no id)
    pass

class HeroRead(HeroBase):  # For reading (with id)
    id: int
```

## Database Connection Strings

| Database | Sync | Async |
|----------|------|-------|
| SQLite | `sqlite:///./db.sqlite` | `sqlite+aiosqlite:///./db.sqlite` |
| PostgreSQL | `postgresql://user:pass@host/db` | `postgresql+asyncpg://user:pass@host/db` |
| MySQL | `mysql://user:pass@host/db` | `mysql+aiomysql://user:pass@host/db` |

## Common Patterns

### Basic CRUD

```python
# Create
session.add(hero)
session.commit()
session.refresh(hero)

# Read
hero = session.get(Hero, hero_id)
heroes = session.exec(select(Hero)).all()

# Update
hero.name = "New Name"
session.add(hero)
session.commit()

# Delete
session.delete(hero)
session.commit()
```

### FastAPI Dependency

```python
def get_session():
    with Session(engine) as session:
        yield session

@app.post("/heroes")
def create_hero(hero: Hero, session: Session = Depends(get_session)):
    session.add(hero)
    session.commit()
    session.refresh(hero)
    return hero
```

## Installation

```bash
# Core
pip install sqlmodel

# Database drivers
pip install psycopg2-binary  # PostgreSQL sync
pip install asyncpg           # PostgreSQL async
pip install aiosqlite         # SQLite async
pip install aiomysql          # MySQL async

# Migrations
pip install alembic
```

## Anti-Patterns to Avoid

| Anti-Pattern | Problem | Solution |
|--------------|---------|----------|
| N+1 queries | Loading relationships one-by-one | Use `selectinload()` or `joinedload()` |
| Forgetting `table=True` | Model won't create table | Add `table=True` for DB tables |
| Not refreshing after commit | Stale data in object | Call `session.refresh(obj)` |
| Sync engine with async code | Blocks event loop | Use `create_async_engine` |
| Circular imports | Model relationships fail | Use `TYPE_CHECKING` pattern |
