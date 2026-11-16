"""
VelaMed DPDP checks — the part that makes this more than a security scan.

Two passive checks, both reading only the public site:

  1. Privacy policy  — is there one, and does it name the three things the
     DPDP Rules expect: the PURPOSE of collection, a GRIEVANCE OFFICER /
     contact, and a RETENTION period?
  2. Form consent    — do forms that collect personal data (name, phone,
     email) carry a consent checkbox or a privacy link, or do they collect
     silently?

The policy reader ships with a zero-cost heuristic analyzer (keyword/section
matching, no AI, works offline). For sharper reading you can plug in an LLM:
pass an `analyzer` callable to analyze_policy(text, analyzer=...). Keep patient
data off free model tiers — a *public privacy policy* is fine to send, patient
data is not.

All findings are framed as "possible gaps to review", never a verdict.
"""

import re
from html.parser import HTMLParser
from urllib.parse import urljoin

from .checks import _request, DEFAULT_TIMEOUT

# ---------------------------------------------------------------------------
# Heuristic policy analysis (pure, offline, zero-cost)
# ---------------------------------------------------------------------------

POLICY_SIGNALS = {
    "purpose": [
        r"purpose[s]? of (collect|process)",
        r"we (collect|use|process)[^.]{0,60}\b(to|for|in order to)\b",
        r"why we collect",
    ],
    "grievance_officer": [
        r"grievance officer",
        r"grievance redress",
        r"data protection officer",
        r"\bDPO\b",
        r"nodal officer",
    ],
    "retention": [
        r"retention",
        r"retain[^.]{0,40}(data|information)",
        r"how long we (keep|store|retain)",
        r"store[^.]{0,40}for[^.]{0,30}(period|year|month|day)",
    ],
    "consent": [
        r"\bconsent\b",
        r"you (agree|consent)",
        r"by (submitting|providing)",
        r"withdraw[^.]{0,30}consent",
    ],
}

POLICY_LABELS = {
    "purpose": "States the purpose of data collection",
    "grievance_officer": "Names a grievance officer / contact",
    "retention": "States a data retention period",
    "consent": "Mentions consent",
}


def analyze_policy_text(text: str) -> dict:
    """Heuristic read of a privacy-policy's text. Pure — no network, no AI."""
    low = (text or "").lower()
    findings = {}
    for key, patterns in POLICY_SIGNALS.items():
        hit = any(re.search(p, low) for p in patterns)
        findings[key] = hit
    present = sum(1 for k in ("purpose", "grievance_officer", "retention") if findings[k])
    return {
        "findings": findings,
        "core_present": present,       # of the 3 DPDP essentials
        "core_total": 3,
        "has_consent_language": findings["consent"],
        "length": len(text or ""),
    }


# ---------------------------------------------------------------------------
# HTML parsing for policy links and form consent (pure, offline)
# ---------------------------------------------------------------------------

class _LinkFormParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []            # (href, text)
        self._cur_href = None
        self._cur_text = []
        self.inputs = []           # (type, name)
        self.has_checkbox = False
        self.has_form = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "a" and a.get("href"):
            self._cur_href = a["href"]
            self._cur_text = []
        elif tag == "form":
            self.has_form = True
        elif tag == "input":
            itype = (a.get("type") or "text").lower()
            name = (a.get("name") or a.get("id") or "").lower()
            self.inputs.append((itype, name))
            if itype == "checkbox":
                self.has_checkbox = True

    def handle_data(self, data):
        if self._cur_href is not None:
            self._cur_text.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self._cur_href is not None:
            self.links.append((self._cur_href, "".join(self._cur_text).strip()))
            self._cur_href = None


PRIVACY_LINK = re.compile(r"privacy|data[-\s]?protection|dpdp", re.I)
PERSONAL_FIELD = re.compile(r"name|phone|mobile|email|tel|contact", re.I)


def find_policy_link(base_url: str, html_text: str):
    """Return the best-guess privacy-policy URL from a homepage, or None."""
    p = _LinkFormParser()
    try:
        p.feed(html_text or "")
    except Exception:
        pass
    for href, text in p.links:
        if PRIVACY_LINK.search(href) or PRIVACY_LINK.search(text):
            return urljoin(base_url, href)
    return None


def analyze_form_html(html_text: str) -> dict:
    """Detect forms collecting personal data and whether consent is offered."""
    p = _LinkFormParser()
    try:
        p.feed(html_text or "")
    except Exception:
        pass

    personal_fields = [n for (t, n) in p.inputs if t in ("text", "tel", "email") and PERSONAL_FIELD.search(n)]
    collects_personal = bool(p.has_form and (personal_fields or any(t == "email" for t, _ in p.inputs)))
    has_privacy_link = any(PRIVACY_LINK.search(h) or PRIVACY_LINK.search(x) for h, x in p.links)
    has_consent_text = bool(re.search(r"\bconsent\b|i agree|i accept", (html_text or ""), re.I))

    consent_offered = collects_personal and (p.has_checkbox or has_privacy_link or has_consent_text)
    return {
        "collects_personal_data": collects_personal,
        "personal_fields": personal_fields[:6],
        "has_checkbox": p.has_checkbox,
        "has_privacy_link": has_privacy_link,
        "has_consent_text": has_consent_text,
        "consent_offered": consent_offered,
    }


# ---------------------------------------------------------------------------
# Orchestration (network — runs on the user's machine)
# ---------------------------------------------------------------------------

def _fetch_text(url: str, timeout: int):
    try:
        import urllib.request
        req = urllib.request.Request(url, headers={"User-Agent": "VelaMed-PassiveScanner/0.1"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read(500_000)  # cap: homepages/policies are small
            charset = resp.headers.get_content_charset() or "utf-8"
            return raw.decode(charset, errors="replace")
    except Exception:
        return None


def check_privacy_policy(url: str, timeout: int = DEFAULT_TIMEOUT, analyzer=None) -> dict:
    """Find and read the privacy policy. analyzer(text)->dict overrides the heuristic."""
    home = _fetch_text(url, timeout)
    if home is None:
        return {"pass": None, "detail": "Could not load the site to look for a policy"}

    policy_url = find_policy_link(url, home)
    if not policy_url:
        return {"pass": False, "detail": "No privacy policy link found on the homepage",
                "policy_url": None, "core_present": 0, "core_total": 3}

    policy_text = _fetch_text(policy_url, timeout)
    if not policy_text:
        return {"pass": False, "detail": f"Privacy policy link found but page did not load: {policy_url}",
                "policy_url": policy_url, "core_present": 0, "core_total": 3}

    analysis = analyzer(policy_text) if analyzer else analyze_policy_text(policy_text)
    core = analysis["core_present"]
    missing = [POLICY_LABELS[k] for k in ("purpose", "grievance_officer", "retention")
               if not analysis["findings"][k]]
    if core == 3:
        detail = "Privacy policy found; names purpose, grievance officer and retention"
    else:
        detail = f"Privacy policy found, but review: missing {', '.join(missing)}"
    return {
        "pass": core == 3,
        "detail": detail,
        "policy_url": policy_url,
        "core_present": core,
        "core_total": 3,
        "findings": analysis["findings"],
    }


def check_form_consent(url: str, timeout: int = DEFAULT_TIMEOUT, use_render: bool = True) -> dict:
    """Do forms collecting personal data offer consent?

    First reads the static HTML (fast). If that finds no personal-data form and
    rendering is available, loads the page in a headless browser (Playwright) to
    catch forms injected by JavaScript. Falls back silently if Playwright is absent.
    """
    home = _fetch_text(url, timeout)
    if home is None:
        return {"pass": None, "detail": "Could not load the site to inspect forms"}

    r = analyze_form_html(home)
    rendered = False

    if not r["collects_personal_data"] and use_render:
        try:
            from .render import render_html
            r2 = analyze_form_html(render_html(url, timeout))
            if r2["collects_personal_data"]:
                r, rendered = r2, True
        except Exception:
            pass  # rendering unavailable → keep the static result

    r["rendered"] = rendered
    tag = " (JS-rendered)" if rendered else ""

    if not r["collects_personal_data"]:
        note = "No personal-data form found on the homepage"
        if not rendered and use_render:
            note += " (static read; a form may load via JavaScript)"
        return {"pass": None, "detail": note,
                "collects_personal_data": False, "consent_offered": None, "rendered": rendered}
    if r["consent_offered"]:
        return {"pass": True,
                "detail": f"Form collects personal data and offers consent / a privacy link{tag}", **r}
    return {"pass": False,
            "detail": f"Form collects personal data (name/phone/email) with no visible consent or privacy link{tag}",
            **r}
