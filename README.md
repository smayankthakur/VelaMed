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
│   ├── dpdp.py        DPDP checks: privacy policy + form consent
│   ├── render.py      optional Playwright rendering for JS-loaded forms
│   ├── scoring.py     0–40 rubric (Security 24 / DPDP 16)
│   ├── report.py      console / batch rendering
│   ├── report_html.py one-page print-ready HTML report
│   └── report_pdf.py  one-page PDF report (reportlab)
├── apps/
│   ├── api/           FastAPI wrapper over the scanner (M4; live on Render)
│   └── web/           Next.js front end (M5)
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

## What it checks

**Security (24 points)**
- HTTPS reachable on port 443
- HTTP redirects to HTTPS
- TLS certificate validity + days to expiry (warn < 30 days, fail < 7)
- Security headers: HSTS, CSP, X-Frame-Options, X-Content-Type-Options,
  Referrer-Policy, Permissions-Policy

**DPDP (16 points)**
- Privacy policy: present, and names the purpose of collection, a grievance
  officer, and a retention period
- Form consent: forms collecting personal data (name/phone/email) offer a
  consent checkbox or privacy link, rather than collecting silently

The privacy-policy reader uses a zero-cost heuristic by default (keyword/section
matching, offline). To use an LLM instead, pass an `analyzer(text)->dict`
callable to `dpdp.check_privacy_policy`. A *public privacy policy* is fine to
send to a model; **patient data is not** — keep it off free tiers.

## Roadmap

- **M1** passive engine — done
- **M2** scoring (0–40) + one-page HTML/PDF report — done
- **M3** DPDP checks: privacy-policy reader + form consent — done
- **M3b** JS-rendered form consent via Playwright — done (optional; static fallback)
- **M4** FastAPI wrapper — done (see `apps/api/`; live on Render)
- **M5** Next.js front end — done (see `apps/web/`)
- **M6** deploy the front end (Vercel) + lead-capture storage
- Paid tier (ownership gate + scanner worker + billing) — separate sprint

## Live

- API: https://velamed-api.onrender.com (`/docs` for the interactive API)
- Front end: `apps/web` — run locally or deploy to Vercel (M6)

## API

A thin HTTP layer lives in `apps/api/` — `POST /scan` returns the score and
checks, with `/scan/{id}/report.html` and `.pdf` for the one-pager. See
`apps/api/README.md`.

## Add a check

Write it in `scanner/checks.py` returning `{"pass": ..., "detail": ...}`,
then register it in `scanner/engine.py`. Everything downstream (scoring,
report, API) reads the same JSON.
