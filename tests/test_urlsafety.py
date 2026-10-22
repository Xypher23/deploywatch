import socket
import time

import httpx
import pytest

from app import checker, urlsafety
from app.urlsafety import UnsafeURLError, validate_url

BLOCKED = [
    "http://localhost/", "http://LOCALHOST:8000/", "http://app.localhost/",
    "http://127.0.0.1/", "http://127.1.2.3:9000/", "http://0.0.0.0/",
    "http://10.0.0.5/", "http://172.16.0.1/", "http://192.168.1.1/",
    "http://169.254.169.254/latest/meta-data/", "http://metadata.google.internal/",
    "http://100.64.0.1/", "http://[::1]/", "http://[fd00::1]/", "http://[fe80::1]/",
    "http://[::ffff:127.0.0.1]/", "http://[::ffff:169.254.169.254]/",
    "http://[64:ff9b::a00:1]/",
    "https://user:secret@example.com/",
]


@pytest.mark.parametrize("url", BLOCKED)
def test_blocked_urls(url):
    with pytest.raises(UnsafeURLError):
        validate_url(url)


@pytest.mark.parametrize("url", ["ftp://example.com", "example.com", "http://", "http://[bad"])
def test_malformed_urls(url):
    with pytest.raises(UnsafeURLError):
        validate_url(url)


@pytest.mark.parametrize("url", ["https://example.com", "http://93.184.216.34:8080/x", "http://[2606:2800:220:1::1]/"])
def test_public_urls_allowed(url):
    validate_url(url)


def test_hostname_resolving_to_private_ip_is_blocked(monkeypatch):
    monkeypatch.setattr(urlsafety, "_resolve", lambda h, p: ["10.1.2.3"])
    with pytest.raises(UnsafeURLError):
        validate_url("http://innocent-looking.example")


def test_any_private_answer_blocks(monkeypatch):
    monkeypatch.setattr(urlsafety, "_resolve", lambda h, p: ["93.184.216.34", "127.0.0.1"])
    with pytest.raises(UnsafeURLError):
        validate_url("http://mixed.example")


def test_unresolvable_host_is_allowed(monkeypatch):
    def nxdomain(h, p):
        raise socket.gaierror("nope")

    monkeypatch.setattr(urlsafety, "_resolve", nxdomain)
    validate_url("http://this-domain-does-not-exist.invalid")


def test_blocked_site_is_recorded_down_and_never_requested(db, monkeypatch):
    from app.models import Site

    def explode(*a, **kw):
        raise AssertionError("must not make a request")

    monkeypatch.setattr(checker.httpx, "stream", explode)
    site = Site(url="http://169.254.169.254/", interval_minutes=5)
    db.add(site)
    db.commit()
    result = checker.check_site(db, site)
    assert not result.success and result.error.startswith("Blocked")


def _chunks(counter, size=100_000, delay=0.0):
    while True:
        counter.append(1)
        time.sleep(delay)
        yield b"x" * size


def test_response_body_is_capped(db, site, monkeypatch):
    counter = []

    def stream(method, url, **kw):
        from contextlib import contextmanager

        @contextmanager
        def cm():
            yield httpx.Response(200, content=_chunks(counter), request=httpx.Request(method, url))

        return cm()

    monkeypatch.setattr(checker.httpx, "stream", stream)
    result = checker.check_site(db, site)
    assert result.success
    assert len(counter) * 100_000 <= checker.MAX_BODY_BYTES + 100_000


def test_slow_drip_response_hits_total_deadline(db, site, monkeypatch):
    from contextlib import contextmanager

    @contextmanager
    def stream(method, url, **kw):
        yield httpx.Response(200, content=_chunks([], 10, delay=0.03), request=httpx.Request(method, url))

    monkeypatch.setattr(checker.httpx, "stream", stream)
    result = checker.check_site(db, site, timeout=0.1)
    assert not result.success and result.error == "Timeout"
