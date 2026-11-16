"""
VelaMed API (Milestone 4) — a thin FastAPI wrapper over the scanner.

    POST /scan                 {"url": "example.com"}  -> run a scan, return score + checks
    GET  /scan/{id}            retrieve a stored scan
    GET  /scan/{id}/report.html  the one-page HTML report
    GET  /scan/{id}/report.pdf   the one-page PDF report (if reportlab is installed)
    GET  /health

Still PASSIVE ONLY — this exposes the passive scanner over HTTP, nothing more.
Scans are kept in an in-memory store for now; swap for a database in M5/M6.

Run it:
    cd apps/api
    uvicorn main:app --reload --port 8000
"""

import os
import sys
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, Response
from pydantic import BaseModel

# Make the repo-root `scanner` package importable when run from apps/api.
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from scanner import scan, score_scan              # noqa: E402
from scanner.report_html import build_html         # noqa: E402
from scanner import report_pdf                     # noqa: E402

app = FastAPI(title="VelaMed API", version="0.1")

# Allow the Next.js front end (M5) to call this during development.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],          # tighten to your domains before production
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory store: id -> {"result": ..., "scoring": ...}. Replace with a DB later.
STORE: dict = {}


class ScanRequest(BaseModel):
    url: str
    timeout: int = 10


@app.get("/health")
def health():
    return {"status": "ok", "service": "velamed-api", "version": "0.1"}


@app.post("/scan")
def run_scan(req: ScanRequest):
    try:
        result = scan(req.url, timeout=req.timeout)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    scoring = score_scan(result)
    scan_id = uuid.uuid4().hex[:12]
    STORE[scan_id] = {"result": result, "scoring": scoring}
    return {
        "id": scan_id,
        "host": result["host"],
        "score": scoring["score"],
        "max": scoring["max"],
        "band": scoring["band"],
        "scoring": scoring,
        "checks": result["checks"],
    }


def _get(scan_id: str):
    item = STORE.get(scan_id)
    if not item:
        raise HTTPException(status_code=404, detail="scan not found")
    return item


@app.get("/scan/{scan_id}")
def get_scan(scan_id: str):
    item = _get(scan_id)
    return {"id": scan_id, **item}


@app.get("/scan/{scan_id}/report.html", response_class=HTMLResponse)
def report_html(scan_id: str):
    item = _get(scan_id)
    return build_html(item["result"], item["scoring"])


@app.get("/scan/{scan_id}/report.pdf")
def report_pdf_endpoint(scan_id: str):
    item = _get(scan_id)
    tmp = f"/tmp/velamed-{scan_id}.pdf"
    try:
        report_pdf.write_pdf(item["result"], item["scoring"], tmp)
    except report_pdf.ReportlabMissing as e:
        raise HTTPException(status_code=501, detail=str(e))
    with open(tmp, "rb") as f:
        data = f.read()
    os.remove(tmp)
    return Response(
        content=data,
        media_type="application/pdf",
        headers={"Content-Disposition": f'inline; filename="velamed-{item["result"]["host"]}.pdf"'},
    )
