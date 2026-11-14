# API de Música

## Estudiante

- **Nombre:** Derik Jair Hurtado Sinisterra
- **GitHub:** [DerikHurt](https://github.com/DerikHurt)

Una [API RESTful](https://aws.amazon.com/es/what-is/restful-api/) para gestionar usuarios, canciones y favoritos. Desarrollada con [FastAPI](https://fastapi.tiangolo.com/), [SQLModel](https://sqlmodel.tiangolo.com/) y [Pydantic](https://docs.pydantic.dev/).

## Descripción

Esta API permite administrar:
- **Usuarios**: crear y gestionar perfiles de usuarios.
- **Canciones**: agregar, actualizar y eliminar canciones con sus metadatos.
- **Favoritos**: gestionar las canciones favoritas de cada usuario.

El proyecto incluye una interfaz de documentación interactiva generada automáticamente con [Swagger](https://swagger.io/) disponible en el *endpoint* `/docs`.

## Estructura del Proyecto

```
lpa2-taller3
├──  README.md            # Este archivo, documentación completa del proyecto
├──  .env                 # Variables de entorno (desarrollo, pruebas, producción)
├──  .env.example         # Plantilla de variables de entorno (copiar como .env)
├──  .gitignore           # Archivos y directorios a ignorar por Git
├──  main.py              # Script principal para ejecutar la aplicación
├──  musica.db            # Base de Datos
├──  musica_api
│   ├──  __init__.py      # Inicialización del módulo
│   └──  *                # Implementación del API
├── 󰌠 requirements.txt     # Dependencias del proyecto
├── 󰙨 tests
│   └──  test_api.py      # Pruebas Unitarias
└──  utils.py             # Funciones de utilidad

```
## Modelo de Datos

1. **Usuario**:
   - id: Identificador único
   - nombre: Nombre del usuario
   - correo: Correo electrónico (único)
   - fecha_registro: Fecha de registro

2. **Canción**:
   - id: Identificador único
   - titulo: Título de la canción
   - artista: Artista o intérprete
   - album: Álbum al que pertenece
   - duracion: Duración en segundos
   - año: Año de lanzamiento
   - genero: Género musical
   - fecha_creacion: Fecha de creación del registro

3. **Favorito**:
   - id: Identificador único
   - id_usuario: ID del usuario (clave foránea)
   - id_cancion: ID de la canción (clave foránea)
   - fecha_marcado: Fecha en que se marcó como favorito

## Requisitos

- [Python 3.12](https://www.python.org/downloads/) (es la versión con la que se prueba en el CI)
- [Git](https://git-scm.com/downloads)
- Opcional: [DBeaver](https://dbeaver.io/) para ver o editar `musica.db`

## Instalación

1. Clona este repositorio:

   ```bash
   git clone https://github.com/DerikHurt/lpa2-taller3.git
   cd lpa2-taller3
   ```

2. Crea y activa un entorno virtual:

   ```bash
   python -m venv venv

   # Windows (PowerShell)
   venv\Scripts\activate

   # Linux / macOS / Git Bash
   source venv/bin/activate
   ```

   En PowerShell, si aparece un error de "ejecución de scripts deshabilitada", ejecuta una vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`.

3. Instala las dependencias (API, pruebas, ruff y pre-commit):

   ```bash
   pip install -r requirements.txt
   ```

4. (Opcional) Configura las variables de entorno. Sin `.env` la API funciona con los valores por defecto; para cambiarlos:

   ```bash
   cp .env.example .env
   ```

   y descomenta en `.env` lo que necesites (`DATABASE_URL`, `CORS_ORIGINS`, `LOG_LEVEL`, `LOG_FILE`, `ENVIRONMENT`).

## Ejecución

1. Con el entorno virtual activado, ejecuta la aplicación:

   ```bash
   uvicorn main:app --reload --no-access-log
   ```

   `--no-access-log` evita que uvicorn repita cada petición, porque la API ya las registra con su propio formato. Al arrancar se crean las tablas si no existen; `musica.db` ya incluye 5 usuarios y 10 canciones de ejemplo.

2. Accede a la aplicación:
   - API: [http://127.0.0.1:8000/](http://127.0.0.1:8000/)
   - Documentación *Swagger UI*: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
   - Documentación *ReDoc*: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
   - Estado de la API: [http://127.0.0.1:8000/health](http://127.0.0.1:8000/health)

3. Para detenerla, pulsa `Ctrl + C` en la terminal.

## Pruebas y calidad de código

Con el entorno virtual activado:

```bash
python -m pytest                 # todas las pruebas
python -m pytest -k favorito     # solo las que contienen "favorito" en el nombre
ruff check --fix .               # linter
ruff format .                    # formatter
```

Para que ruff y pytest se ejecuten antes de cada commit, instala los hooks una vez:

```bash
pre-commit install
pre-commit run --all-files       # revisar todo el repositorio
```

El hook de pytest usa el `python` activo, así que haz los commits con el entorno virtual activado. GitHub Actions ejecuta ruff y pytest en cada push a `main` y en cada pull request.

## Uso de la API

### Usuarios

- **Listar usuarios**: `GET /api/usuarios`
- **Crear usuario**: `POST /api/usuarios`
- **Obtener usuario**: `GET /api/usuarios/{id}`
- **Actualizar usuario**: `PUT /api/usuarios/{id}`
- **Eliminar usuario**: `DELETE /api/usuarios/{id}`

### Canciones

- **Listar canciones**: `GET /api/canciones`
- **Crear canción**: `POST /api/canciones`
- **Obtener canción**: `GET /api/canciones/{id}`
- **Actualizar canción**: `PUT /api/canciones/{id}`
- **Eliminar canción**: `DELETE /api/canciones/{id}`
- **Buscar canciones**: `GET /api/canciones/buscar?titulo=value&artista=value&genero=value`

### Favoritos

- **Listar favoritos**: `GET /api/favoritos`
- **Marcar favorito**: `POST /api/favoritos`
- **Obtener favorito**: `GET /api/favoritos/{id}`
- **Eliminar favorito**: `DELETE /api/favoritos/{id}`
- **Listar favoritos de usuario**: `GET /api/usuarios/{id}/favoritos`
- **Marcar favorito específico**: `POST /api/usuarios/{id_usuario}/favoritos/{id_cancion}`
- **Eliminar favorito específico**: `DELETE /api/usuarios/{id_usuario}/favoritos/{id_cancion}`

## Desarrollo del Taller

1. Ajustar este `README.md` con los datos del Estudiante

2. Utilizando [DBeaver](https://dbeaver.io/), adiciona 5 usuarios y 10 canciones, directo a las tablas.

3. Adicionar `pre-commit` y `workflow` de GitHub Actions para **ruff** *linter* y *formatter*, y para **pytest**.

4. Busca todos los comentarios `# TODO` y `# FIXME`, realiza los ajustes necesarios, y ejecuta un `commit` por cada uno. Usa Pydantic para la validación de datos.

5. Prueba el funcionamiento del API, desde la documentación *Swagger UI* o *ReDoc*.

6. Desarrolla las pruebas automatizadas para verificar el funcionamiento correcto de la API.

7. Implementar dos (2) de las sugerencias que se presentan a continuación.

## Sugerencias de Mejora

1. **Autenticación y autorización**: Implementar JWT o OAuth2 para proteger los endpoints y asociar los usuarios automáticamente con sus favoritos.

2. **Paginación**: Añadir soporte para paginación en las listas de canciones, usuarios y favoritos para mejorar el rendimiento con grandes volúmenes de datos.

3. **Base de datos en producción**: Migrar a una base de datos más robusta como PostgreSQL o MySQL para entornos de producción.

4. **Docker**: Contenerizar la aplicación para facilitar su despliegue en diferentes entornos.

5. **Registro (logging)**: Implementar un sistema de registro más completo para monitorear errores y uso de la API.

6. **Caché**: Añadir caché para mejorar la velocidad de respuesta en consultas frecuentes.

7. **Estadísticas de uso**: Implementar un sistema de seguimiento para analizar qué canciones son más populares y sugerir recomendaciones basadas en preferencias similares.

8. **Subida de archivos**: Permitir la subida de archivos de audio y gestionar su almacenamiento en un servicio como S3 o similar.

## Mejoras Implementadas

### Registro (logging)

- Todos los logs usan el formato `fecha | nivel | logger | mensaje` y cuelgan del logger `musica_api` (`musica_api/logging_config.py`).
- **Middleware de requests** (`musica_api/middleware.py`): registra método, ruta, código de estado y duración de cada petición. Los errores 4xx/5xx se registran como `WARNING`/`ERROR`.
- **Id de seguimiento**: cada respuesta incluye la cabecera `X-Request-ID` (o reutiliza la que envíe el cliente), y ese id aparece en el log. Así un error visto en el frontend se puede encontrar en los logs.
- **Manejadores de errores** (`musica_api/errores.py`): registran los 404, 400 y errores de validación sin cambiar el formato `{"detail": ...}`. Una excepción no controlada se registra con su traceback y el cliente recibe un 500 genérico con el `request_id`, sin detalles internos.
- Los routers registran las altas, cambios y bajas usando solo ids, sin correos ni nombres.
- Configurable por variables de entorno en `.env`:

  ```bash
  LOG_LEVEL=INFO              # DEBUG, INFO, WARNING, ERROR, CRITICAL
  LOG_FILE=logs/musica_api.log  # opcional: archivo rotativo (1 MB x 5)
  ```

  En desarrollo el nivel por defecto es `DEBUG`; en producción se escribe además en `logs/musica_api.log`.
- Para evitar líneas duplicadas con el log de acceso de uvicorn: `uvicorn main:app --reload --no-access-log`

### Paginación

- Todos los listados (`/api/usuarios`, `/api/canciones`, `/api/canciones/buscar`, `/api/favoritos` y `/api/usuarios/{id}/favoritos`) aceptan `offset` (por defecto `0`) y `limit` (por defecto `20`, máximo `100`).
- La respuesta incluye el total de resultados, para que el frontend calcule el número de páginas (`ceil(total / limit)`):

  ```json
  GET /api/canciones/buscar?genero=rock&offset=20&limit=10

  {
    "items": [ { "id": 21, "titulo": "...", ... } ],
    "total": 57,
    "offset": 20,
    "limit": 10
  }
  ```

- En búsquedas, `total` cuenta solo los resultados filtrados.
- Los resultados se ordenan por `id`, de modo que las páginas no repiten ni saltan elementos. Los favoritos de un usuario se devuelven del más reciente al más antiguo.
- Implementación reutilizable en `musica_api/paginacion.py` (`Pagina[T]`, dependencia `parametros_paginacion` y función `paginar`).
