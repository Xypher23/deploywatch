# deploywatch
A simple web app for student developers, freelancers, and small agencies that monitors a website/API URL and records whether it is reachable, how long it took to respond, and when a deployment caused a failure.

![CI](https://github.com/Xypher23/deploywatch/actions/workflows/ci.yml/badge.svg)

## Run locally (without Docker)

```bash
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload   # then open http://127.0.0.1:8000
pytest
```

## Run with Docker Compose (recommended)

```bash
# Build and start the full stack (app + PostgreSQL)
docker compose up --build -d

# Verify containers are healthy
docker compose ps

# View logs
docker compose logs -f app

# Open the dashboard
open http://localhost:8000/

# Run tests inside the container
docker compose exec app pytest -v

# Stop the stack (add -v to remove database volume)
docker compose down
```

## Run tests locally

```bash
pytest -v
```

## Dependencies

- **FastAPI** (web framework)
- **Uvicorn** (server)
- **Jinja2** (HTML templates)
- **python-multipart** (form parsing)
- **httpx** (HTTP checks)
- **SQLAlchemy** (database layer; SQLite locally, PostgreSQL via `DATABASE_URL`)
- **apscheduler** (background jobs)
- **python-dotenv** (reads `.env`)
- **psycopg2-binary** (PostgreSQL driver)
- **pytest** (tests)

## Monitoring and alerts (week 2)

- A background scheduler (APScheduler) wakes up every minute and checks each site
  whose last check is older than its interval. Run a **single** Uvicorn worker, or
  checks will be duplicated.
- After 3 consecutive failures, one Discord message is sent. The counter resets on
  the next successful check. Copy `.env.example` to `.env` and set
  `DISCORD_WEBHOOK_URL` (never commit `.env`).
- Each site has a history page at `/sites/<id>`.
- New dependencies: `apscheduler` (background jobs), `python-dotenv` (reads `.env`).
- If you upgraded from week 1, delete the old `deploywatch.db` once so the new
  `consecutive_failures` column is created.

## URL safety

Sites are rejected when added, and re-validated before every check, if the host is
`localhost`, a private/loopback/link-local address (including the cloud metadata
address 169.254.169.254), or resolves to one (IPv4 and IPv6). URLs with embedded
credentials are rejected. Redirects are not followed, requests time out after 10 s in
total, and at most ~1 MB of a response is read.

Known limit: the hostname is validated just before the request, and the HTTP client
resolves it again, so a hostile DNS server could still race the two lookups (DNS
rebinding). Before opening the app to strangers, also restrict outbound traffic from the
host at the network level.

## Docker details

The `Dockerfile` uses a multi-stage build:
1. **builder** - installs build dependencies and Python packages
2. **runtime** - copies only the installed packages and app code, runs as non-root user

The `compose.yaml` defines two services:
- **app** - the FastAPI application, depends on PostgreSQL being healthy
- **postgres** - PostgreSQL 16 Alpine with a persistent volume

Environment variables are passed via `.env` file (copy `.env.example` to `.env`).

## GitHub Actions CI

The CI pipeline (`.github/workflows/ci.yml`) runs on every push and PR to `main`:

1. **Test job** - Runs pytest with both SQLite (fast) and PostgreSQL (integration)
2. **Docker job** - Builds the Docker image and verifies it starts
3. **Compose job** - Brings up the full stack and runs tests inside the container

### Protecting main branch

To require CI checks to pass before merging:

1. Go to **Settings** → **Branches** → **Branch protection rules**
2. Click **Add rule**
3. Branch name pattern: `main`
4. Check **Require status checks to pass before merging**
5. Select the CI checks (e.g., `Test on Python 3.11`, `Build Docker image`, `Test Docker Compose stack`)
6. Save changes