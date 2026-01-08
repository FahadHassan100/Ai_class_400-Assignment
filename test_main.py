import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from sqlmodel.pool import StaticPool

from main import app, get_session, Todo


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


def test_create_todo(client: TestClient):
    response = client.post(
        "/createTodo",
        json={"title": "Test Todo", "description": "Test Description"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Test Todo"
    assert data["description"] == "Test Description"
    assert data["id"] is not None


def test_get_all_todos(client: TestClient):
    client.post("/createTodo", json={"title": "Todo 1", "description": "Desc 1"})
    client.post("/createTodo", json={"title": "Todo 2", "description": "Desc 2"})

    response = client.get("/allTodo")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["title"] == "Todo 1"
    assert data[1]["title"] == "Todo 2"


def test_get_todo_by_id(client: TestClient):
    create_response = client.post(
        "/createTodo",
        json={"title": "Find Me", "description": "Find this todo"},
    )
    todo_id = create_response.json()["id"]

    response = client.get(f"/todo/{todo_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Find Me"
    assert data["description"] == "Find this todo"


def test_get_todo_by_id_not_found(client: TestClient):
    response = client.get("/todo/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Todo not found"


def test_update_todo(client: TestClient):
    create_response = client.post(
        "/createTodo",
        json={"title": "Original Title", "description": "Original Desc"},
    )
    todo_id = create_response.json()["id"]

    response = client.put(
        f"/todo/{todo_id}",
        json={"title": "Updated Title", "description": "Updated Desc"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Updated Title"
    assert data["description"] == "Updated Desc"


def test_update_todo_partial(client: TestClient):
    create_response = client.post(
        "/createTodo",
        json={"title": "Original Title", "description": "Original Desc"},
    )
    todo_id = create_response.json()["id"]

    response = client.put(f"/todo/{todo_id}", json={"title": "Only Title Updated"})
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Only Title Updated"
    assert data["description"] == "Original Desc"


def test_update_todo_not_found(client: TestClient):
    response = client.put("/todo/999", json={"title": "New Title"})
    assert response.status_code == 404
    assert response.json()["detail"] == "Todo not found"


def test_delete_todo(client: TestClient):
    create_response = client.post(
        "/createTodo",
        json={"title": "Delete Me", "description": "To be deleted"},
    )
    todo_id = create_response.json()["id"]

    response = client.delete(f"/todo/{todo_id}")
    assert response.status_code == 200
    assert response.json()["message"] == "Todo deleted successfully"

    get_response = client.get(f"/todo/{todo_id}")
    assert get_response.status_code == 404


def test_delete_todo_not_found(client: TestClient):
    response = client.delete("/todo/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "Todo not found"
