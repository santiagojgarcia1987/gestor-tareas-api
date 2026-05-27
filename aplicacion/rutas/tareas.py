# Definición de los endpoints REST para la gestión de tareas

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from aplicacion.base_de_datos import get_db
from aplicacion.esquemas import TaskCreate, TaskResponse, TaskUpdate
from aplicacion.modelos import Task, TaskStatus

# Router con prefijo /tasks; agrupa todos los endpoints de tareas
router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("/", response_model=List[TaskResponse])
def list_tasks(db: Session = Depends(get_db)):
    """Obtiene la lista completa de tareas almacenadas.

    Args:
        db (Session): Sesión de base de datos inyectada por
            FastAPI mediante la dependencia ``get_db``.

    Returns:
        List[TaskResponse]: Lista con todas las tareas existentes
            en la base de datos.
    """
    return db.query(Task).all()


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)):
    """Obtiene una tarea por su identificador único.

    Args:
        task_id (int): Identificador numérico de la tarea.
        db (Session): Sesión de base de datos inyectada por
            FastAPI mediante la dependencia ``get_db``.

    Returns:
        TaskResponse: Representación de la tarea solicitada.

    Raises:
        HTTPException: Error 404 si no existe una tarea con el
            identificador proporcionado.
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    """Crea una nueva tarea en la base de datos.

    Args:
        payload (TaskCreate): Esquema con los datos de la tarea a
            crear. Solo el título es obligatorio.
        db (Session): Sesión de base de datos inyectada por
            FastAPI mediante la dependencia ``get_db``.

    Returns:
        TaskResponse: Representación de la tarea recién creada,
            incluyendo el identificador y la fecha de creación
            asignados por la base de datos.
    """
    task = Task(**payload.model_dump())
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.patch("/{task_id}", response_model=TaskResponse)
def update_task(task_id: int, payload: TaskUpdate, db: Session = Depends(get_db)):
    """Actualiza parcialmente una tarea existente.

    Solo se modifican los campos incluidos en el cuerpo de la
    petición. No se permite actualizar tareas en estado ``done``.

    Args:
        task_id (int): Identificador numérico de la tarea a
            actualizar.
        payload (TaskUpdate): Esquema con los campos a modificar.
            Los campos no incluidos se mantienen sin cambios.
        db (Session): Sesión de base de datos inyectada por
            FastAPI mediante la dependencia ``get_db``.

    Returns:
        TaskResponse: Representación actualizada de la tarea.

    Raises:
        HTTPException: Error 404 si no existe una tarea con el
            identificador proporcionado.
        HTTPException: Error 400 si la tarea tiene estado
            ``done`` y no puede ser modificada.
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if task.status == TaskStatus.done:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update a completed task",
        )
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


@router.delete("/", status_code=status.HTTP_204_NO_CONTENT)
def delete_all_tasks(db: Session = Depends(get_db)):
    """Elimina todas las tareas de la base de datos.

    Si no existen tareas, devuelve un error 404.

    Args:
        db (Session): Sesión de base de datos inyectada por
            FastAPI mediante la dependencia ``get_db``.

    Returns:
        None: Respuesta vacía con código de estado HTTP 204.

    Raises:
        HTTPException: Error 404 si no existen tareas para
            eliminar.
    """
    count = db.query(Task).count()
    if count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No tasks to delete",
        )
    db.query(Task).delete()
    db.commit()


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(task_id: int, db: Session = Depends(get_db)):
    """Elimina una tarea de la base de datos.

    Args:
        task_id (int): Identificador numérico de la tarea a
            eliminar.
        db (Session): Sesión de base de datos inyectada por
            FastAPI mediante la dependencia ``get_db``.

    Returns:
        None: Respuesta vacía con código de estado HTTP 204.

    Raises:
        HTTPException: Error 404 si no existe una tarea con el
            identificador proporcionado.
    """
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    db.delete(task)
    db.commit()
