from time import perf_counter

import httpx

from . import alerts
from .models import CheckResult, Site

TIMEOUT_SECONDS = 10.0


def check_site(db, site: Site, timeout: float = TIMEOUT_SECONDS) -> CheckResult:
    """Request the site's URL, time it, and save the outcome.

    Up = status 200-399. Down = timeout, connection error, or 400+.
    """
    status_code = None
    error = None
    success = False
    start = perf_counter()
    try:
        response = httpx.get(site.url, timeout=timeout, follow_redirects=False)
        status_code = response.status_code
        success = 200 <= status_code < 400
        if not success:
            error = f"HTTP {status_code}"
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
