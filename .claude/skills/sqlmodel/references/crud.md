# SQLModel - CRUD Operations

## Setup

```python
from sqlmodel import SQLModel, Field, Session, create_engine, select

class Hero(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    secret_name: str
    age: int | None = None

engine = create_engine("sqlite:///database.db", echo=True)
SQLModel.metadata.create_all(engine)
```

## Create (INSERT)

### Single Record

```python
with Session(engine) as session:
    hero = Hero(name="Spider-Man", secret_name="Peter Parker", age=25)
    session.add(hero)
    session.commit()
    session.refresh(hero)  # Get auto-generated id
    print(hero.id)  # Now has the id from database
```

### Multiple Records

```python
with Session(engine) as session:
    heroes = [
        Hero(name="Iron Man", secret_name="Tony Stark", age=45),
        Hero(name="Thor", secret_name="Thor Odinson", age=1500),
        Hero(name="Black Widow", secret_name="Natasha", age=35),
    ]
    session.add_all(heroes)
    session.commit()
```

## Read (SELECT)

### Get by Primary Key

```python
with Session(engine) as session:
    hero = session.get(Hero, 1)  # Get hero with id=1
    if hero:
        print(hero.name)
```

### Select All

```python
with Session(engine) as session:
    statement = select(Hero)
    heroes = session.exec(statement).all()
    for hero in heroes:
        print(hero.name)
```

### Select First / One

```python
with Session(engine) as session:
    # First result (or None)
    statement = select(Hero).where(Hero.name == "Spider-Man")
    hero = session.exec(statement).first()

    # Exactly one result (raises if 0 or >1)
    hero = session.exec(statement).one()

    # One or None (raises if >1)
    hero = session.exec(statement).one_or_none()
```

### Filtering (WHERE)

```python
with Session(engine) as session:
    # Single condition
    statement = select(Hero).where(Hero.age > 30)

    # Multiple conditions (AND)
    statement = select(Hero).where(Hero.age > 30, Hero.name.startswith("I"))

    # OR conditions
    from sqlmodel import or_
    statement = select(Hero).where(or_(Hero.age > 30, Hero.name == "Thor"))

    # IN clause
    statement = select(Hero).where(Hero.name.in_(["Iron Man", "Thor"]))

    # IS NULL / IS NOT NULL
    statement = select(Hero).where(Hero.age == None)
    statement = select(Hero).where(Hero.age != None)

    # LIKE
    statement = select(Hero).where(Hero.name.like("%Man%"))
    statement = select(Hero).where(Hero.name.ilike("%man%"))  # Case-insensitive

    heroes = session.exec(statement).all()
```

### Ordering

```python
with Session(engine) as session:
    # Ascending
    statement = select(Hero).order_by(Hero.name)

    # Descending
    statement = select(Hero).order_by(Hero.age.desc())

    # Multiple columns
    statement = select(Hero).order_by(Hero.age.desc(), Hero.name)

    heroes = session.exec(statement).all()
```

### Pagination (LIMIT / OFFSET)

```python
with Session(engine) as session:
    page = 1
    page_size = 10

    statement = (
        select(Hero)
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    heroes = session.exec(statement).all()
```

### Select Specific Columns

```python
with Session(engine) as session:
    # Select specific columns (returns tuples)
    statement = select(Hero.name, Hero.age)
    results = session.exec(statement).all()
    for name, age in results:
        print(f"{name}: {age}")
```

### Aggregations

```python
from sqlalchemy import func

with Session(engine) as session:
    # Count
    statement = select(func.count(Hero.id))
    count = session.exec(statement).one()

    # Average
    statement = select(func.avg(Hero.age))
    avg_age = session.exec(statement).one()

    # Sum, Min, Max
    statement = select(
        func.sum(Hero.age),
        func.min(Hero.age),
        func.max(Hero.age)
    )
    total, min_age, max_age = session.exec(statement).one()
```

### Group By

```python
with Session(engine) as session:
    statement = (
        select(Hero.team_id, func.count(Hero.id))
        .group_by(Hero.team_id)
    )
    results = session.exec(statement).all()
```

## Update

### Update Single Record

```python
with Session(engine) as session:
    hero = session.get(Hero, 1)
    if hero:
        hero.age = 26
        session.add(hero)
        session.commit()
        session.refresh(hero)
```

### Partial Update (from dict)

```python
with Session(engine) as session:
    hero = session.get(Hero, 1)
    if hero:
        update_data = {"age": 27, "name": "Spider-Man 2"}
        for key, value in update_data.items():
            if value is not None:
                setattr(hero, key, value)
        session.add(hero)
        session.commit()
```

### Bulk Update

```python
from sqlalchemy import update

with Session(engine) as session:
    statement = (
        update(Hero)
        .where(Hero.age < 30)
        .values(age=Hero.age + 1)
    )
    session.exec(statement)
    session.commit()
```

## Delete

### Delete Single Record

```python
with Session(engine) as session:
    hero = session.get(Hero, 1)
    if hero:
        session.delete(hero)
        session.commit()
```

### Bulk Delete

```python
from sqlalchemy import delete

with Session(engine) as session:
    statement = delete(Hero).where(Hero.age > 100)
    session.exec(statement)
    session.commit()
```

## Transactions

### Basic Transaction

```python
with Session(engine) as session:
    try:
        hero1 = Hero(name="Hero 1", secret_name="Secret 1")
        hero2 = Hero(name="Hero 2", secret_name="Secret 2")
        session.add_all([hero1, hero2])
        session.commit()
    except Exception:
        session.rollback()
        raise
```

### Nested Transaction (Savepoint)

```python
with Session(engine) as session:
    hero1 = Hero(name="Hero 1", secret_name="Secret 1")
    session.add(hero1)

    # Create savepoint
    session.begin_nested()
    try:
        hero2 = Hero(name="Hero 2", secret_name="Secret 2")
        session.add(hero2)
        # This will rollback to savepoint, not the whole transaction
        raise ValueError("Oops")
    except ValueError:
        session.rollback()

    # hero1 is still staged
    session.commit()  # Only hero1 is committed
```

## Query Patterns

### Exists Check

```python
with Session(engine) as session:
    statement = select(Hero).where(Hero.name == "Spider-Man")
    exists = session.exec(statement).first() is not None
```

### Get or Create

```python
def get_or_create(session: Session, name: str, **kwargs) -> tuple[Hero, bool]:
    statement = select(Hero).where(Hero.name == name)
    hero = session.exec(statement).first()

    if hero:
        return hero, False

    hero = Hero(name=name, **kwargs)
    session.add(hero)
    session.commit()
    session.refresh(hero)
    return hero, True
```

### Update or Create (Upsert)

```python
def update_or_create(session: Session, id: int, **kwargs) -> Hero:
    hero = session.get(Hero, id)

    if hero:
        for key, value in kwargs.items():
            setattr(hero, key, value)
    else:
        hero = Hero(id=id, **kwargs)

    session.add(hero)
    session.commit()
    session.refresh(hero)
    return hero
```

## Common Pitfalls

| Pitfall | Problem | Solution |
|---------|---------|----------|
| Forgetting `refresh()` | Auto-generated values not loaded | Call `session.refresh(obj)` after commit |
| Accessing expired objects | Object not usable outside session | Refresh or use `expire_on_commit=False` |
| N+1 queries | Slow relationship loading | Use `selectinload()` or `joinedload()` |
| Not committing | Changes lost | Always `commit()` to persist changes |
