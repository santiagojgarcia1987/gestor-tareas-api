# Tests para los endpoints de tareas

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from aplicacion.base_de_datos import Base, get_db
from aplicacion.principal import app

# Motor en memoria con StaticPool para aislamiento entre tests
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client():
    return TestClient(app)


def _create_task(client, **kwargs):
    payload = {"title": "Sample task"}
    payload.update(kwargs)
    resp = client.post("/tasks/", json=payload)
    assert resp.status_code == 201
    return resp.json()


def test_update_task_with_done_status_returns_400(client):
    """Modificar una tarea con estado done debe devolver 400."""
    task = _create_task(client, status="done")
    resp = client.patch(f"/tasks/{task['id']}", json={"title": "New title"})
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Cannot update a completed task"


def test_update_task_pending_allows_changes(client):
    """Modificar una tarea pendiente debe funcionar correctamente."""
    task = _create_task(client)
    resp = client.patch(
        f"/tasks/{task['id']}", json={"title": "Updated", "status": "in_progress"}
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["title"] == "Updated"
    assert data["status"] == "in_progress"


def test_update_task_in_progress_to_done(client):
    """Cambiar una tarea de in_progress a done debe ser v\u00e1lido."""
    task = _create_task(client, status="in_progress")
    resp = client.patch(f"/tasks/{task['id']}", json={"status": "done"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "done"


def test_update_done_task_status_field_returns_400(client):
    """Intentar cambiar solo el estado de una tarea done devuelve 400."""
    task = _create_task(client, status="done")
    resp = client.patch(f"/tasks/{task['id']}", json={"status": "pending"})
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Cannot update a completed task"


def test_update_task_set_to_done_then_reject_further_updates(client):
    """Flujo end-to-end: crear, completar y verificar rechazo posterior."""
    task = _create_task(client)
    resp = client.patch(f"/tasks/{task['id']}", json={"status": "done"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "done"

    resp = client.patch(f"/tasks/{task['id']}", json={"title": "Hacked"})
    assert resp.status_code == 400
    assert resp.json()["detail"] == "Cannot update a completed task"


def test_delete_all_tasks_removes_every_task(client):
    """Eliminar todas las tareas deja la lista vacía."""
    _create_task(client, title="Task 1")
    _create_task(client, title="Task 2")
    _create_task(client, title="Task 3")

    resp = client.delete("/tasks/")
    assert resp.status_code == 204

    resp = client.get("/tasks/")
    assert resp.status_code == 200
    assert resp.json() == []


def test_delete_all_tasks_empty_db_returns_404(client):
    """Intentar eliminar todas las tareas sin tareas existentes devuelve 404."""
    resp = client.delete("/tasks/")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "No tasks to delete"
