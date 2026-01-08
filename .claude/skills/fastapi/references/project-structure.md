# FastAPI Project Structure & Best Practices

## Table of Contents
- [Project Layouts](#project-layouts)
- [Application Factory](#application-factory)
- [Routers](#routers)
- [Dependency Injection](#dependency-injection)
- [Error Handling](#error-handling)
- [Middleware](#middleware)
- [CORS](#cors)
- [Background Tasks](#background-tasks)
- [Lifespan Events](#lifespan-events)

---

## Project Layouts

### Small project
```
myproject/
├── main.py
├── models.py
├── schemas.py
├── database.py
├── requirements.txt
└── .env
```

### Medium project
```
myproject/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── user.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── user.py
│   ├── routers/
│   │   ├── __init__.py
│   │   └── users.py
│   ├── services/
│   │   ├── __init__.py
│   │   └── user_service.py
│   └── dependencies.py
├── tests/
├── requirements.txt
└── .env
```

### Large project
```
myproject/
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── security.py
│   │   └── database.py
│   ├── api/
│   │   ├── __init__.py
│   │   ├── deps.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py
│   │       └── endpoints/
│   │           ├── users.py
│   │           └── items.py
│   ├── models/
│   ├── schemas/
│   ├── services/
│   └── utils/
├── tests/
├── alembic/
├── docker-compose.yml
├── Dockerfile
└── pyproject.toml
```

---

## Application Factory

```python
# app/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.v1.router import api_router
from app.core.config import settings

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Starting up...")
    yield
    # Shutdown
    print("Shutting down...")

def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        lifespan=lifespan,
    )

    # Include routers
    app.include_router(api_router, prefix=settings.API_V1_STR)

    return app

app = create_app()
```

---

## Routers

### Define router (`app/api/v1/endpoints/users.py`)
```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.api import deps
from app import schemas, services

router = APIRouter()

@router.get("/", response_model=list[schemas.User])
def read_users(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(deps.get_db),
):
    return services.user.get_multi(db, skip=skip, limit=limit)

@router.post("/", response_model=schemas.User)
def create_user(
    user_in: schemas.UserCreate,
    db: Session = Depends(deps.get_db),
):
    user = services.user.get_by_email(db, email=user_in.email)
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    return services.user.create(db, obj_in=user_in)
```

### Combine routers (`app/api/v1/router.py`)
```python
from fastapi import APIRouter
from app.api.v1.endpoints import users, items, auth

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(items.router, prefix="/items", tags=["items"])
```

---

## Dependency Injection

### Common dependencies (`app/api/deps.py`)
```python
from typing import Generator, Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.core.security import decode_token
from app import models

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")

def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
) -> models.User:
    token_data = decode_token(token)
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )
    user = db.query(models.User).filter(models.User.id == token_data.sub).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Type aliases for cleaner signatures
DB = Annotated[Session, Depends(get_db)]
CurrentUser = Annotated[models.User, Depends(get_current_user)]
```

### Using dependencies
```python
@router.get("/me")
def read_current_user(current_user: CurrentUser):
    return current_user

@router.get("/items")
def read_items(db: DB, current_user: CurrentUser):
    return db.query(Item).filter(Item.owner_id == current_user.id).all()
```

---

## Error Handling

### Custom exceptions
```python
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

class AppException(Exception):
    def __init__(self, status_code: int, detail: str):
        self.status_code = status_code
        self.detail = detail

class NotFoundError(AppException):
    def __init__(self, resource: str):
        super().__init__(404, f"{resource} not found")

class ValidationError(AppException):
    def __init__(self, detail: str):
        super().__init__(422, detail)

# Exception handler
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

# Usage
@router.get("/users/{user_id}")
def get_user(user_id: int, db: DB):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise NotFoundError("User")
    return user
```

---

## Middleware

```python
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import time

app = FastAPI()

# Timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# Logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    print(f"{request.method} {request.url}")
    response = await call_next(request)
    print(f"Status: {response.status_code}")
    return response
```

---

## CORS

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://myapp.com"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Or allow all (development only)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Background Tasks

```python
from fastapi import BackgroundTasks

def send_email(email: str, message: str):
    # Simulate sending email
    print(f"Sending email to {email}: {message}")

@app.post("/users/")
async def create_user(
    user: UserCreate,
    background_tasks: BackgroundTasks,
    db: DB,
):
    db_user = create_user_in_db(db, user)
    background_tasks.add_task(send_email, user.email, "Welcome!")
    return db_user

# Multiple background tasks
@app.post("/items/")
async def create_item(item: ItemCreate, background_tasks: BackgroundTasks):
    background_tasks.add_task(log_operation, "create", item.name)
    background_tasks.add_task(notify_subscribers, item)
    return item
```

---

## Lifespan Events

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: runs before accepting requests
    print("Starting up...")
    app.state.db_pool = await create_db_pool()
    app.state.redis = await create_redis_connection()

    yield  # Application runs here

    # Shutdown: runs when application stops
    print("Shutting down...")
    await app.state.db_pool.close()
    await app.state.redis.close()

app = FastAPI(lifespan=lifespan)
```
