#!/usr/bin/env python3
"""
VelaMed — passive public-surface scanner (CLI entry point).

PASSIVE ONLY. Ordinary GET requests, like a browser. No scanning, no probing,
no login. Active testing (VAPT) belongs in a separate, permission-gated tool.

  python3 scan.py example.com                 # one site, readable report
  python3 scan.py example.com --json          # one site, raw JSON
  python3 scan.py --batch sites.txt           # many sites, one line each
  python3 scan.py --batch sites.txt --json    # many sites, JSON array
"""

import argparse
import json
import sys

from scanner import scan
from scanner.report import render, summary_line


def _read_sites(path: str) -> list:
    with open(path, encoding="utf-8") as f:
        return [ln.strip() for ln in f if ln.strip() and not ln.strip().startswith("#")]


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="VelaMed passive public-surface scanner")
    p.add_argument("url", nargs="?", help="Site to scan, e.g. example.com")
    p.add_argument("--batch", metavar="FILE", help="Scan every URL listed in FILE (one per line)")
    p.add_argument("--json", action="store_true", help="Output raw JSON")
    p.add_argument("--timeout", type=int, default=10, help="Per-check timeout in seconds")
    args = p.parse_args(argv)

    if not args.url and not args.batch:
        p.error("give a URL or --batch FILE")

    targets = _read_sites(args.batch) if args.batch else [args.url]
    results = []
    for t in targets:
        try:
            results.append(scan(t, timeout=args.timeout))
        except ValueError as e:
            print(f"skip {t}: {e}", file=sys.stderr)

    if args.json:
        print(json.dumps(results if args.batch else results[0], indent=2))
    elif args.batch:
        print()
        for r in results:
            print("  " + summary_line(r))
        print(f"\n  {len(results)} site(s) scanned.\n")
    else:
        print(render(results[0]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
