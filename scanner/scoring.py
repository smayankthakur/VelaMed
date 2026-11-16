"""
VelaMed scoring — turn a raw scan into a 0–40 score with a band and a
plain-language breakdown.

Framing rule: these are *gaps to review*, never a verdict of "non-compliant".
The rubric is intentionally simple and transparent so a hospital can see
exactly why it scored what it did.

Rubric (max 40):
    HTTPS reachable        8   pass / fail
    HTTP -> HTTPS redirect  8   pass / fail
    TLS certificate        12   valid >30d: 12 · valid <=30d: 8 · expired/invalid: 0
    Security headers       12   2 points per header present (6 headers)
"""

WEIGHTS = {
    "https_reachable": 8,
    "http_redirect": 8,
    "certificate": 12,
    "security_headers": 12,
}
MAX_SCORE = sum(WEIGHTS.values())  # 40

BANDS = [
    (32, "Good", "#1a7f37"),
    (20, "Needs attention", "#bf8700"),
    (0, "At risk", "#c0392b"),
]


def _band(score: int):
    for threshold, label, colour in BANDS:
        if score >= threshold:
            return label, colour
    return BANDS[-1][1], BANDS[-1][2]


def _score_certificate(cert: dict) -> int:
    if cert.get("pass") is not True:
        return 0
    days = cert.get("days_left")
    if isinstance(days, int) and days <= 30:
        return 8
    return 12


def _score_headers(sh: dict) -> int:
    present = len(sh.get("present", {}))
    return min(present * 2, WEIGHTS["security_headers"])


def score_scan(result: dict) -> dict:
    """Return {score, max, band, colour, items:[{key,label,points,max,note}]}."""
    c = result["checks"]
    items = []

    def add(key, label, points):
        items.append({
            "key": key,
            "label": label,
            "points": points,
            "max": WEIGHTS[key],
            "note": c[key]["detail"],
        })

    add("https_reachable", "HTTPS reachable", WEIGHTS["https_reachable"] if c["https_reachable"]["pass"] else 0)
    add("http_redirect", "HTTP redirects to HTTPS", WEIGHTS["http_redirect"] if c["http_redirect"]["pass"] else 0)
    add("certificate", "TLS certificate valid", _score_certificate(c["certificate"]))
    add("security_headers", "Security headers", _score_headers(c["security_headers"]))

    score = sum(i["points"] for i in items)
    label, colour = _band(score)
    return {
        "score": score,
        "max": MAX_SCORE,
        "band": label,
        "colour": colour,
        "items": items,
    }
