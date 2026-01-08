#!/usr/bin/env python3
"""
FastAPI Project Initializer

Creates a new FastAPI project with configurable templates.

Usage:
    python init.py <project-name> [--template minimal|standard|full]
"""

import argparse
import os
from pathlib import Path

TEMPLATES = {
    "minimal": {
        "files": {
            "main.py": '''from fastapi import FastAPI

app = FastAPI()


@app.get("/")
def root():
    return {"message": "Hello World"}


@app.get("/health")
def health():
    return {"status": "healthy"}
''',
            "requirements.txt": '''fastapi[standard]>=0.109.0
''',
            ".gitignore": '''__pycache__/
*.py[cod]
.env
.venv/
venv/
''',
        }
    },
    "standard": {
        "files": {
            "app/__init__.py": "",
            "app/main.py": '''from fastapi import FastAPI
from app.routers import items, users

app = FastAPI(title="My API", version="0.1.0")

app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(items.router, prefix="/items", tags=["items"])


@app.get("/")
def root():
    return {"message": "Welcome to the API"}


@app.get("/health")
def health():
    return {"status": "healthy"}
''',
            "app/config.py": '''from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    app_name: str = "My API"
    debug: bool = False

    model_config = {"env_file": ".env"}


@lru_cache
def get_settings():
    return Settings()
''',
            "app/routers/__init__.py": "",
            "app/routers/users.py": '''from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def list_users():
    return []


@router.get("/{user_id}")
def get_user(user_id: int):
    return {"id": user_id}
''',
            "app/routers/items.py": '''from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class Item(BaseModel):
    name: str
    price: float
    description: str | None = None


@router.get("/")
def list_items():
    return []


@router.post("/")
def create_item(item: Item):
    return item
''',
            "app/schemas/__init__.py": "",
            "requirements.txt": '''fastapi[standard]>=0.109.0
pydantic-settings>=2.0.0
''',
            ".env.example": '''DEBUG=false
''',
            ".gitignore": '''__pycache__/
*.py[cod]
.env
.venv/
venv/
''',
        }
    },
    "full": {
        "files": {
            "app/__init__.py": "",
            "app/main.py": '''from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.router import api_router
from app.core.database import engine, Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/health")
def health():
    return {"status": "healthy"}
''',
            "app/core/__init__.py": "",
            "app/core/config.py": '''from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    PROJECT_NAME: str = "My API"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False

    DATABASE_URL: str = "sqlite:///./app.db"
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    CORS_ORIGINS: list[str] = ["http://localhost:3000"]

    model_config = {"env_file": ".env"}


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()
''',
            "app/core/database.py": '''from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.config import settings

engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in settings.DATABASE_URL else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
''',
            "app/core/security.py": '''from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.core.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None
''',
            "app/api/__init__.py": "",
            "app/api/deps.py": '''from typing import Annotated, Generator
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.security import decode_token
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/token")

DB = Annotated[Session, Depends(get_db)]


async def get_current_user(
    db: DB,
    token: str = Depends(oauth2_scheme),
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    user_id: int = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise credentials_exception
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
''',
            "app/api/v1/__init__.py": "",
            "app/api/v1/router.py": '''from fastapi import APIRouter
from app.api.v1.endpoints import auth, users, items

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(items.router, prefix="/items", tags=["items"])
''',
            "app/api/v1/endpoints/__init__.py": "",
            "app/api/v1/endpoints/auth.py": '''from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from app.api.deps import DB
from app.core.security import verify_password, create_access_token
from app.core.config import settings
from app.models.user import User
from app.schemas.auth import Token

router = APIRouter()


@router.post("/token", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(DB)):
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": access_token, "token_type": "bearer"}
''',
            "app/api/v1/endpoints/users.py": '''from fastapi import APIRouter, HTTPException
from app.api.deps import DB, CurrentUser
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse
from app.core.security import hash_password

router = APIRouter()


@router.get("/me", response_model=UserResponse)
def read_current_user(current_user: CurrentUser):
    return current_user


@router.post("/", response_model=UserResponse)
def create_user(user_in: UserCreate, db: DB):
    existing = db.query(User).filter(User.email == user_in.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")
    user = User(
        email=user_in.email,
        hashed_password=hash_password(user_in.password),
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
''',
            "app/api/v1/endpoints/items.py": '''from fastapi import APIRouter, HTTPException
from app.api.deps import DB, CurrentUser
from app.models.item import Item
from app.schemas.item import ItemCreate, ItemResponse

router = APIRouter()


@router.get("/", response_model=list[ItemResponse])
def list_items(db: DB, skip: int = 0, limit: int = 100):
    return db.query(Item).offset(skip).limit(limit).all()


@router.post("/", response_model=ItemResponse)
def create_item(item_in: ItemCreate, db: DB, current_user: CurrentUser):
    item = Item(**item_in.model_dump(), owner_id=current_user.id)
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/{item_id}", response_model=ItemResponse)
def get_item(item_id: int, db: DB):
    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return item
''',
            "app/models/__init__.py": "",
            "app/models/user.py": '''from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    items = relationship("Item", back_populates="owner")
''',
            "app/models/item.py": '''from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base


class Item(Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True, nullable=False)
    description = Column(String)
    price = Column(Float, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="items")
''',
            "app/schemas/__init__.py": "",
            "app/schemas/auth.py": '''from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str
''',
            "app/schemas/user.py": '''from pydantic import BaseModel, EmailStr, ConfigDict


class UserCreate(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    is_active: bool

    model_config = ConfigDict(from_attributes=True)
''',
            "app/schemas/item.py": '''from pydantic import BaseModel, ConfigDict


class ItemCreate(BaseModel):
    name: str
    description: str | None = None
    price: float


class ItemResponse(BaseModel):
    id: int
    name: str
    description: str | None
    price: float
    owner_id: int

    model_config = ConfigDict(from_attributes=True)
''',
            "tests/__init__.py": "",
            "tests/conftest.py": '''import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.core.database import Base, get_db

SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
''',
            "tests/test_health.py": '''def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}
''',
            "Dockerfile": '''FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
''',
            "docker-compose.yml": '''version: '3.8'

services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=sqlite:///./app.db
    volumes:
      - .:/app
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
''',
            "requirements.txt": '''fastapi[standard]>=0.109.0
pydantic-settings>=2.0.0
sqlalchemy>=2.0.0
python-jose[cryptography]>=3.3.0
passlib[bcrypt]>=1.7.4
pytest>=7.0.0
httpx>=0.25.0
''',
            ".env.example": '''DEBUG=false
DATABASE_URL=sqlite:///./app.db
SECRET_KEY=change-me-in-production
''',
            ".gitignore": '''__pycache__/
*.py[cod]
.env
.venv/
venv/
*.db
htmlcov/
.coverage
''',
        }
    },
}


def create_project(name: str, template: str) -> None:
    """Create a new FastAPI project with the specified template."""
    project_path = Path(name)

    if project_path.exists():
        print(f"Error: Directory '{name}' already exists")
        return

    template_data = TEMPLATES.get(template)
    if not template_data:
        print(f"Error: Unknown template '{template}'")
        return

    print(f"Creating FastAPI project '{name}' with '{template}' template...")

    for file_path, content in template_data["files"].items():
        full_path = project_path / file_path
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text(content)
        print(f"  Created: {file_path}")

    print(f"\n✅ Project '{name}' created successfully!")
    print(f"\nNext steps:")
    print(f"  cd {name}")
    print(f"  python -m venv venv")
    print(f"  source venv/bin/activate  # On Windows: venv\\Scripts\\activate")
    print(f"  pip install -r requirements.txt")
    if template == "full":
        print(f"  cp .env.example .env")
    print(f"  uvicorn {'app.main' if template != 'minimal' else 'main'}:app --reload")


def main():
    parser = argparse.ArgumentParser(description="Initialize a new FastAPI project")
    parser.add_argument("name", help="Project name")
    parser.add_argument(
        "--template",
        choices=["minimal", "standard", "full"],
        default="standard",
        help="Project template (default: standard)",
    )
    args = parser.parse_args()
    create_project(args.name, args.template)


if __name__ == "__main__":
    main()
