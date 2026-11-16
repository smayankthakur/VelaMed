"""
VelaMed scoring — turn a raw scan into a 0–40 score with a band and a
plain-language breakdown.

Framing rule: these are *gaps to review*, never a verdict of "non-compliant".
The rubric is transparent so a hospital can see exactly why it scored what it did.

Two halves, so the score reflects DPDP exposure, not just security hygiene —
a site can have perfect HTTPS and still collect patient data with no notice.

Security (24):
    HTTPS reachable        6
    HTTP -> HTTPS redirect  6
    TLS certificate         6   valid >30d: 6 · valid <=30d: 4 · invalid: 0
    Security headers        6   1 point per header present (6 headers)

DPDP (16):
    Privacy policy         10   present: 4 · +2 each for purpose / grievance / retention
    Form consent            6   personal-data form offers consent / privacy link
"""

WEIGHTS = {
    "https_reachable": 6,
    "http_redirect": 6,
    "certificate": 6,
    "security_headers": 6,
    "privacy_policy": 10,
    "form_consent": 6,
}
MAX_SCORE = sum(WEIGHTS.values())  # 40  (Security 24 + DPDP 16)

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
        return 4
    return 6


def _score_headers(sh: dict) -> int:
    present = len(sh.get("present", {}))
    return min(present, WEIGHTS["security_headers"])  # 1 point each, 6 headers


def _score_privacy_policy(pp: dict) -> int:
    # No policy, or couldn't find one → 0. Present → 4, plus 2 per DPDP essential.
    if pp.get("pass") is None and pp.get("policy_url") is None:
        return 0
    if not pp.get("policy_url"):
        return 0
    return 4 + 2 * pp.get("core_present", 0)  # max 4 + 6 = 10


def _score_form_consent(fc: dict) -> int:
    # pass True → 6; pass False → 0; None (no personal-data form) → neutral full marks.
    if fc.get("pass") is True:
        return 6
    if fc.get("pass") is None:
        return WEIGHTS["form_consent"]  # nothing collected on the page we saw
    return 0


SCORERS = {
    "https_reachable": lambda c: WEIGHTS["https_reachable"] if c["pass"] else 0,
    "http_redirect": lambda c: WEIGHTS["http_redirect"] if c["pass"] else 0,
    "certificate": _score_certificate,
    "security_headers": _score_headers,
    "privacy_policy": _score_privacy_policy,
    "form_consent": _score_form_consent,
}

LABELS = {
    "https_reachable": "HTTPS reachable",
    "http_redirect": "HTTP redirects to HTTPS",
    "certificate": "TLS certificate valid",
    "security_headers": "Security headers",
    "privacy_policy": "Privacy policy",
    "form_consent": "Consent on forms",
}

GROUPS = {
    "https_reachable": "Security",
    "http_redirect": "Security",
    "certificate": "Security",
    "security_headers": "Security",
    "privacy_policy": "DPDP",
    "form_consent": "DPDP",
}


def score_scan(result: dict) -> dict:
    """Return {score, max, band, colour, items:[{key,group,label,points,max,note}]}."""
    c = result["checks"]
    items = []
    for key in WEIGHTS:
        chk = c.get(key, {"detail": "not checked"})
        points = SCORERS[key](chk) if key in c else 0
        items.append({
            "key": key,
            "group": GROUPS[key],
            "label": LABELS[key],
            "points": points,
            "max": WEIGHTS[key],
            "note": chk.get("detail", ""),
        })

    score = sum(i["points"] for i in items)
    label, colour = _band(score)
    return {
        "score": score,
        "max": MAX_SCORE,
        "band": label,
        "colour": colour,
        "items": items,
    }
