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


def test_list_tasks_by_status_returns_matching_tasks(client):
    """Filtrar por estado devuelve solo las tareas con ese estado."""
    _create_task(client, title="T1", status="pending")
    _create_task(client, title="T2", status="in_progress")
    _create_task(client, title="T3", status="pending")

    resp = client.get("/tasks/status/pending")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert all(t["status"] == "pending" for t in data)

    resp = client.get("/tasks/status/in_progress")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["title"] == "T2"


def test_list_tasks_by_status_empty(client):
    """Si no hay tareas con el estado solicitado devuelve lista vacía."""
    resp = client.get("/tasks/status/done")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_tasks_by_status_invalid_status_returns_422(client):
    """Un valor de estado inválido devuelve 422."""
    resp = client.get("/tasks/status/invalid_status")
    assert resp.status_code == 422


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
