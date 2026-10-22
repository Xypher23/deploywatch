from time import perf_counter

import httpx

from . import alerts
from .models import CheckResult, Site
from .urlsafety import UnsafeURLError, validate_url

TIMEOUT_SECONDS = 10.0
MAX_BODY_BYTES = 1_000_000  # stop reading after ~1 MB


def _fetch_status(url: str, timeout: float) -> int:
    """GET the URL, reading at most MAX_BODY_BYTES and at most `timeout` seconds in total."""
    start = perf_counter()
    with httpx.stream("GET", url, timeout=timeout, follow_redirects=False) as response:
        read = 0
        for chunk in response.iter_bytes():
            if perf_counter() - start > timeout:
                raise httpx.ReadTimeout("total time limit exceeded")
            read += len(chunk)
            if read >= MAX_BODY_BYTES:
                break
        return response.status_code


def check_site(db, site: Site, timeout: float = TIMEOUT_SECONDS) -> CheckResult:
    """Request the site's URL, time it, and save the outcome.

    Up = status 200-399. Down = timeout, connection error, or 400+.
    """
    status_code = None
    error = None
    success = False
    start = perf_counter()
    try:
        validate_url(site.url)  # re-checked on every request, not just when added
        status_code = _fetch_status(site.url, timeout)
        success = 200 <= status_code < 400
        if not success:
            error = f"HTTP {status_code}"
    except UnsafeURLError as exc:
        error = f"Blocked: {exc}"
    except httpx.TimeoutException:
        error = "Timeout"
    except httpx.HTTPError as exc:
        error = f"{type(exc).__name__}: {exc}"[:500]
    elapsed_ms = round((perf_counter() - start) * 1000)

    result = CheckResult(
        site_id=site.id,
        status_code=status_code,
        response_time_ms=elapsed_ms,
        success=success,
        error=error,
    )
    site.consecutive_failures = 0 if success else site.consecutive_failures + 1
    db.add(result)
    db.commit()
    if not success and site.consecutive_failures == alerts.ALERT_THRESHOLD:
        alerts.send_discord_alert(site, result)
    return result
