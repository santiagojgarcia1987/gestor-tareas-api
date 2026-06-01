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


def test_update_task_short_title_returns_422(client):
    """Actualizar una tarea con título de menos de 3 caracteres devuelve 422."""
    task = _create_task(client)
    resp = client.patch(f"/tasks/{task['id']}", json={"title": "AB"})
    assert resp.status_code == 422
    assert resp.json()["detail"] == "Title must be at least 3 characters long"


def test_update_task_empty_title_returns_422(client):
    """Actualizar una tarea con título vacío devuelve 422."""
    task = _create_task(client)
    resp = client.patch(f"/tasks/{task['id']}", json={"title": ""})
    assert resp.status_code == 422
    assert resp.json()["detail"] == "Title must be at least 3 characters long"


def test_update_task_title_exactly_3_chars_succeeds(client):
    """Actualizar una tarea con título de exactamente 3 caracteres es válido."""
    task = _create_task(client)
    resp = client.patch(f"/tasks/{task['id']}", json={"title": "ABC"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "ABC"


# ── Tests del campo prioridad ──────────────────────────────────────────


def test_create_task_default_priority_is_medium(client):
    """Crear una tarea sin indicar prioridad debe asignar 'medium'."""
    task = _create_task(client)
    assert task["priority"] == "medium"


def test_create_task_with_explicit_priority(client):
    """Crear una tarea con prioridad explícita debe respetar el valor enviado."""
    for priority in ("low", "medium", "high"):
        task = _create_task(client, priority=priority)
        assert task["priority"] == priority


def test_create_task_with_invalid_priority_returns_422(client):
    """Crear una tarea con un valor de prioridad no válido devuelve 422."""
    resp = client.post("/tasks/", json={"title": "Tarea inválida", "priority": "urgent"})
    assert resp.status_code == 422


def test_update_task_priority(client):
    """Actualizar la prioridad de una tarea pendiente debe funcionar."""
    task = _create_task(client)
    resp = client.patch(f"/tasks/{task['id']}", json={"priority": "high"})
    assert resp.status_code == 200
    assert resp.json()["priority"] == "high"


def test_update_task_invalid_priority_returns_422(client):
    """Actualizar la prioridad con un valor no válido devuelve 422."""
    task = _create_task(client)
    resp = client.patch(f"/tasks/{task['id']}", json={"priority": "critical"})
    assert resp.status_code == 422


def test_get_task_includes_priority(client):
    """Obtener una tarea por id debe incluir el campo prioridad."""
    task = _create_task(client, priority="low")
    resp = client.get(f"/tasks/{task['id']}")
    assert resp.status_code == 200
    assert resp.json()["priority"] == "low"


def test_list_tasks_includes_priority(client):
    """Listar tareas debe incluir el campo prioridad en cada elemento."""
    _create_task(client, priority="high")
    _create_task(client, priority="low")
    resp = client.get("/tasks/")
    assert resp.status_code == 200
    priorities = [t["priority"] for t in resp.json()]
    assert "high" in priorities
    assert "low" in priorities


# ── Tests del campo categoría ──────────────────────────────────────────


def test_create_task_default_category_is_other(client):
    """Crear una tarea sin indicar categoría debe asignar 'other'."""
    task = _create_task(client)
    assert task["category"] == "other"


def test_create_task_with_explicit_category(client):
    """Crear una tarea con categoría explícita debe respetar el valor enviado."""
    for category in ("work", "personal", "shopping", "other"):
        task = _create_task(client, category=category)
        assert task["category"] == category


def test_create_task_with_invalid_category_returns_422(client):
    """Crear una tarea con un valor de categoría no válido devuelve 422."""
    resp = client.post("/tasks/", json={"title": "Tarea inválida", "category": "urgent"})
    assert resp.status_code == 422


def test_update_task_category(client):
    """Actualizar la categoría de una tarea pendiente debe funcionar."""
    task = _create_task(client)
    resp = client.patch(f"/tasks/{task['id']}", json={"category": "work"})
    assert resp.status_code == 200
    assert resp.json()["category"] == "work"


def test_update_task_invalid_category_returns_422(client):
    """Actualizar la categoría con un valor no válido devuelve 422."""
    task = _create_task(client)
    resp = client.patch(f"/tasks/{task['id']}", json={"category": "fitness"})
    assert resp.status_code == 422


def test_get_task_includes_category(client):
    """Obtener una tarea por id debe incluir el campo categoría."""
    task = _create_task(client, category="personal")
    resp = client.get(f"/tasks/{task['id']}")
    assert resp.status_code == 200
    assert resp.json()["category"] == "personal"


def test_list_tasks_includes_category(client):
    """Listar tareas debe incluir el campo categoría en cada elemento."""
    _create_task(client, category="work")
    _create_task(client, category="shopping")
    resp = client.get("/tasks/")
    assert resp.status_code == 200
    categories = [t["category"] for t in resp.json()]
    assert "work" in categories
    assert "shopping" in categories
