# ADR-001: Elección de SQLite como base de datos

## Estado

**Aceptado**

## Fecha

2025-05-27

## Contexto

El proyecto *Gestor de Tareas API* necesita una base de datos relacional para persistir tareas con los campos `id`, `title`, `description`, `status` y `created_at`. Los requisitos principales del proyecto son:

- Es una API REST de alcance reducido, orientada a la gestión del ciclo de vida de tareas individuales.
- El volumen de datos esperado es bajo (cientos o miles de registros, no millones).
- El equipo de desarrollo es pequeño y busca minimizar la complejidad operativa.
- El despliegue debe ser sencillo, sin depender de servicios externos ni de infraestructura adicional.
- Los tests deben ejecutarse de forma rápida y aislada, sin necesidad de levantar un servidor de base de datos.
- Se utiliza **SQLAlchemy 2.0** como ORM, lo que permite cambiar de motor en el futuro si fuera necesario.

## Decisión

Se elige **SQLite** como motor de base de datos, almacenando los datos en el archivo local `tareas.db`.

### Razones

1. **Cero configuración**: SQLite no requiere instalar ni administrar un servidor de base de datos. Basta con la librería `sqlite3` incluida en la stdlib de Python.
2. **Portabilidad**: el archivo `tareas.db` es un único fichero que se puede copiar, respaldar o migrar fácilmente.
3. **Simplicidad de despliegue**: no hay dependencias externas; el proyecto se ejecuta con `pip install -r requirements.txt` y `uvicorn`.
4. **Tests rápidos y aislados**: SQLite admite bases de datos en memoria (`:memory:`) con `StaticPool`, lo que permite ejecutar los tests sin tocar el archivo de producción y sin levantar infraestructura.
5. **Suficiente para el volumen actual**: el modelo de datos es sencillo (una sola tabla `tasks`) y el tráfico esperado es bajo, dentro de los límites de rendimiento de SQLite.
6. **Compatibilidad con SQLAlchemy**: al usar el ORM como capa de abstracción, el acoplamiento con SQLite es mínimo. Una migración futura a otro motor requeriría solo cambiar la URL de conexión y ajustar configuraciones específicas del driver.

## Alternativas consideradas

### PostgreSQL

**Ventajas:**

- Motor robusto y maduro, ampliamente utilizado en producción a gran escala.
- Soporte nativo para tipos avanzados (JSON, arrays, rangos, UUID).
- Excelente rendimiento en lecturas y escrituras concurrentes gracias a MVCC.
- Amplio ecosistema de herramientas de monitorización, respaldo y replicación.
- Soporte completo de transacciones ACID con aislamiento configurable.

**Inconvenientes:**

- Requiere instalar y administrar un servidor de base de datos (o contratar un servicio gestionado).
- Añade complejidad al entorno de desarrollo: cada miembro del equipo necesita un PostgreSQL local o un contenedor Docker.
- Los tests requieren una instancia de PostgreSQL en ejecución (o una imagen Docker), lo que aumenta el tiempo de configuración y ejecución del CI.
- Sobredimensionado para una API con una sola tabla y tráfico bajo.

### MySQL

**Ventajas:**

- Motor muy popular con gran comunidad y abundante documentación.
- Buen rendimiento en operaciones de lectura intensiva.
- Disponible como servicio gestionado en la mayoría de proveedores cloud (AWS RDS, Azure Database, Google Cloud SQL).
- Herramientas maduras de administración (MySQL Workbench, phpMyAdmin).

**Inconvenientes:**

- Requiere instalar y mantener un servidor de base de datos, al igual que PostgreSQL.
- Históricamente menos estricto en el cumplimiento de estándares SQL, lo que puede provocar comportamientos inesperados en validaciones y tipos.
- Menor soporte de tipos avanzados en comparación con PostgreSQL.
- Los tests también necesitan una instancia del servidor en ejecución.
- No aporta ventajas significativas frente a PostgreSQL para este caso de uso, y comparte sus mismos inconvenientes operativos.

## Consecuencias

### Positivas

- **Arranque inmediato**: cualquier desarrollador puede clonar el repositorio y ejecutar la API sin configurar infraestructura de base de datos.
- **CI sencillo**: los tests con SQLite en memoria se ejecutan en milisegundos y no requieren servicios adicionales en el pipeline.
- **Bajo coste operativo**: no hay servidor de base de datos que monitorizar, actualizar o escalar.

### Negativas y riesgos a largo plazo

- **Concurrencia limitada**: SQLite utiliza bloqueos a nivel de archivo. Si en el futuro la API necesita manejar muchas escrituras simultáneas, el rendimiento se degradará.
- **Sin soporte multiusuario real**: SQLite no está diseñado para acceso concurrente desde múltiples procesos o servidores. Un despliegue con varios workers de Uvicorn o múltiples instancias requerirá migrar a un motor cliente-servidor.
- **Funcionalidades SQL reducidas**: SQLite no soporta `ALTER TABLE` completo (por ejemplo, no permite eliminar columnas en versiones antiguas), ni tipos avanzados como arrays o JSON nativos con la misma riqueza que PostgreSQL.
- **Escalabilidad acotada**: si el volumen de datos crece significativamente (millones de registros) o se necesitan consultas analíticas complejas, SQLite dejará de ser adecuado.
- **Migración futura necesaria**: gracias a SQLAlchemy, la migración a PostgreSQL u otro motor es factible cambiando la URL de conexión y el driver. Sin embargo, será necesario:
  - Exportar los datos existentes de `tareas.db`.
  - Ajustar la configuración del argumento `check_same_thread` (específico de SQLite).
  - Verificar que las migraciones de esquema (si se añade Alembic) funcionen con el nuevo motor.
  - Actualizar el entorno de tests para usar el nuevo motor o mantener SQLite en memoria solo para tests.

### Indicadores para reconsiderar esta decisión

- El proyecto necesita despliegue en múltiples instancias o contenedores.
- Se requieren escrituras concurrentes de alto volumen.
- El modelo de datos crece en complejidad (múltiples tablas con relaciones, búsquedas full-text, datos JSON).
- Se necesita replicación o alta disponibilidad de la base de datos.
