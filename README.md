# Gestor de Tareas API

API REST para gestionar el ciclo de vida de tareas, construida con **FastAPI** y **SQLAlchemy**. Permite crear, consultar, actualizar y eliminar tareas. Cada tarea cuenta con un identificador único, título, descripción opcional, estado (`pending`, `in_progress`, `done`), prioridad (`low`, `medium`, `high`; por defecto `medium`), categoría (`work`, `personal`, `shopping`, `other`; por defecto `other`) y fecha de creación automática.

## Stack tecnológico

| Capa | Tecnología |
|---|---|
| Framework web | FastAPI 0.136 |
| ORM | SQLAlchemy 2.0 |
| Validación | Pydantic 2 |
| Base de datos | SQLite |
| Servidor | Uvicorn |
| Tests | pytest + httpx |
| Lenguaje | Python 3.12+ |

## Estructura del proyecto

```
gestor-tareas-api/
├── aplicacion/
│   ├── __init__.py
│   ├── principal.py          # Punto de entrada: instancia FastAPI y registro de routers
│   ├── base_de_datos.py      # Configuración del engine y sesión de SQLAlchemy
│   ├── modelos.py            # Modelos ORM (tabla tasks, enum TaskStatus)
│   ├── esquemas.py           # Esquemas Pydantic de entrada y respuesta
│   └── rutas/
│       ├── __init__.py
│       └── tareas.py         # Endpoints REST de tareas
├── tests/
│   ├── __init__.py
│   └── test_tasks.py         # Tests con pytest y SQLite en memoria
├── AGENTS.md                 # Instrucciones y convenciones del proyecto
├── requirements.txt          # Dependencias de producción y desarrollo
└── README.md
```

## Requisitos previos

- **Python 3.12** o superior
- **pip** (incluido con Python)

## Instalación y puesta en marcha

1. Clonar el repositorio:

   ```bash
   git clone https://github.com/santiagojgarcia1987/gestor-tareas-api.git
   cd gestor-tareas-api
   ```

2. Crear y activar el entorno virtual:

   ```bash
   python -m venv venv

   # macOS / Linux
   source venv/bin/activate

   # Windows
   venv\Scripts\activate
   ```

3. Instalar dependencias:

   ```bash
   pip install -r requirements.txt
   ```

4. Arrancar el servidor de desarrollo:

   ```bash
   uvicorn aplicacion.principal:app --reload
   ```

La API quedará disponible en `http://127.0.0.1:8000`.
La documentación interactiva (Swagger UI) estará en `http://127.0.0.1:8000/docs`.

## Endpoints disponibles

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/tasks/` | Lista todas las tareas |
| `GET` | `/tasks/{id}` | Obtiene una tarea por su identificador |
| `POST` | `/tasks/` | Crea una nueva tarea |
| `PATCH` | `/tasks/{id}` | Actualiza parcialmente una tarea |
| `DELETE` | `/tasks/{id}` | Elimina una tarea |

### Ejemplo rápido

Crear una tarea:

```bash
curl -X POST http://127.0.0.1:8000/tasks/ \
  -H "Content-Type: application/json" \
  -d '{"title": "Mi primera tarea", "priority": "high", "category": "work"}'
```

Si no se indica `priority`, la tarea se crea con prioridad `medium`.
Si no se indica `category`, la tarea se crea con categoría `other`.

## Ejecución de tests

```bash
pytest tests/ -v
```

Los tests utilizan una base de datos SQLite en memoria con `StaticPool`, lo que garantiza aislamiento total entre casos de prueba. No se toca el archivo `tareas.db` de producción.

## Convenciones del proyecto

### Idioma

- El **código** (variables, funciones, clases, rutas de URL) se escribe en **inglés**.
- Los **comentarios** y la **documentación** se escriben en **castellano**.
- Los nombres de **archivos y carpetas** del proyecto están en **castellano** (`modelos.py`, `esquemas.py`, `rutas/`).

### Estilo

- Se sigue **PEP 8** con un máximo de **100 caracteres** por línea.
- Importaciones agrupadas: stdlib → third-party → proyecto, separadas por una línea en blanco.

Para más detalle sobre las convenciones, consultar el fichero [`AGENTS.md`](AGENTS.md).

## Licencia

*Pendiente de definir.*
