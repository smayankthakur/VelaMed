"""
VelaMed scan orchestration.

scan(url) runs every registered passive check and returns one result dict.
This JSON is the contract every later layer builds on (scoring, report, API).
"""

import re
from datetime import datetime, timezone
from urllib.parse import urlparse

from . import checks, dpdp

# A hostname: dot-separated labels, no spaces. Good enough to reject junk input.
_HOST_RE = re.compile(r"^(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.(?!-)[A-Za-z0-9-]{1,63}(?<!-))+$")

SCANNER_VERSION = "velamed-passive/0.2 (milestone-3)"


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
    if not host or not _HOST_RE.match(host):
        raise ValueError(f"Not a valid hostname: {url}")

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
            "privacy_policy": dpdp.check_privacy_policy(url, timeout),
            "form_consent": dpdp.check_form_consent(url, timeout),
        },
    }
