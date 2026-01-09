# SQLModel - Alembic Migrations

## Installation

```bash
pip install alembic
```

## Initialize Alembic

```bash
alembic init migrations
```

This creates:
```
migrations/
├── env.py           # Migration environment config
├── script.py.mako   # Migration script template
├── versions/        # Migration files go here
└── README
alembic.ini          # Alembic configuration
```

## Configure Alembic

### 1. Update `alembic.ini`

```ini
# Set your database URL
sqlalchemy.url = postgresql://user:pass@localhost:5432/dbname

# Or use environment variable (recommended)
# sqlalchemy.url =
```

### 2. Update `migrations/env.py`

```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os

# Import SQLModel and your models
from sqlmodel import SQLModel
# IMPORTANT: Import all your models here so Alembic can detect them
from app.models import Hero, Team  # Import your actual models

config = context.config

# Use environment variable for database URL
database_url = os.getenv("DATABASE_URL")
if database_url:
    config.set_main_option("sqlalchemy.url", database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Set target metadata to SQLModel's metadata
target_metadata = SQLModel.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        render_as_batch=True,  # Required for SQLite
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=True,  # Required for SQLite
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### 3. Update `migrations/script.py.mako`

Add SQLModel imports to the template:

```mako
"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
import sqlmodel  # Add this line
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    ${downgrades if downgrades else "pass"}
```

## Migration Workflow

### Create Initial Migration

```bash
# Auto-generate from models
alembic revision --autogenerate -m "Initial migration"

# Or create empty migration
alembic revision -m "Initial migration"
```

### Apply Migrations

```bash
# Upgrade to latest
alembic upgrade head

# Upgrade one step
alembic upgrade +1

# Upgrade to specific revision
alembic upgrade abc123
```

### Downgrade

```bash
# Downgrade one step
alembic downgrade -1

# Downgrade to specific revision
alembic downgrade abc123

# Downgrade to nothing (dangerous!)
alembic downgrade base
```

### View Status

```bash
# Current revision
alembic current

# Migration history
alembic history

# Show pending migrations
alembic history --verbose
```

## Common Migration Operations

### Add Column

```python
def upgrade() -> None:
    op.add_column('hero', sa.Column('power_level', sa.Integer(), nullable=True))

def downgrade() -> None:
    op.drop_column('hero', 'power_level')
```

### Add Column with Default (Non-Nullable)

```python
def upgrade() -> None:
    # Add as nullable first
    op.add_column('hero', sa.Column('is_active', sa.Boolean(), nullable=True))
    # Set default value for existing rows
    op.execute("UPDATE hero SET is_active = true")
    # Make non-nullable
    op.alter_column('hero', 'is_active', nullable=False)

def downgrade() -> None:
    op.drop_column('hero', 'is_active')
```

### Remove Column

```python
def upgrade() -> None:
    op.drop_column('hero', 'old_column')

def downgrade() -> None:
    op.add_column('hero', sa.Column('old_column', sa.String(), nullable=True))
```

### Rename Column

```python
def upgrade() -> None:
    op.alter_column('hero', 'name', new_column_name='full_name')

def downgrade() -> None:
    op.alter_column('hero', 'full_name', new_column_name='name')
```

### Create Table

```python
def upgrade() -> None:
    op.create_table(
        'weapon',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('damage', sa.Integer(), nullable=False),
        sa.Column('hero_id', sa.Integer(), sa.ForeignKey('hero.id')),
    )

def downgrade() -> None:
    op.drop_table('weapon')
```

### Drop Table

```python
def upgrade() -> None:
    op.drop_table('old_table')

def downgrade() -> None:
    op.create_table(
        'old_table',
        sa.Column('id', sa.Integer(), primary_key=True),
        # ... other columns
    )
```

### Add Index

```python
def upgrade() -> None:
    op.create_index('ix_hero_name', 'hero', ['name'])

def downgrade() -> None:
    op.drop_index('ix_hero_name', 'hero')
```

### Add Foreign Key

```python
def upgrade() -> None:
    op.add_column('hero', sa.Column('team_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_hero_team', 'hero', 'team', ['team_id'], ['id'])

def downgrade() -> None:
    op.drop_constraint('fk_hero_team', 'hero', type_='foreignkey')
    op.drop_column('hero', 'team_id')
```

### Add Unique Constraint

```python
def upgrade() -> None:
    op.create_unique_constraint('uq_hero_email', 'hero', ['email'])

def downgrade() -> None:
    op.drop_constraint('uq_hero_email', 'hero', type_='unique')
```

## Async Migrations

For async engines, update `env.py`:

```python
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine

async def run_migrations_online() -> None:
    connectable = create_async_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()

def do_run_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())
```

## Best Practices

### 1. Always Review Auto-generated Migrations

```bash
# Generate
alembic revision --autogenerate -m "Add user table"

# Review the generated file before applying!
cat migrations/versions/abc123_add_user_table.py
```

### 2. Use Descriptive Migration Names

```bash
# Good
alembic revision --autogenerate -m "Add email column to users"

# Bad
alembic revision --autogenerate -m "update"
```

### 3. Handle Data Migrations Carefully

```python
def upgrade() -> None:
    # Schema change
    op.add_column('hero', sa.Column('status', sa.String(), nullable=True))

    # Data migration
    connection = op.get_bind()
    connection.execute(sa.text("UPDATE hero SET status = 'active'"))

    # Make non-nullable after data is set
    op.alter_column('hero', 'status', nullable=False)
```

### 4. Test Migrations

```bash
# Test upgrade
alembic upgrade head

# Test downgrade
alembic downgrade -1

# Verify upgrade again
alembic upgrade head
```

### 5. Batch Mode for SQLite

SQLite doesn't support many ALTER TABLE operations. Use batch mode:

```python
# In env.py
context.configure(
    connection=connection,
    target_metadata=target_metadata,
    render_as_batch=True,  # Required for SQLite
)
```

## Troubleshooting

| Issue | Cause | Solution |
|-------|-------|----------|
| "Target database is not up to date" | Pending migrations | Run `alembic upgrade head` |
| "Can't locate revision" | Missing migration file | Check `versions/` folder |
| "Detected removed table" | Models not imported | Import all models in `env.py` |
| Empty migration | No changes detected | Check model imports |
| "No changes in schema" | Metadata not set | Set `target_metadata = SQLModel.metadata` |

## Migration Commands Reference

| Command | Description |
|---------|-------------|
| `alembic init migrations` | Initialize Alembic |
| `alembic revision -m "msg"` | Create empty migration |
| `alembic revision --autogenerate -m "msg"` | Auto-generate migration |
| `alembic upgrade head` | Apply all migrations |
| `alembic upgrade +1` | Apply next migration |
| `alembic downgrade -1` | Revert last migration |
| `alembic downgrade base` | Revert all migrations |
| `alembic current` | Show current revision |
| `alembic history` | Show migration history |
| `alembic show <revision>` | Show specific migration |
