# Testing FastAPI Applications

## Table of Contents
- [Setup](#setup)
- [Basic Testing](#basic-testing)
- [Testing with Database](#testing-with-database)
- [Testing Authentication](#testing-authentication)
- [Async Testing](#async-testing)
- [Fixtures and Factories](#fixtures-and-factories)
- [Coverage](#coverage)

---

## Setup

```bash
pip install pytest httpx pytest-asyncio
```

---

## Basic Testing

### Simple tests (`test_main.py`)
```python
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}

def test_read_item():
    response = client.get("/items/42")
    assert response.status_code == 200
    assert response.json()["item_id"] == 42

def test_create_item():
    response = client.post(
        "/items/",
        json={"name": "Test Item", "price": 10.5}
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Test Item"

def test_invalid_item():
    response = client.post(
        "/items/",
        json={"name": "Test"}  # Missing price
    )
    assert response.status_code == 422  # Validation error
```

---

## Testing with Database

### Override dependency
```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db

# Test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

client = TestClient(app)

def test_create_user():
    response = client.post(
        "/users/",
        json={"email": "test@example.com", "password": "testpass123"}
    )
    assert response.status_code == 200
    assert response.json()["email"] == "test@example.com"

def test_create_duplicate_user():
    client.post("/users/", json={"email": "test@example.com", "password": "pass123"})
    response = client.post("/users/", json={"email": "test@example.com", "password": "pass456"})
    assert response.status_code == 400
```

---

## Testing Authentication

```python
from fastapi.testclient import TestClient

client = TestClient(app)

def get_auth_token():
    response = client.post(
        "/token",
        data={"username": "testuser", "password": "testpass"}
    )
    return response.json()["access_token"]

def test_protected_route_no_auth():
    response = client.get("/users/me")
    assert response.status_code == 401

def test_protected_route_with_auth():
    token = get_auth_token()
    response = client.get(
        "/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"

def test_invalid_token():
    response = client.get(
        "/users/me",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401
```

---

## Async Testing

```python
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_async_root():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Hello World"}

@pytest.mark.asyncio
async def test_async_create_item():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post(
            "/items/",
            json={"name": "Async Item", "price": 25.0}
        )
    assert response.status_code == 201
```

### Pytest config (`conftest.py`)
```python
import pytest

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"
```

---

## Fixtures and Factories

### Conftest.py
```python
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.main import app
from app.database import Base, get_db

@pytest.fixture(scope="session")
def engine():
    return create_engine("sqlite:///./test.db", connect_args={"check_same_thread": False})

@pytest.fixture(scope="function")
def db_session(engine):
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(db_session):
    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()

@pytest.fixture
def test_user(client):
    response = client.post(
        "/users/",
        json={"email": "test@example.com", "password": "testpass123"}
    )
    return response.json()

@pytest.fixture
def auth_headers(client, test_user):
    response = client.post(
        "/token",
        data={"username": test_user["email"], "password": "testpass123"}
    )
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
```

### Using fixtures
```python
def test_get_current_user(client, auth_headers):
    response = client.get("/users/me", headers=auth_headers)
    assert response.status_code == 200

def test_create_item_for_user(client, auth_headers, test_user):
    response = client.post(
        "/items/",
        json={"name": "User Item", "price": 15.0},
        headers=auth_headers
    )
    assert response.status_code == 201
    assert response.json()["owner_id"] == test_user["id"]
```

---

## Coverage

```bash
pip install pytest-cov

# Run with coverage
pytest --cov=app --cov-report=html

# View coverage report
open htmlcov/index.html
```

### pytest.ini
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_functions = test_*
addopts = -v --cov=app --cov-report=term-missing
asyncio_mode = auto
```
