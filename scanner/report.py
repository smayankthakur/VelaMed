"""Human-readable rendering of a scan result."""

_MARK = {True: "PASS", False: "FAIL", None: "N/A "}


def mark(p) -> str:
    return _MARK[p]


def render(result: dict) -> str:
    c = result["checks"]
    lines = [
        "",
        f"VelaMed passive scan — {result['target']}",
        f"scanned at {result['scanned_at']}",
        "",
    ]

    h = c["https_reachable"]
    lines.append(f"  [{mark(h['pass'])}] HTTPS reachable   — {h['detail']}")

    r = c["http_redirect"]
    lines.append(f"  [{mark(r['pass'])}] HTTP -> HTTPS     — {r['detail']}")

    cert = c["certificate"]
    lines.append(f"  [{mark(cert['pass'])}] TLS certificate   — {cert['detail']}")
    if "issuer" in cert:
        lines.append(f"         issuer: {cert['issuer']}, expires {cert.get('expires')}")

    sh = c["security_headers"]
    lines.append(f"  [{mark(sh['pass'])}] Security headers  — {sh['detail']}")
    for m in sh.get("missing", []):
        lines.append(f"         missing: {m['header']} ({m['note']})")

    lines.append("")
    return "\n".join(lines)


def summary_line(result: dict) -> str:
    """One compact line per site — used by the batch runner."""
    c = result["checks"]
    flags = []
    if c["https_reachable"]["pass"] is not True:
        flags.append("no-https")
    if c["http_redirect"]["pass"] is not True:
        flags.append("no-redirect")
    if c["certificate"]["pass"] is not True:
        flags.append("cert")
    sh = c["security_headers"]
    present = len(sh.get("present", {}))
    total = present + len(sh.get("missing", []))
    flags.append(f"headers {present}/{total}")
    return f"{result['host']:<32}  {', '.join(flags)}"
