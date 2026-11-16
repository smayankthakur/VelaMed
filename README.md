# VelaMed

A passive DPDP + security surface check for hospital and clinic websites.
Reads only what a normal visitor's browser already receives — **no scanning,
no probing, no login.** Active testing (VAPT) is a separate, permission-gated
tool, built later.

## Project layout

```
velamed/
├── scan.py            CLI entry point (single site or --batch)
├── sites.txt          target list for batch scanning
├── requirements.txt   (stdlib only for now)
├── scanner/           the passive engine (the product's core)
│   ├── checks.py      individual passive checks
│   ├── engine.py      scan() — runs the checks, returns JSON
│   └── report.py      human-readable rendering
├── apps/              (later) api/ FastAPI · web/ Next.js
└── reports/           (generated; git-ignored)
```

## Run it

No dependencies — Python 3.9+ standard library only.

```bash
python3 scan.py yourhospital.com            # readable report
python3 scan.py yourhospital.com --json     # raw JSON (the API contract)
python3 scan.py --batch sites.txt           # one line per site
python3 scan.py --batch sites.txt --json    # JSON array
```

> Run it on a normal machine, not behind a TLS-intercepting proxy, or the
> certificate and header readings will reflect the proxy, not the site.

## What it checks (Milestone 1)

- HTTPS reachable on port 443
- HTTP redirects to HTTPS
- TLS certificate validity + days to expiry (warn < 30 days, fail < 7)
- Security headers: HSTS, CSP, X-Frame-Options, X-Content-Type-Options,
  Referrer-Policy, Permissions-Policy

## Roadmap

- **M2** scoring (0–40) + one-page PDF report
- **M3** AI privacy-policy reader (purpose, grievance officer, retention, itemised consent)
- **M3b** form consent detection (Playwright)
- **M4** FastAPI wrapper → **M5** Next.js front end → **M6** deploy free tier
- Paid tier (ownership gate + scanner worker + billing) — separate sprint

## Add a check

Write it in `scanner/checks.py` returning `{"pass": ..., "detail": ...}`,
then register it in `scanner/engine.py`. Everything downstream (scoring,
report, API) reads the same JSON.
