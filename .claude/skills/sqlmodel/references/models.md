# SQLModel - Model Definitions

## Basic Model

```python
from sqlmodel import SQLModel, Field

class Hero(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    secret_name: str
    age: int | None = None
```

## Field Options

```python
from sqlmodel import Field
from datetime import datetime

class User(SQLModel, table=True):
    # Primary key
    id: int | None = Field(default=None, primary_key=True)

    # Required with constraints
    email: str = Field(unique=True, index=True, max_length=255)

    # Optional with default
    is_active: bool = Field(default=True)

    # With validation
    age: int | None = Field(default=None, ge=0, le=150)

    # Foreign key
    team_id: int | None = Field(default=None, foreign_key="team.id")

    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)

    # Custom column name
    full_name: str = Field(sa_column_kwargs={"name": "fullname"})
```

## Field Parameters

| Parameter | Purpose | Example |
|-----------|---------|---------|
| `primary_key` | Mark as primary key | `Field(primary_key=True)` |
| `default` | Default value | `Field(default=True)` |
| `default_factory` | Callable for default | `Field(default_factory=datetime.utcnow)` |
| `foreign_key` | FK reference | `Field(foreign_key="table.column")` |
| `unique` | Unique constraint | `Field(unique=True)` |
| `index` | Create index | `Field(index=True)` |
| `nullable` | Allow NULL | `Field(nullable=True)` |
| `max_length` | String max length | `Field(max_length=100)` |
| `ge`, `gt`, `le`, `lt` | Numeric validation | `Field(ge=0, le=100)` |
| `regex` | String pattern | `Field(regex="^[a-z]+$")` |

## Inheritance Pattern (Recommended)

Avoid code duplication with base classes:

```python
# Base with shared fields (no table)
class HeroBase(SQLModel):
    name: str
    secret_name: str
    age: int | None = None

# Database table
class Hero(HeroBase, table=True):
    id: int | None = Field(default=None, primary_key=True)

# Create schema (no id)
class HeroCreate(HeroBase):
    pass

# Read schema (with id)
class HeroRead(HeroBase):
    id: int

# Update schema (all optional)
class HeroUpdate(SQLModel):
    name: str | None = None
    secret_name: str | None = None
    age: int | None = None
```

## Custom Table Name

```python
class Hero(SQLModel, table=True):
    __tablename__ = "heroes"  # Custom table name

    id: int | None = Field(default=None, primary_key=True)
    name: str
```

## Composite Primary Key

```python
class HeroTeamLink(SQLModel, table=True):
    hero_id: int = Field(foreign_key="hero.id", primary_key=True)
    team_id: int = Field(foreign_key="team.id", primary_key=True)
```

## Column Types

```python
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, Text, JSON, ARRAY, Enum
from datetime import datetime, date
from decimal import Decimal
from enum import Enum as PyEnum
import uuid

class Status(str, PyEnum):
    ACTIVE = "active"
    INACTIVE = "inactive"

class Product(SQLModel, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)

    # Text types
    name: str                                    # VARCHAR
    description: str = Field(sa_column=Column(Text))  # TEXT

    # Numeric types
    price: Decimal = Field(decimal_places=2)
    quantity: int
    rating: float

    # Date/time types
    created_at: datetime
    birth_date: date

    # Boolean
    is_available: bool = True

    # JSON (PostgreSQL)
    metadata: dict = Field(default={}, sa_column=Column(JSON))

    # Enum
    status: Status = Status.ACTIVE
```

## Indexes

```python
from sqlmodel import SQLModel, Field
from sqlalchemy import Index

class Hero(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)  # Simple index
    team_id: int | None = Field(default=None, index=True)

    # Composite index
    __table_args__ = (
        Index("ix_hero_name_team", "name", "team_id"),
    )
```

## Unique Constraints

```python
from sqlalchemy import UniqueConstraint

class User(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    email: str = Field(unique=True)  # Simple unique

    # Composite unique constraint
    first_name: str
    last_name: str

    __table_args__ = (
        UniqueConstraint("first_name", "last_name", name="uq_user_full_name"),
    )
```

## Check Constraints (PostgreSQL)

```python
from sqlalchemy import CheckConstraint

class Product(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    price: float
    quantity: int

    __table_args__ = (
        CheckConstraint("price > 0", name="ck_product_price_positive"),
        CheckConstraint("quantity >= 0", name="ck_product_quantity_non_negative"),
    )
```

## Avoiding Circular Imports

```python
# models/base.py
from sqlmodel import SQLModel

# models/team.py
from typing import TYPE_CHECKING, List
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .hero import Hero

class Team(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    heroes: List["Hero"] = Relationship(back_populates="team")

# models/hero.py
from typing import TYPE_CHECKING
from sqlmodel import SQLModel, Field, Relationship

if TYPE_CHECKING:
    from .team import Team

class Hero(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    team_id: int | None = Field(default=None, foreign_key="team.id")
    team: "Team" | None = Relationship(back_populates="heroes")
```

## Model Config

```python
class Hero(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str

    model_config = {
        "str_strip_whitespace": True,  # Strip whitespace from strings
        "validate_assignment": True,    # Validate on attribute assignment
    }
```
