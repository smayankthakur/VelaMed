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
│   ├── scoring.py     0–40 rubric → score, band, breakdown
│   ├── report.py      console / batch rendering
│   ├── report_html.py one-page print-ready HTML report
│   └── report_pdf.py  one-page PDF report (reportlab)
├── apps/              (later) api/ FastAPI · web/ Next.js
└── reports/           (generated; git-ignored)
```

## Run it

The scanner and HTML report need only the Python 3.9+ standard library.
The PDF report needs reportlab (`pip install -r requirements.txt`).

```bash
python3 scan.py yourhospital.com                 # report + 0–40 score
python3 scan.py yourhospital.com --json          # raw JSON (the API contract)
python3 scan.py yourhospital.com --report pdf    # one-page PDF -> reports/
python3 scan.py yourhospital.com --report both   # HTML + PDF
python3 scan.py --batch sites.txt                # one scored line per site
python3 scan.py --batch sites.txt --report html  # a report per site
```

Reports land in `reports/` (git-ignored). Without reportlab, `--report pdf`
falls back to HTML, which prints to PDF from any browser.

> Run it on a normal machine, not behind a TLS-intercepting proxy, or the
> certificate and header readings will reflect the proxy, not the site.

## What it checks (Milestone 1)

- HTTPS reachable on port 443
- HTTP redirects to HTTPS
- TLS certificate validity + days to expiry (warn < 30 days, fail < 7)
- Security headers: HSTS, CSP, X-Frame-Options, X-Content-Type-Options,
  Referrer-Policy, Permissions-Policy

## Roadmap

- **M1** passive engine — done
- **M2** scoring (0–40) + one-page HTML/PDF report — done
- **M3** AI privacy-policy reader (purpose, grievance officer, retention, itemised consent)
- **M3b** form consent detection (Playwright)
- **M4** FastAPI wrapper → **M5** Next.js front end → **M6** deploy free tier
- Paid tier (ownership gate + scanner worker + billing) — separate sprint

## Add a check

Write it in `scanner/checks.py` returning `{"pass": ..., "detail": ...}`,
then register it in `scanner/engine.py`. Everything downstream (scoring,
report, API) reads the same JSON.
