# SQLModel - Relationships

## One-to-Many Relationship

A team has many heroes, each hero belongs to one team.

```python
from sqlmodel import SQLModel, Field, Relationship

class Team(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    headquarters: str

    # One team -> Many heroes
    heroes: list["Hero"] = Relationship(back_populates="team")

class Hero(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    secret_name: str

    # Foreign key to team
    team_id: int | None = Field(default=None, foreign_key="team.id")

    # Many heroes -> One team
    team: Team | None = Relationship(back_populates="heroes")
```

### Using One-to-Many

```python
# Create team with heroes
team = Team(name="Avengers", headquarters="NYC")
hero1 = Hero(name="Iron Man", secret_name="Tony", team=team)
hero2 = Hero(name="Thor", secret_name="Thor", team=team)

session.add(team)
session.commit()

# Access relationship
team = session.get(Team, 1)
for hero in team.heroes:
    print(hero.name)

# Access reverse
hero = session.get(Hero, 1)
print(hero.team.name)
```

## Many-to-Many Relationship

Heroes can belong to multiple teams, teams can have multiple heroes.

```python
from sqlmodel import SQLModel, Field, Relationship

# Link table (required for many-to-many)
class HeroTeamLink(SQLModel, table=True):
    hero_id: int = Field(foreign_key="hero.id", primary_key=True)
    team_id: int = Field(foreign_key="team.id", primary_key=True)

class Team(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str

    heroes: list["Hero"] = Relationship(
        back_populates="teams",
        link_model=HeroTeamLink
    )

class Hero(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str

    teams: list[Team] = Relationship(
        back_populates="heroes",
        link_model=HeroTeamLink
    )
```

### Using Many-to-Many

```python
# Create and link
team1 = Team(name="Avengers")
team2 = Team(name="X-Men")
hero = Hero(name="Wolverine", teams=[team1, team2])

session.add(hero)
session.commit()

# Access both directions
hero = session.get(Hero, 1)
for team in hero.teams:
    print(team.name)

team = session.get(Team, 1)
for hero in team.heroes:
    print(hero.name)
```

## Link Table with Extra Fields

When the relationship itself has data.

```python
from datetime import datetime

class HeroTeamLink(SQLModel, table=True):
    hero_id: int = Field(foreign_key="hero.id", primary_key=True)
    team_id: int = Field(foreign_key="team.id", primary_key=True)

    # Extra fields on the relationship
    joined_at: datetime = Field(default_factory=datetime.utcnow)
    is_leader: bool = Field(default=False)
    role: str | None = None

    # Relationships to access the linked objects
    hero: "Hero" = Relationship(back_populates="team_links")
    team: "Team" = Relationship(back_populates="hero_links")

class Team(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str

    hero_links: list[HeroTeamLink] = Relationship(back_populates="team")

class Hero(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str

    team_links: list[HeroTeamLink] = Relationship(back_populates="hero")
```

### Using Link Table with Extra Fields

```python
# Create with extra data
hero = Hero(name="Captain America")
team = Team(name="Avengers")

session.add_all([hero, team])
session.commit()

# Create the link with extra fields
link = HeroTeamLink(
    hero_id=hero.id,
    team_id=team.id,
    is_leader=True,
    role="Team Leader"
)
session.add(link)
session.commit()

# Query the link data
for link in hero.team_links:
    print(f"{link.team.name}: {link.role}, Leader: {link.is_leader}")
```

## Self-Referential Relationship

E.g., manager-employee hierarchy.

```python
class Employee(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str

    # Self-referential FK
    manager_id: int | None = Field(default=None, foreign_key="employee.id")

    # Relationships
    manager: "Employee" | None = Relationship(
        back_populates="reports",
        sa_relationship_kwargs={"remote_side": "Employee.id"}
    )
    reports: list["Employee"] = Relationship(back_populates="manager")
```

## Cascade Delete

```python
from sqlmodel import Relationship

class Team(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str

    # Delete heroes when team is deleted
    heroes: list["Hero"] = Relationship(
        back_populates="team",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
```

## Lazy Loading vs Eager Loading

### Lazy Loading (Default)

Relationships loaded when accessed - causes N+1 queries.

```python
# N+1 problem: 1 query for teams + N queries for heroes
teams = session.exec(select(Team)).all()
for team in teams:
    print(team.heroes)  # Each access triggers a query
```

### Eager Loading (Recommended)

Load relationships upfront.

```python
from sqlmodel import select
from sqlalchemy.orm import selectinload, joinedload

# selectinload: Separate query for relationships (recommended for collections)
statement = select(Team).options(selectinload(Team.heroes))
teams = session.exec(statement).all()

# joinedload: Single JOIN query (good for single relationships)
statement = select(Hero).options(joinedload(Hero.team))
heroes = session.exec(statement).all()

# Nested eager loading
statement = select(Team).options(
    selectinload(Team.heroes).selectinload(Hero.weapons)
)
```

## Relationship Patterns Summary

| Pattern | Use Case | Key Config |
|---------|----------|------------|
| One-to-Many | Parent-children | `foreign_key` on child, `Relationship` on both |
| Many-to-Many | Tags, categories | `link_model` in `Relationship` |
| Link with fields | Membership with data | Explicit link model with extra columns |
| Self-referential | Hierarchies | `remote_side` in kwargs |
| Cascade delete | Auto-cleanup | `cascade="all, delete-orphan"` |

## Querying Relationships

```python
from sqlmodel import select

# Filter by related field
statement = select(Hero).where(Hero.team.has(Team.name == "Avengers"))
heroes = session.exec(statement).all()

# Filter by existence of relationship
statement = select(Hero).where(Hero.team != None)
heroes_with_team = session.exec(statement).all()

# Filter collection contains
statement = select(Team).where(Team.heroes.any(Hero.name == "Iron Man"))
teams = session.exec(statement).all()

# Join query
statement = (
    select(Hero, Team)
    .join(Team)
    .where(Team.name == "Avengers")
)
results = session.exec(statement).all()
```
