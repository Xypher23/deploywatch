import logging
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlparse

from fastapi import Depends, FastAPI, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.orm import Session

from .checker import check_site
from .database import Base, engine, get_db
from .models import CheckResult, Site
from .scheduler import start_scheduler

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")

BASE_DIR = Path(__file__).parent
templates = Jinja2Templates(directory=BASE_DIR / "templates")


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    scheduler = start_scheduler()
    yield
    scheduler.shutdown(wait=False)


app = FastAPI(title="DeployWatch", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


@app.get("/health")
def health():
    return {"status": "ok"}


def _latest_result(db: Session, site_id: int):
    stmt = (
        select(CheckResult)
        .where(CheckResult.site_id == site_id)
        .order_by(CheckResult.id.desc())
        .limit(1)
    )
    return db.scalars(stmt).first()


def _render_dashboard(request: Request, db: Session, error=None, status_code=200):
    sites = db.scalars(select(Site).order_by(Site.id)).all()
    rows = [(site, _latest_result(db, site.id)) for site in sites]
    return templates.TemplateResponse(
        request, "index.html", {"rows": rows, "error": error}, status_code=status_code
    )


@app.get("/")
def dashboard(request: Request, db: Session = Depends(get_db)):
    return _render_dashboard(request, db)


@app.post("/sites")
def add_site(
    request: Request,
    url: str = Form(...),
    interval_minutes: int = Form(5),
    db: Session = Depends(get_db),
):
    url = url.strip()
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        return _render_dashboard(
            request, db, "Enter a full http:// or https:// URL.", status_code=400
        )
    if not 1 <= interval_minutes <= 1440:
        return _render_dashboard(
            request, db, "Interval must be between 1 and 1440 minutes.", status_code=400
        )
    db.add(Site(url=url, interval_minutes=interval_minutes))
    db.commit()
    return RedirectResponse("/", status_code=303)


@app.post("/sites/{site_id}/check")
def check_now(site_id: int, db: Session = Depends(get_db)):
    site = db.get(Site, site_id)
    if site is None:
        raise HTTPException(status_code=404, detail="Site not found")
    check_site(db, site)
    return RedirectResponse("/", status_code=303)


@app.get("/sites/{site_id}")
def site_history(site_id: int, request: Request, db: Session = Depends(get_db)):
    site = db.get(Site, site_id)
    if site is None:
        raise HTTPException(status_code=404, detail="Site not found")
    stmt = (
        select(CheckResult)
        .where(CheckResult.site_id == site_id)
        .order_by(CheckResult.id.desc())
        .limit(50)
    )
    results = db.scalars(stmt).all()
    return templates.TemplateResponse(
        request, "history.html", {"site": site, "results": results}
    )
