---
name: fastapi
description: Build FastAPI applications from hello world to production projects. Use when creating REST APIs, web backends, or microservices with Python. Covers routing, Pydantic models, databases (SQLAlchemy), authentication (JWT/OAuth2), testing, Docker deployment, and project structure best practices.
---

# FastAPI Development

Build production-ready FastAPI applications with professional structure, authentication, database integration and deployment configurations.

## Quick Start

```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Hello World"}
```

Run: `uvicorn main:app --reload`

Docs: `http://127.0.0.1:8000/docs`

## Workflow

```
┌─────────────────────────────────────────────────────────┐
│                   What do you need?                      │
└─────────────────────────────────────────────────────────┘
                           │
       ┌───────────────────┼───────────────────┐
       ▼                   ▼                   ▼
   New Project      Add Feature         Production
       │                   │                   │
       ▼                   ▼                   ▼
  Run init script    See references      See deployment
  scripts/init.py    for topic           reference
```

## Reference Guides

Load the appropriate reference based on the task:

| Task                          | Reference File                                                     |
| ----------------------------- | ------------------------------------------------------------------ |
| Routing, params, responses    | [references/basics.md](references/basics.md)                       |
| Pydantic models, validation   | [references/models.md](references/models.md)                       |
| SQLAlchemy, async DB, MongoDB | [references/databases.md](references/databases.md)                 |
| JWT, OAuth2, API keys, RBAC   | [references/auth.md](references/auth.md)                           |
| pytest, TestClient, fixtures  | [references/testing.md](references/testing.md)                     |
| Docker, Nginx, cloud deploy   | [references/deployment.md](references/deployment.md)               |
| Project layout, routers, DI   | [references/project-structure.md](references/project-structure.md) |

## Project Initialization

For new projects, run the initialization script:

```bash
python scripts/init.py <project-name> [--template minimal|standard|full]
```

Templates:

- `minimal` - Single main.py file
- `standard` - Basic app structure with routers (default)
- `full` - Production-ready with auth, DB, tests, Docker

## Common Patterns

### Add a new endpoint

```python
@app.get("/items/{item_id}")
def get_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "q": q}
```

### Add request validation

```python
from pydantic import BaseModel, Field

class Item(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    price: float = Field(gt=0)

@app.post("/items")
def create_item(item: Item):
    return item
```

### Add database model

```python
from sqlalchemy import Column, Integer, String
from database import Base

class Item(Base):
    __tablename__ = "items"
    id = Column(Integer, primary_key=True)
    name = Column(String, index=True)
```

### Protect a route

```python
from fastapi import Depends
from auth import get_current_user

@app.get("/protected")
def protected_route(user = Depends(get_current_user)):
    return {"user": user.email}
```

## Installation

```bash
# Full install (recommended)
pip install "fastapi[standard]"

# With database
pip install sqlalchemy alembic

# With auth
pip install python-jose[cryptography] passlib[bcrypt]

# For testing
pip install pytest httpx
```
