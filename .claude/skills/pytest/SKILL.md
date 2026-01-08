---
name: pytest
description: Run and write pytest tests for Python projects. Use when user wants to run tests, write new tests, debug failing tests, or check test coverage. Supports FastAPI, SQLModel, and general Python testing patterns.
---

# Pytest Testing Skill

This skill helps with running pytest tests, writing new tests, and debugging test failures in Python projects.

## When to Use This Skill

**Trigger conditions:**
- User mentions running tests: "run tests", "test this", "pytest"
- User wants to write tests: "write tests for", "add tests", "create test"
- User has failing tests: "tests failing", "fix test", "debug test"
- User mentions coverage: "test coverage", "coverage report"

## Running Tests

### Basic Commands

```bash
# Run all tests
uv run pytest

# Run with verbose output
uv run pytest -v

# Run specific test file
uv run pytest test_main.py

# Run specific test function
uv run pytest test_main.py::test_function_name

# Run tests matching pattern
uv run pytest -k "pattern"

# Run with print output visible
uv run pytest -s

# Run and stop on first failure
uv run pytest -x

# Run last failed tests only
uv run pytest --lf
```

### Coverage Commands

```bash
# Run with coverage report
uv run pytest --cov=. --cov-report=term-missing

# Generate HTML coverage report
uv run pytest --cov=. --cov-report=html
```

## Writing Tests for FastAPI + SQLModel

### Test File Structure

For FastAPI applications using SQLModel, use this pattern:

```python
import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.pool import StaticPool

from main import app, get_session, ModelName


@pytest.fixture(name="session")
def session_fixture():
    """Create an in-memory SQLite database for testing."""
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
    """Create a test client with dependency override."""
    def get_session_override():
        return session

    app.dependency_overrides[get_session] = get_session_override
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
```

### Test Naming Conventions

- Test files: `test_<module>.py`
- Test functions: `test_<what_is_being_tested>`
- Test classes: `Test<ClassName>`

### Common Test Patterns

#### Testing CRUD Endpoints

```python
def test_create_item(client: TestClient):
    response = client.post("/items", json={"name": "Test", "value": 123})
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test"
    assert data["id"] is not None


def test_get_item(client: TestClient):
    # First create
    create_response = client.post("/items", json={"name": "Test"})
    item_id = create_response.json()["id"]

    # Then get
    response = client.get(f"/items/{item_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Test"


def test_get_item_not_found(client: TestClient):
    response = client.get("/items/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Item not found"


def test_update_item(client: TestClient):
    # Create
    create_response = client.post("/items", json={"name": "Original"})
    item_id = create_response.json()["id"]

    # Update
    response = client.put(f"/items/{item_id}", json={"name": "Updated"})
    assert response.status_code == 200
    assert response.json()["name"] == "Updated"


def test_delete_item(client: TestClient):
    # Create
    create_response = client.post("/items", json={"name": "ToDelete"})
    item_id = create_response.json()["id"]

    # Delete
    response = client.delete(f"/items/{item_id}")
    assert response.status_code == 200

    # Verify deleted
    get_response = client.get(f"/items/{item_id}")
    assert get_response.status_code == 404
```

#### Testing with Authentication

```python
def test_protected_endpoint_unauthorized(client: TestClient):
    response = client.get("/protected")
    assert response.status_code == 401


def test_protected_endpoint_authorized(client: TestClient):
    # Login first
    login_response = client.post("/login", json={"username": "test", "password": "test"})
    token = login_response.json()["access_token"]

    # Access protected endpoint
    response = client.get(
        "/protected",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 200
```

#### Testing Validation Errors

```python
def test_create_item_invalid_data(client: TestClient):
    response = client.post("/items", json={"name": ""})  # Invalid: empty name
    assert response.status_code == 422  # Validation error
```

### Fixtures

#### Reusable Test Data

```python
@pytest.fixture
def sample_item(client: TestClient):
    """Create and return a sample item for tests."""
    response = client.post("/items", json={"name": "Sample", "value": 100})
    return response.json()


def test_with_sample_item(client: TestClient, sample_item):
    item_id = sample_item["id"]
    response = client.get(f"/items/{item_id}")
    assert response.status_code == 200
```

#### Parametrized Tests

```python
@pytest.mark.parametrize("name,expected_status", [
    ("ValidName", 200),
    ("", 422),
    (None, 422),
])
def test_create_with_various_names(client: TestClient, name, expected_status):
    response = client.post("/items", json={"name": name})
    assert response.status_code == expected_status
```

## Debugging Failing Tests

### Common Issues and Solutions

1. **Database state bleeding between tests**
   - Use fresh fixtures for each test
   - Ensure `session_fixture` creates new engine each time

2. **Import errors**
   - Check that `__init__.py` exists in test directories if needed
   - Verify module paths are correct

3. **Async test issues**
   - Use `pytest-asyncio` for async tests
   - Mark async tests with `@pytest.mark.asyncio`

4. **Dependency override not working**
   - Clear overrides in fixture teardown
   - Ensure override function returns (not yields) the dependency

### Debugging Commands

```bash
# Run with full traceback
uv run pytest --tb=long

# Run with debugger on failure
uv run pytest --pdb

# Show local variables in traceback
uv run pytest -l
```

## Project Setup

### Required Dependencies

Add to `pyproject.toml`:

```toml
[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "httpx>=0.27.0",
    "pytest-cov>=4.0.0",  # Optional: for coverage
]
```

### Install Dev Dependencies

```bash
uv sync --extra dev
```

## Best Practices

1. **Test one thing per test** - Keep tests focused and isolated
2. **Use descriptive names** - `test_create_user_with_invalid_email_returns_422`
3. **Arrange-Act-Assert** - Structure tests clearly
4. **Don't test implementation details** - Test behavior, not internal code
5. **Use fixtures for setup** - Keep test functions clean
6. **Test edge cases** - Empty inputs, not found, unauthorized, etc.
7. **Keep tests fast** - Use in-memory databases, mock external services
