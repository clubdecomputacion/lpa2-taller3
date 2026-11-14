# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project context

University workshop ("Taller 3") skeleton: a REST API for music (usuarios, canciones, favoritos) built with FastAPI + SQLModel + Pydantic. The code is **intentionally incomplete** — most work consists of resolving `# TODO` / `# FIXME` comments. Code, comments, identifiers and commit messages are in Spanish; keep that convention.

The workshop tasks (from README.md) that shape what changes are expected:
- Resolve each `# TODO` / `# FIXME`, **one commit per item**, using Pydantic for data validation.
- Add `pre-commit` hooks and a GitHub Actions workflow running **ruff** (lint + format) and **pytest**.
- Implement the automated tests in `tests/test_api.py`.
- Implement two items from README's "Sugerencias de Mejora" (JWT/OAuth2, pagination, PostgreSQL, Docker, logging, cache, stats, file upload).

## Commands

```bash
python -m venv venv && source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt

uvicorn main:app --reload          # dev server; Swagger at /docs, ReDoc at /redoc

pytest                              # all tests
pytest tests/test_api.py::TestUsuarios::test_crear_usuario   # single test
pytest -k favorito                  # by keyword

ruff check --fix . && ruff format .  # config in pyproject.toml (B008 ignored for FastAPI Depends)
pre-commit install                  # once; hooks: whitespace/EOF, ruff check+format, pytest
pre-commit run --all-files
```

The pre-commit `pytest` hook is `language: system`, so it runs whatever `python` is on PATH — activate the venv before committing. CI (`.github/workflows/ci.yml`) runs two jobs on push to `main` and on PRs: `ruff check` + `ruff format --check`, and `pytest` on Python 3.12.

## Architecture

- `main.py` — FastAPI app: lifespan calls `create_db_and_tables()`, CORS from `settings.cors_origins`, mounts the three routers under `/api/...`, plus `/` and `/health` (checks DB with `SELECT 1`). Endpoint list is in README.md.
- `musica_api/config.py` — `pydantic-settings` reading `.env` (gitignored). `get_settings()` picks Development/Testing (`test_musica.db`)/Production by `ENVIRONMENT`. Default DB `sqlite:///./musica.db`.
- `musica_api/database.py` — module-level `engine` built from settings at import time, `create_db_and_tables()`, and the `get_session` dependency (override this in tests).
- `musica_api/models.py` — per entity: `XBase` (fields), `X` (`table=True`), `XCreate`/`XUpdate` (input), `XRead` (output). **Validators live only on Create/Update** because SQLModel skips validation on table models; they delegate to `utils.py` (`validar_correo`, `validar_año`). `Favorito` has a unique `(id_usuario, id_cancion)` constraint and ORM `cascade_delete` from Usuario/Cancion.
- `musica_api/routers/` — `favoritos.marcar_favorito()` is the shared create-favorite logic (existence checks → 404, duplicate → 400) also used by `usuarios` nested routes. In `canciones`, `/buscar` must stay declared before `/{id}`.
- `musica_api/paginacion.py` — every list endpoint returns `Pagina[XRead]` (`{items, total, offset, limit}`), not a bare array: use `pag: ParametrosPaginacion = Depends(parametros_paginacion)` and `return paginar(session, query.order_by(...), pag)`. Always give the query an `order_by` (stable pages); `total` is counted on the same filtered query.
- Logging: `main.py` calls `configurar_logging(settings.log_level, settings.log_file)` at import. All app loggers are children of `musica_api` (use `logging.getLogger(__name__)` inside the package); it propagates to root so pytest `caplog` works. `middleware.registrar_requests` logs every request and sets `request.state.request_id` / `X-Request-ID` (exposed via CORS). `errores.registrar_manejadores` logs then delegates to FastAPI's default handlers, so the `{"detail": ...}` response shape must stay unchanged (frontend and tests rely on it); unhandled exceptions → generic 500 with `request_id`. Log ids only, never emails/names.
- `tests/` — `conftest.py` holds the `session` (in-memory SQLite + `StaticPool`) and `client` fixtures (overrides `get_session`; no lifespan, so `musica.db` is never touched). Use `TestClient(app, raise_server_exceptions=False)` to test 500 handling. `DevelopmentSettings` logs at DEBUG, so call `caplog.clear()` when asserting exact log lists. `pyproject.toml` sets `pythonpath = ["."]`.
- Field `año` uses a non-ASCII identifier/column name on purpose (matches README); keep it.
- Leftover movie naming from the original template still exists in tests (commented fixture with `director`/`sinopsis`, `cancions` names).
