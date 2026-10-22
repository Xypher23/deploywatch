import logging
import os
from datetime import datetime, timezone

import httpx

logger = logging.getLogger("deploywatch.alerts")

ALERT_THRESHOLD = 3


def send_discord_alert(site, result) -> bool:
    """Post a 'site is down' message to Discord. Never raises."""
    webhook_url = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook_url:
        logger.warning("DISCORD_WEBHOOK_URL not set; skipping alert for %s", site.url)
        return False

    when = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    content = (
        f"\U0001F534 **{site.url}** is DOWN: {ALERT_THRESHOLD} checks failed in a row.\n"
        f"Last error: {result.error}\nTime: {when}"
    )
    try:
        response = httpx.post(webhook_url, json={"content": content}, timeout=10.0)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        # Log only the exception type: its message can contain the secret webhook URL.
        logger.error("Discord alert failed for %s: %s", site.url, type(exc).__name__)
        return False
    logger.info("Discord alert sent for %s", site.url)
    return True
