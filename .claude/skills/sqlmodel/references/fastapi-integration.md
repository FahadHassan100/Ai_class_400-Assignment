# SQLModel - FastAPI Integration

## Project Structure

```
app/
├── main.py              # FastAPI app, lifespan
├── database.py          # Engine, session setup
├── models/
│   ├── __init__.py      # Export all models
│   ├── hero.py          # Hero model
│   └── team.py          # Team model
├── routers/
│   ├── __init__.py
│   ├── heroes.py        # Hero endpoints
│   └── teams.py         # Team endpoints
└── schemas/             # Optional: separate schemas
    └── hero.py
```

## Database Setup

### Sync Setup (`database.py`)

```python
from sqlmodel import SQLModel, create_engine, Session
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./database.db")

engine = create_engine(DATABASE_URL, echo=True)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
```

### Async Setup (`database.py`)

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel
import os

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./database.db")

async_engine = create_async_engine(DATABASE_URL, echo=True)

async_session_maker = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

async def create_db_and_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

async def get_session() -> AsyncSession:
    async with async_session_maker() as session:
        yield session
```

## Model Inheritance Pattern

Separate concerns with base models:

```python
# models/hero.py
from sqlmodel import SQLModel, Field, Relationship
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .team import Team

# Base fields (shared by all)
class HeroBase(SQLModel):
    name: str = Field(index=True)
    secret_name: str
    age: int | None = None

# Database table
class Hero(HeroBase, table=True):
    id: int | None = Field(default=None, primary_key=True)
    team_id: int | None = Field(default=None, foreign_key="team.id")
    team: "Team" | None = Relationship(back_populates="heroes")

# Create schema (API input)
class HeroCreate(HeroBase):
    team_id: int | None = None

# Read schema (API output)
class HeroRead(HeroBase):
    id: int
    team_id: int | None = None

# Update schema (partial updates)
class HeroUpdate(SQLModel):
    name: str | None = None
    secret_name: str | None = None
    age: int | None = None
    team_id: int | None = None

# Read with relationship
class HeroReadWithTeam(HeroRead):
    team: "TeamRead" | None = None
```

## FastAPI App with Lifespan

### Sync

```python
# main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
from database import create_db_and_tables
from routers import heroes, teams

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    create_db_and_tables()
    yield
    # Shutdown (cleanup if needed)

app = FastAPI(lifespan=lifespan)

app.include_router(heroes.router)
app.include_router(teams.router)
```

### Async

```python
# main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
from database import create_db_and_tables, async_engine
from routers import heroes, teams

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_db_and_tables()
    yield
    await async_engine.dispose()

app = FastAPI(lifespan=lifespan)

app.include_router(heroes.router)
app.include_router(teams.router)
```

## CRUD Router (Sync)

```python
# routers/heroes.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlmodel import Session, select
from database import get_session
from models.hero import Hero, HeroCreate, HeroRead, HeroUpdate

router = APIRouter(prefix="/heroes", tags=["heroes"])

@router.post("/", response_model=HeroRead)
def create_hero(hero: HeroCreate, session: Session = Depends(get_session)):
    db_hero = Hero.model_validate(hero)
    session.add(db_hero)
    session.commit()
    session.refresh(db_hero)
    return db_hero

@router.get("/", response_model=list[HeroRead])
def read_heroes(
    offset: int = 0,
    limit: int = Query(default=100, le=100),
    session: Session = Depends(get_session),
):
    heroes = session.exec(select(Hero).offset(offset).limit(limit)).all()
    return heroes

@router.get("/{hero_id}", response_model=HeroRead)
def read_hero(hero_id: int, session: Session = Depends(get_session)):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    return hero

@router.patch("/{hero_id}", response_model=HeroRead)
def update_hero(
    hero_id: int,
    hero_update: HeroUpdate,
    session: Session = Depends(get_session),
):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")

    update_data = hero_update.model_dump(exclude_unset=True)
    hero.sqlmodel_update(update_data)
    session.add(hero)
    session.commit()
    session.refresh(hero)
    return hero

@router.delete("/{hero_id}")
def delete_hero(hero_id: int, session: Session = Depends(get_session)):
    hero = session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    session.delete(hero)
    session.commit()
    return {"ok": True}
```

## CRUD Router (Async)

```python
# routers/heroes.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlmodel import select
from database import get_session
from models.hero import Hero, HeroCreate, HeroRead, HeroUpdate

router = APIRouter(prefix="/heroes", tags=["heroes"])

@router.post("/", response_model=HeroRead)
async def create_hero(hero: HeroCreate, session: AsyncSession = Depends(get_session)):
    db_hero = Hero.model_validate(hero)
    session.add(db_hero)
    await session.commit()
    await session.refresh(db_hero)
    return db_hero

@router.get("/", response_model=list[HeroRead])
async def read_heroes(
    offset: int = 0,
    limit: int = Query(default=100, le=100),
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(Hero).offset(offset).limit(limit))
    return result.scalars().all()

@router.get("/{hero_id}", response_model=HeroRead)
async def read_hero(hero_id: int, session: AsyncSession = Depends(get_session)):
    hero = await session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    return hero

@router.patch("/{hero_id}", response_model=HeroRead)
async def update_hero(
    hero_id: int,
    hero_update: HeroUpdate,
    session: AsyncSession = Depends(get_session),
):
    hero = await session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")

    update_data = hero_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(hero, key, value)

    session.add(hero)
    await session.commit()
    await session.refresh(hero)
    return hero

@router.delete("/{hero_id}")
async def delete_hero(hero_id: int, session: AsyncSession = Depends(get_session)):
    hero = await session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    await session.delete(hero)
    await session.commit()
    return {"ok": True}
```

## Loading Relationships

```python
from sqlalchemy.orm import selectinload

@router.get("/{hero_id}/with-team", response_model=HeroReadWithTeam)
async def read_hero_with_team(hero_id: int, session: AsyncSession = Depends(get_session)):
    statement = select(Hero).where(Hero.id == hero_id).options(selectinload(Hero.team))
    result = await session.execute(statement)
    hero = result.scalar_one_or_none()
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    return hero
```

## Filtering and Search

```python
@router.get("/search/", response_model=list[HeroRead])
async def search_heroes(
    name: str | None = None,
    age_gt: int | None = None,
    age_lt: int | None = None,
    team_id: int | None = None,
    session: AsyncSession = Depends(get_session),
):
    statement = select(Hero)

    if name:
        statement = statement.where(Hero.name.ilike(f"%{name}%"))
    if age_gt:
        statement = statement.where(Hero.age > age_gt)
    if age_lt:
        statement = statement.where(Hero.age < age_lt)
    if team_id:
        statement = statement.where(Hero.team_id == team_id)

    result = await session.execute(statement)
    return result.scalars().all()
```

## Pagination Response

```python
from pydantic import BaseModel

class PaginatedResponse(BaseModel):
    items: list[HeroRead]
    total: int
    page: int
    page_size: int
    pages: int

@router.get("/paginated/", response_model=PaginatedResponse)
async def read_heroes_paginated(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=10, ge=1, le=100),
    session: AsyncSession = Depends(get_session),
):
    # Count total
    count_statement = select(func.count(Hero.id))
    total = (await session.execute(count_statement)).scalar_one()

    # Get page
    offset = (page - 1) * page_size
    statement = select(Hero).offset(offset).limit(page_size)
    result = await session.execute(statement)
    items = result.scalars().all()

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
        pages=(total + page_size - 1) // page_size,
    )
```

## Transaction Example

```python
@router.post("/transfer/{hero_id}")
async def transfer_hero(
    hero_id: int,
    new_team_id: int,
    session: AsyncSession = Depends(get_session),
):
    async with session.begin():
        hero = await session.get(Hero, hero_id)
        if not hero:
            raise HTTPException(status_code=404, detail="Hero not found")

        new_team = await session.get(Team, new_team_id)
        if not new_team:
            raise HTTPException(status_code=404, detail="Team not found")

        hero.team_id = new_team_id
        session.add(hero)
        # Commits automatically at end of 'begin' block

    return {"transferred": True}
```

## Error Handling

```python
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

@router.post("/", response_model=HeroRead)
async def create_hero(hero: HeroCreate, session: AsyncSession = Depends(get_session)):
    try:
        db_hero = Hero.model_validate(hero)
        session.add(db_hero)
        await session.commit()
        await session.refresh(db_hero)
        return db_hero
    except IntegrityError:
        await session.rollback()
        raise HTTPException(
            status_code=400,
            detail="Hero with this name already exists"
        )
```

## Testing with TestClient

```python
# tests/test_heroes.py
import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session
from sqlmodel.pool import StaticPool

from main import app
from database import get_session

@pytest.fixture(name="session")
def session_fixture():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture(name="client")
def client_fixture(session: Session):
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()

def test_create_hero(client: TestClient):
    response = client.post(
        "/heroes/",
        json={"name": "Spider-Man", "secret_name": "Peter Parker"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Spider-Man"
    assert "id" in data

def test_read_hero(client: TestClient, session: Session):
    hero = Hero(name="Iron Man", secret_name="Tony Stark")
    session.add(hero)
    session.commit()

    response = client.get(f"/heroes/{hero.id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Iron Man"
```
