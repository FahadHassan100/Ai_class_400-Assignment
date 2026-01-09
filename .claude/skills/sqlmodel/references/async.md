# SQLModel - Async Operations

## Installation

```bash
# PostgreSQL async
pip install asyncpg

# SQLite async
pip install aiosqlite

# MySQL async
pip install aiomysql
```

## Connection Strings

| Database | Async Connection String |
|----------|------------------------|
| PostgreSQL | `postgresql+asyncpg://user:pass@localhost:5432/db` |
| SQLite | `sqlite+aiosqlite:///./database.db` |
| MySQL | `mysql+aiomysql://user:pass@localhost:3306/db` |

## Async Engine Setup

```python
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlmodel import SQLModel

DATABASE_URL = "postgresql+asyncpg://user:pass@localhost:5432/db"

async_engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Log SQL statements
    pool_size=5,
    max_overflow=10,
)

# Async session factory
async_session_maker = sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
```

## Create Tables (Async)

```python
async def create_db_and_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)

# Call at startup
import asyncio
asyncio.run(create_db_and_tables())
```

## Async Session Context Manager

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def get_async_session():
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
```

## CRUD Operations (Async)

### Create

```python
from sqlmodel import select

async def create_hero(name: str, secret_name: str, age: int | None = None) -> Hero:
    async with get_async_session() as session:
        hero = Hero(name=name, secret_name=secret_name, age=age)
        session.add(hero)
        await session.commit()
        await session.refresh(hero)
        return hero
```

### Read

```python
async def get_hero(hero_id: int) -> Hero | None:
    async with get_async_session() as session:
        return await session.get(Hero, hero_id)

async def get_heroes() -> list[Hero]:
    async with get_async_session() as session:
        result = await session.execute(select(Hero))
        return result.scalars().all()

async def get_heroes_by_age(min_age: int) -> list[Hero]:
    async with get_async_session() as session:
        statement = select(Hero).where(Hero.age >= min_age)
        result = await session.execute(statement)
        return result.scalars().all()
```

### Update

```python
async def update_hero(hero_id: int, **kwargs) -> Hero | None:
    async with get_async_session() as session:
        hero = await session.get(Hero, hero_id)
        if not hero:
            return None

        for key, value in kwargs.items():
            if value is not None:
                setattr(hero, key, value)

        session.add(hero)
        await session.commit()
        await session.refresh(hero)
        return hero
```

### Delete

```python
async def delete_hero(hero_id: int) -> bool:
    async with get_async_session() as session:
        hero = await session.get(Hero, hero_id)
        if not hero:
            return False

        await session.delete(hero)
        await session.commit()
        return True
```

## FastAPI Integration (Async)

```python
from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

app = FastAPI()

# Dependency
async def get_session() -> AsyncSession:
    async with async_session_maker() as session:
        yield session

# Lifespan for startup/shutdown
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables
    async with async_engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)
    yield
    # Shutdown: dispose engine
    await async_engine.dispose()

app = FastAPI(lifespan=lifespan)

# Routes
@app.post("/heroes", response_model=HeroRead)
async def create_hero(hero: HeroCreate, session: AsyncSession = Depends(get_session)):
    db_hero = Hero.model_validate(hero)
    session.add(db_hero)
    await session.commit()
    await session.refresh(db_hero)
    return db_hero

@app.get("/heroes", response_model=list[HeroRead])
async def read_heroes(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Hero))
    return result.scalars().all()

@app.get("/heroes/{hero_id}", response_model=HeroRead)
async def read_hero(hero_id: int, session: AsyncSession = Depends(get_session)):
    hero = await session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")
    return hero

@app.patch("/heroes/{hero_id}", response_model=HeroRead)
async def update_hero(
    hero_id: int,
    hero_update: HeroUpdate,
    session: AsyncSession = Depends(get_session)
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

@app.delete("/heroes/{hero_id}")
async def delete_hero(hero_id: int, session: AsyncSession = Depends(get_session)):
    hero = await session.get(Hero, hero_id)
    if not hero:
        raise HTTPException(status_code=404, detail="Hero not found")

    await session.delete(hero)
    await session.commit()
    return {"deleted": True}
```

## Eager Loading (Async)

```python
from sqlalchemy.orm import selectinload, joinedload

async def get_teams_with_heroes() -> list[Team]:
    async with get_async_session() as session:
        statement = select(Team).options(selectinload(Team.heroes))
        result = await session.execute(statement)
        return result.scalars().all()

async def get_heroes_with_team() -> list[Hero]:
    async with get_async_session() as session:
        statement = select(Hero).options(joinedload(Hero.team))
        result = await session.execute(statement)
        return result.scalars().unique().all()
```

## Transactions (Async)

```python
async def transfer_hero(hero_id: int, from_team_id: int, to_team_id: int):
    async with get_async_session() as session:
        async with session.begin():
            hero = await session.get(Hero, hero_id)
            if hero and hero.team_id == from_team_id:
                hero.team_id = to_team_id
                session.add(hero)
            # Commits automatically at end of 'begin' block
```

## Connection Pool Configuration

```python
async_engine = create_async_engine(
    DATABASE_URL,
    echo=False,

    # Pool settings
    pool_size=5,           # Number of persistent connections
    max_overflow=10,       # Additional connections when pool is exhausted
    pool_timeout=30,       # Seconds to wait for connection
    pool_recycle=1800,     # Recycle connections after 30 minutes
    pool_pre_ping=True,    # Test connections before use
)
```

## Key Differences: Sync vs Async

| Operation | Sync | Async |
|-----------|------|-------|
| Create engine | `create_engine()` | `create_async_engine()` |
| Session class | `Session` | `AsyncSession` |
| Execute query | `session.exec()` | `await session.execute()` |
| Get by ID | `session.get()` | `await session.get()` |
| Commit | `session.commit()` | `await session.commit()` |
| Refresh | `session.refresh()` | `await session.refresh()` |
| Create tables | `metadata.create_all()` | `await conn.run_sync(metadata.create_all)` |
| Result access | `.all()` | `.scalars().all()` |

## Common Async Pitfalls

| Pitfall | Problem | Solution |
|---------|---------|----------|
| Using sync engine | Blocks event loop | Use `create_async_engine` |
| Forgetting `await` | Coroutine never runs | Always `await` async operations |
| Wrong driver | Connection fails | Use async drivers (asyncpg, aiosqlite) |
| Session leak | Connections exhausted | Use context managers |
| Lazy loading | Sync I/O in async context | Use eager loading options |
