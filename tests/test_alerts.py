from datetime import datetime, timedelta, timezone

import httpx
import pytest

from app import alerts, checker, scheduler
from app.models import CheckResult
from helpers import fake_stream


def fail(*a, **kw):
    raise httpx.ConnectError("no route")


ok = fake_stream(200)


@pytest.fixture
def sent(monkeypatch):
    calls = []
    monkeypatch.setattr(alerts, "send_discord_alert", lambda s, r: calls.append(r.id) or True)
    return calls


def test_alert_only_on_third_consecutive_failure(db, site, sent, monkeypatch):
    monkeypatch.setattr(checker.httpx, "stream", fail)
    for _ in range(2):
        checker.check_site(db, site)
    assert sent == [] and site.consecutive_failures == 2
    checker.check_site(db, site)
    assert len(sent) == 1 and site.consecutive_failures == 3
    for _ in range(3):
        checker.check_site(db, site)
    assert len(sent) == 1  # no spam on failures 4, 5, 6


def test_success_resets_counter_and_allows_new_alert(db, site, sent, monkeypatch):
    monkeypatch.setattr(checker.httpx, "stream", fail)
    for _ in range(3):
        checker.check_site(db, site)
    monkeypatch.setattr(checker.httpx, "stream", ok)
    checker.check_site(db, site)
    assert site.consecutive_failures == 0
    monkeypatch.setattr(checker.httpx, "stream", fail)
    for _ in range(3):
        checker.check_site(db, site)
    assert len(sent) == 2


def test_discord_message_is_posted(site, monkeypatch):
    posted = {}
    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.test/hook")
    monkeypatch.setattr(
        alerts.httpx, "post",
        lambda url, **kw: posted.update(url=url, **kw) or httpx.Response(204, request=httpx.Request("POST", url)),
    )
    result = CheckResult(site_id=1, success=False, error="Timeout")
    assert alerts.send_discord_alert(site, result)
    assert "example.com" in posted["json"]["content"] and "Timeout" in posted["json"]["content"]


def test_missing_webhook_is_skipped(site, monkeypatch):
    monkeypatch.delenv("DISCORD_WEBHOOK_URL", raising=False)
    assert alerts.send_discord_alert(site, CheckResult(error="x")) is False


def test_discord_outage_does_not_raise(site, monkeypatch):
    def boom(*a, **kw):
        raise httpx.ConnectError("down")

    monkeypatch.setenv("DISCORD_WEBHOOK_URL", "https://discord.test/hook")
    monkeypatch.setattr(alerts.httpx, "post", boom)
    assert alerts.send_discord_alert(site, CheckResult(error="x")) is False


def test_scheduler_checks_only_due_sites(db, site, monkeypatch):
    monkeypatch.setattr(checker.httpx, "stream", ok)
    assert scheduler.run_due_checks(db) == 1   # never checked -> due
    assert scheduler.run_due_checks(db) == 0   # just checked -> not due
    old = datetime.now(timezone.utc).replace(tzinfo=None) - timedelta(minutes=10)
    db.query(CheckResult).update({"checked_at": old})
    db.commit()
    assert scheduler.run_due_checks(db) == 1   # last check is stale -> due
