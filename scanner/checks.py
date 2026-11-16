"""
VelaMed passive checks.

Each function reads only what a normal visitor's browser already receives and
returns a dict with at least {"pass": True|False|None, "detail": str}.
PASSIVE ONLY — ordinary GET requests, no probing, no login.

Add a new passive check here, then register it in engine.py.
"""

import socket
import ssl
import urllib.error
import urllib.request
from datetime import datetime, timezone

DEFAULT_TIMEOUT = 10  # seconds
USER_AGENT = "VelaMed-PassiveScanner/0.1 (+compliance check; contact sitelytc.com)"

# Security headers we check for, with a short note on what each does.
SECURITY_HEADERS = {
    "strict-transport-security": "Forces HTTPS (HSTS)",
    "content-security-policy": "Limits what the page can load (CSP)",
    "x-frame-options": "Blocks clickjacking via framing",
    "x-content-type-options": "Stops MIME-type sniffing",
    "referrer-policy": "Controls referrer leakage",
    "permissions-policy": "Restricts browser features",
}

CERT_WARN_DAYS = 30
CERT_CRITICAL_DAYS = 7


def _request(url: str, timeout: int, method: str = "GET"):
    """One request, following no redirects. Returns (status, headers_dict, final_url)."""

    class _NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, req, fp, code, msg, headers, newurl):
            return None  # we want to SEE the redirect, not follow it

    opener = urllib.request.build_opener(_NoRedirect)
    req = urllib.request.Request(url, method=method, headers={"User-Agent": USER_AGENT})
    try:
        resp = opener.open(req, timeout=timeout)
        return resp.status, dict(resp.headers), resp.geturl()
    except urllib.error.HTTPError as e:
        return e.code, dict(e.headers), url


def check_https(host: str, timeout: int = DEFAULT_TIMEOUT) -> dict:
    """Can we open a TLS connection on 443 at all?"""
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((host, 443), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=host):
                return {"pass": True, "detail": "HTTPS reachable on port 443"}
    except Exception as e:
        return {"pass": False, "detail": f"HTTPS not reachable: {e.__class__.__name__}: {e}"}


def check_http_redirect(host: str, timeout: int = DEFAULT_TIMEOUT) -> dict:
    """Does plain http:// redirect to https://?"""
    try:
        status, headers, _ = _request(f"http://{host}", timeout)
    except Exception as e:
        return {"pass": None, "detail": f"Could not reach HTTP: {e.__class__.__name__}"}

    location = headers.get("Location", "") or headers.get("location", "")
    if status in (301, 302, 303, 307, 308) and location.startswith("https://"):
        return {"pass": True, "detail": f"HTTP {status} -> {location}"}
    if status in (301, 302, 303, 307, 308):
        return {"pass": False, "detail": f"Redirects, but not to HTTPS: {location or '(no Location)'}"}
    return {"pass": False, "detail": f"No HTTPS redirect (HTTP returned {status})"}


def check_certificate(host: str, timeout: int = DEFAULT_TIMEOUT) -> dict:
    """Fetch the TLS certificate and report validity + days to expiry."""
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((host, 443), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()
    except ssl.SSLCertVerificationError as e:
        return {"pass": False, "detail": f"Certificate did not verify: {getattr(e, 'verify_message', e)}"}
    except Exception as e:
        return {"pass": None, "detail": f"Could not read certificate: {e.__class__.__name__}: {e}"}

    not_after = cert.get("notAfter")
    issuer = dict(x[0] for x in cert.get("issuer", []))
    try:
        expiry = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return {"pass": None, "detail": f"Could not parse expiry: {not_after}"}

    days_left = (expiry - datetime.now(timezone.utc)).days
    result = {
        "issuer": issuer.get("organizationName", "unknown"),
        "expires": expiry.date().isoformat(),
        "days_left": days_left,
    }
    if days_left < 0:
        result.update({"pass": False, "detail": f"Certificate EXPIRED {abs(days_left)} days ago"})
    elif days_left <= CERT_CRITICAL_DAYS:
        result.update({"pass": False, "detail": f"Certificate expires in {days_left} days — critical"})
    elif days_left <= CERT_WARN_DAYS:
        result.update({"pass": True, "detail": f"Valid, but expires in {days_left} days — renew soon"})
    else:
        result.update({"pass": True, "detail": f"Valid, {days_left} days left"})
    return result


def check_security_headers(url: str, timeout: int = DEFAULT_TIMEOUT) -> dict:
    """Look at the response headers a visitor receives over HTTPS."""
    try:
        _, headers, _ = _request(url, timeout)
    except Exception as e:
        return {"pass": None, "detail": f"Could not fetch headers: {e.__class__.__name__}", "missing": []}

    lowered = {k.lower(): v for k, v in headers.items()}
    found, missing = {}, []
    for header, note in SECURITY_HEADERS.items():
        if header in lowered:
            found[header] = lowered[header]
        else:
            missing.append({"header": header, "note": note})

    return {
        "pass": len(found) == len(SECURITY_HEADERS),
        "detail": f"{len(found)}/{len(SECURITY_HEADERS)} security headers present",
        "present": found,
        "missing": missing,
    }
