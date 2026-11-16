"""Human-readable rendering of a scan result."""

_MARK = {True: "PASS", False: "FAIL", None: "N/A "}


def mark(p) -> str:
    return _MARK[p]


def render(result: dict, scored: dict = None) -> str:
    c = result["checks"]
    lines = ["", f"VelaMed passive scan — {result['target']}"]
    if scored:
        lines.append(f"score {scored['score']}/{scored['max']} — {scored['band']}")
    lines += [f"scanned at {result['scanned_at']}", ""]

    if scored:
        group = None
        for item in scored["items"]:
            if item["group"] != group:
                group = item["group"]
                lines.append(f"  {group}")
            chk = c.get(item["key"], {})
            lines.append(f"    [{mark(chk.get('pass'))}] {item['label']:<22} "
                         f"{item['points']}/{item['max']}  — {item['note']}")
        lines.append("")
        return "\n".join(lines)

    # Fallback without scoring: list whatever checks exist.
    for key, chk in c.items():
        lines.append(f"  [{mark(chk.get('pass'))}] {key} — {chk.get('detail', '')}")
    lines.append("")
    return "\n".join(lines)


def summary_line(result: dict, scored: dict = None) -> str:
    """One compact line per site — used by the batch runner."""
    c = result["checks"]
    prefix = f"{scored['score']:>2}/{scored['max']}  " if scored else ""
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
    if c.get("privacy_policy", {}).get("pass") is not True:
        flags.append("policy")
    if c.get("form_consent", {}).get("pass") is False:
        flags.append("no-consent")
    return f"{prefix}{result['host']:<32}  {', '.join(flags)}"
