import logging
from datetime import datetime, timedelta, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy import select

from .checker import check_site
from .database import SessionLocal
from .models import CheckResult, Site

logger = logging.getLogger("deploywatch.scheduler")

TICK_SECONDS = 60
# Checks happen a little before the interval ends so a 1-minute tick never skips a cycle.
TOLERANCE = timedelta(seconds=30)


def _now():
    return datetime.now(timezone.utc).replace(tzinfo=None)  # DB stores naive UTC


def run_due_checks(db) -> int:
    """Check every site whose last check is older than its interval."""
    now = _now()
    checked = 0
    for site in db.scalars(select(Site)).all():
        last = db.scalars(
            select(CheckResult.checked_at)
            .where(CheckResult.site_id == site.id)
            .order_by(CheckResult.id.desc())
            .limit(1)
        ).first()
        if last is None or now - last >= timedelta(minutes=site.interval_minutes) - TOLERANCE:
            check_site(db, site)
            checked += 1
    if checked:
        logger.info("Scheduled run checked %d site(s)", checked)
    return checked


def _job():
    db = SessionLocal()
    try:
        run_due_checks(db)
    except Exception:
        logger.exception("Scheduled run failed")
    finally:
        db.close()


def start_scheduler() -> BackgroundScheduler:
    scheduler = BackgroundScheduler()
    scheduler.add_job(
        _job,
        "interval",
        seconds=TICK_SECONDS,
        id="due_checks",
        max_instances=1,  # never overlap runs
        coalesce=True,
        next_run_time=datetime.now(),
    )
    scheduler.start()
    return scheduler
