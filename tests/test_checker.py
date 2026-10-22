import httpx
from fastapi.testclient import TestClient

from app import checker
from app.database import get_db
from app.main import app


def fake_get(status):
    return lambda url, **kw: httpx.Response(status, request=httpx.Request("GET", url))


def test_success(db, site, monkeypatch):
    monkeypatch.setattr(checker.httpx, "get", fake_get(200))
    result = checker.check_site(db, site)
    assert result.success and result.status_code == 200 and result.error is None


def test_redirect_counts_as_up(db, site, monkeypatch):
    monkeypatch.setattr(checker.httpx, "get", fake_get(301))
    assert checker.check_site(db, site).success


def test_http_error_is_down(db, site, monkeypatch):
    monkeypatch.setattr(checker.httpx, "get", fake_get(500))
    result = checker.check_site(db, site)
    assert not result.success and result.status_code == 500


def test_timeout_is_down(db, site, monkeypatch):
    def boom(url, **kw):
        raise httpx.ReadTimeout("slow")

    monkeypatch.setattr(checker.httpx, "get", boom)
    result = checker.check_site(db, site)
    assert not result.success and result.status_code is None and result.error == "Timeout"


def test_connection_error_is_down(db, site, monkeypatch):
    def boom(url, **kw):
        raise httpx.ConnectError("no route")

    monkeypatch.setattr(checker.httpx, "get", boom)
    result = checker.check_site(db, site)
    assert not result.success and "ConnectError" in result.error


def test_add_site_and_check_now(db, monkeypatch):
    monkeypatch.setattr(checker.httpx, "get", fake_get(200))
    app.dependency_overrides[get_db] = lambda: db
    client = TestClient(app)
    try:
        assert client.post("/sites", data={"url": "ftp://x", "interval_minutes": 5}).status_code == 400
        r = client.post("/sites", data={"url": "https://example.com", "interval_minutes": 5}, follow_redirects=False)
        assert r.status_code == 303
        client.post("/sites/1/check")
        page = client.get("/")
        assert "https://example.com" in page.text and "Up" in page.text
        assert "200" in client.get("/sites/1").text
        assert client.get("/sites/99").status_code == 404
    finally:
        app.dependency_overrides.clear()
