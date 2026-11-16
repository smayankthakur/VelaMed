#!/usr/bin/env python3
"""
VelaMed — passive public-surface scanner (CLI entry point).

PASSIVE ONLY. Ordinary GET requests, like a browser. No scanning, no probing,
no login. Active testing (VAPT) belongs in a separate, permission-gated tool.

  python3 scan.py example.com                      # one site, readable report + score
  python3 scan.py example.com --json               # one site, raw JSON (score included)
  python3 scan.py example.com --report pdf          # write a one-page PDF
  python3 scan.py example.com --report both --out reports
  python3 scan.py --batch sites.txt                 # many sites, scored, one line each
  python3 scan.py --batch sites.txt --report html   # a report per site
"""

import argparse
import json
import os
import sys

from scanner import scan, score_scan
from scanner.report import render, summary_line
from scanner import report_html, report_pdf


def _read_sites(path: str) -> list:
    with open(path, encoding="utf-8") as f:
        return [ln.strip() for ln in f if ln.strip() and not ln.strip().startswith("#")]


def _write_reports(result, scored, kinds, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    base = os.path.join(out_dir, result["host"].replace(":", "_"))
    written = []
    if kinds in ("html", "both"):
        written.append(report_html.write_html(result, scored, base + ".html"))
    if kinds in ("pdf", "both"):
        try:
            written.append(report_pdf.write_pdf(result, scored, base + ".pdf"))
        except report_pdf.ReportlabMissing as e:
            # Fall back to HTML so the user still gets a deliverable.
            print(f"note: {e}", file=sys.stderr)
            if kinds == "pdf":
                written.append(report_html.write_html(result, scored, base + ".html"))
    return written


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="VelaMed passive public-surface scanner")
    p.add_argument("url", nargs="?", help="Site to scan, e.g. example.com")
    p.add_argument("--batch", metavar="FILE", help="Scan every URL listed in FILE (one per line)")
    p.add_argument("--json", action="store_true", help="Output raw JSON (score included)")
    p.add_argument("--report", choices=["html", "pdf", "both"], help="Write a one-page report per site")
    p.add_argument("--out", default="reports", help="Directory for reports (default: reports)")
    p.add_argument("--timeout", type=int, default=10, help="Per-check timeout in seconds")
    args = p.parse_args(argv)

    if not args.url and not args.batch:
        p.error("give a URL or --batch FILE")

    targets = _read_sites(args.batch) if args.batch else [args.url]
    rows = []  # (result, scored)
    for t in targets:
        try:
            result = scan(t, timeout=args.timeout)
        except ValueError as e:
            print(f"skip {t}: {e}", file=sys.stderr)
            continue
        rows.append((result, score_scan(result)))

    # Reports
    all_written = []
    if args.report:
        for result, scored in rows:
            all_written += _write_reports(result, scored, args.report, args.out)

    # Console / JSON output
    if args.json:
        payload = [{**r, "scoring": s} for r, s in rows]
        print(json.dumps(payload if args.batch else payload[0], indent=2))
    elif args.batch:
        print()
        for result, scored in rows:
            print("  " + summary_line(result, scored))
        print(f"\n  {len(rows)} site(s) scanned.")
    else:
        result, scored = rows[0]
        print(render(result, scored))

    if all_written:
        print("  reports written:")
        for w in all_written:
            print(f"    {w}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
