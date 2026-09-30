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
