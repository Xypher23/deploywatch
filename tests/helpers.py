from contextlib import contextmanager

import httpx


def fake_stream(status=200, body=b""):
    """Stand-in for httpx.stream that returns a canned response."""

    @contextmanager
    def _stream(method, url, **kw):
        yield httpx.Response(status, content=body, request=httpx.Request(method, url))

    return _stream
