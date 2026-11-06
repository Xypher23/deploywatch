# Tech Stack

## Language and runtime

- **Language:** Python.
- **Runtime declared by the project:** Python 3.11 in the Dockerfile and GitHub Actions workflow.
- **Observed local virtual environment:** Python 3.14.6, recorded in `.venv/pyvenv.cfg`; this is environment metadata and does not change the project’s declared CI/container runtime.
- The source uses Python 3.10+ syntax such as union types (`T | None`); the configured project runtime is Python 3.11.
- **Web runtime:** Uvicorn ASGI server, launched as one process in the documented Docker command. The README notes that the scheduler expects a single Uvicorn worker to avoid duplicate checks.

## Frameworks and libraries

Versions are not pinned in `requirements.txt` or `requirements-dev.txt`; the versions below are therefore not specified by the project manifests.

| Dependency | Role |
|---|---|
| FastAPI | HTTP application and route declarations |
| Uvicorn `[standard]` | ASGI server |
| Jinja2 | Server-rendered HTML templates |
| python-multipart | HTML form parsing used by FastAPI form fields |
| SQLAlchemy | ORM, engine, session, and table metadata |
| APScheduler | In-process periodic background scheduler |
| httpx | Outbound website checks and Discord webhook calls |
| python-dotenv | Loads `.env` values |
| psycopg | PostgreSQL driver |
| pytest (development requirements) | Test runner |

Python standard-library modules used include `logging`, `datetime`, `contextlib`, `pathlib`, `os`, `socket`, `ipaddress`, `time`, and `urllib.parse`.

## Frontend

- Jinja2 HTML templates with CSS and plain JavaScript; there is no frontend build system or JavaScript package manifest.
- Tailwind CSS is loaded from `https://cdn.tailwindcss.com` in the templates.
- `app/static/theme.js` stores the theme selection in browser `localStorage` and applies system/dark/light mode.

## Persistence

- SQLAlchemy declarative models.
- SQLite by default (`sqlite:///./deploywatch.db`); PostgreSQL through `DATABASE_URL`.
- PostgreSQL support is configured through `psycopg`, with PostgreSQL 16 Alpine in Compose and CI.
- The lifespan uses `Base.metadata.create_all`; no migration framework is configured in the inspected project files.

## Configuration and build files

- `requirements.txt`: runtime Python dependencies; versions are unpinned.
- `requirements-dev.txt`: includes runtime requirements and pytest.
- `.env.example`: documents `DATABASE_URL` and `DISCORD_WEBHOOK_URL`.
- `Dockerfile`: multi-stage image based on `python:3.11-slim`; installs dependencies and runs Uvicorn as a non-root user.
- `compose.yaml`: app and PostgreSQL services, database health check, and named persistent volume.
- `.github/workflows/ci.yml`: Python 3.11 test job, PostgreSQL service, Docker build/start check, and Compose stack check.

## Existing runtime constraints

- APScheduler is in-process; the README documents a single Uvicorn worker/replica to prevent duplicate scheduled checks.
- Dependencies are unpinned in the manifests, so exact installed dependency versions are not part of the repository’s declared stack.
