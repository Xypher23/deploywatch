# deploywatch
A simple web app for student developers, freelancers, and small agencies that monitors a website/API URL and records whether it is reachable, how long it took to respond, and when a deployment caused a failure.

## Run locally

```bash
python -m venv .venv
.venv\Scripts\activate          # macOS/Linux: source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload   # then open http://127.0.0.1:8000
pytest
```

Dependencies: FastAPI (web framework), Uvicorn (server), Jinja2 (HTML templates),
python-multipart (form parsing), httpx (HTTP checks), SQLAlchemy (database layer;
SQLite locally, PostgreSQL later via `DATABASE_URL`), pytest (tests).

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
