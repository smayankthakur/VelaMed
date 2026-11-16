"""
VelaMed scan orchestration.

scan(url) runs every registered passive check and returns one result dict.
This JSON is the contract every later layer builds on (scoring, report, API).
"""

from datetime import datetime, timezone
from urllib.parse import urlparse

from . import checks

SCANNER_VERSION = "velamed-passive/0.1 (milestone-1)"


def normalize(url: str) -> str:
    url = url.strip()
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    return url.rstrip("/")


def hostname_of(url: str) -> str:
    return urlparse(url).hostname or ""


def scan(url: str, timeout: int = checks.DEFAULT_TIMEOUT) -> dict:
    url = normalize(url)
    host = hostname_of(url)
    if not host:
        raise ValueError(f"Could not parse a hostname from: {url}")

    return {
        "target": url,
        "host": host,
        "scanned_at": datetime.now(timezone.utc).isoformat(),
        "scanner": SCANNER_VERSION,
        "checks": {
            "https_reachable": checks.check_https(host, timeout),
            "http_redirect": checks.check_http_redirect(host, timeout),
            "certificate": checks.check_certificate(host, timeout),
            "security_headers": checks.check_security_headers(url, timeout),
        },
    }
