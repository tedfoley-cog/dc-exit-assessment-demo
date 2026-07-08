#!/usr/bin/env python3
"""Aggregate per-app readiness readouts into a portfolio disposition table.

Reads YAML front-matter from every file in assessment/readouts/, prints a
console table, and writes a self-contained HTML portfolio report to
assessment/portfolio_report.html.

Stdlib only; run with: python3 scripts/aggregate_readouts.py
"""

import html
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
READOUTS = ROOT / "assessment" / "readouts"
REPORT = ROOT / "assessment" / "portfolio_report.html"

FIELDS = [
    "app_id", "app_name", "stack", "disposition",
    "blockers", "majors", "backlog_items",
]

DISPOSITION_COLORS = {
    "rehost": "#16a34a",
    "replatform": "#0ea5e9",
    "refactor": "#d97706",
    "retire": "#64748b",
    "replace": "#9333ea",
}


def parse_front_matter(path):
    lines = path.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    meta = {}
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    return meta


def load_readouts():
    if not READOUTS.is_dir():
        return []
    readouts = []
    for path in sorted(READOUTS.glob("*.md")):
        meta = parse_front_matter(path)
        if meta is None:
            print(f"warning: {path.name} has no front-matter, skipping", file=sys.stderr)
            continue
        meta["_file"] = path.name
        readouts.append(meta)
    return readouts


def print_table(readouts):
    headers = ["App", "Stack", "Disposition", "Blockers", "Majors", "Backlog"]
    rows = [
        [
            r.get("app_name", r.get("app_id", "?")),
            r.get("stack", "?"),
            r.get("disposition", "?").upper(),
            r.get("blockers", "?"),
            r.get("majors", "?"),
            r.get("backlog_items", "?"),
        ]
        for r in readouts
    ]
    widths = [max(len(h), *(len(row[i]) for row in rows)) for i, h in enumerate(headers)]
    sep = "+".join("-" * (w + 2) for w in widths)
    print(sep)
    print(" | ".join(h.ljust(w) for h, w in zip(headers, widths)))
    print(sep)
    for row in rows:
        print(" | ".join(cell.ljust(w) for cell, w in zip(row, widths)))
    print(sep)


def write_html(readouts):
    rows_html = []
    for r in readouts:
        disposition = r.get("disposition", "unknown").lower()
        color = DISPOSITION_COLORS.get(disposition, "#334155")
        rows_html.append(
            "<tr>"
            f"<td class='app'>{html.escape(r.get('app_name', '?'))}</td>"
            f"<td>{html.escape(r.get('stack', '?'))}</td>"
            f"<td><span class='badge' style='background:{color}'>"
            f"{html.escape(disposition.upper())}</span></td>"
            f"<td class='num'>{html.escape(r.get('blockers', '?'))}</td>"
            f"<td class='num'>{html.escape(r.get('majors', '?'))}</td>"
            f"<td class='num'>{html.escape(r.get('backlog_items', '?'))}</td>"
            f"<td><a href='readouts/{html.escape(r['_file'])}'>readout</a></td>"
            "</tr>"
        )
    doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Portfolio Migration-Readiness Report</title>
<style>
  body {{ font-family: system-ui, sans-serif; background: #f5f7fa; color: #1e293b;
         margin: 0; }}
  header {{ background: linear-gradient(135deg, #0f172a, #1e3a5f); color: #fff;
            padding: 2rem 1rem; text-align: center; }}
  header h1 {{ margin: 0; font-size: 1.6rem; }}
  header p {{ margin: .5rem 0 0; color: #94a3b8; font-size: .9rem; }}
  main {{ max-width: 1100px; margin: 2rem auto; padding: 0 1rem; }}
  table {{ width: 100%; border-collapse: collapse; background: #fff;
           border: 1px solid #e2e8f0; border-radius: 8px; overflow: hidden; }}
  th {{ background: #0f172a; color: #fff; text-align: left; padding: .6rem .8rem;
        font-size: .8rem; text-transform: uppercase; letter-spacing: .04em; }}
  td {{ padding: .6rem .8rem; border-top: 1px solid #e2e8f0; font-size: .9rem; }}
  td.app {{ font-weight: 600; }}
  td.num {{ text-align: center; }}
  .badge {{ color: #fff; padding: .15rem .5rem; border-radius: 4px;
            font-size: .75rem; font-weight: 600; }}
</style>
</head>
<body>
<header>
  <h1>Portfolio Migration-Readiness Report</h1>
  <p>Wave 0 pilot tranche &middot; generated {date.today().isoformat()}</p>
</header>
<main>
<table>
<tr><th>Application</th><th>Stack</th><th>Disposition</th>
<th>Blockers</th><th>Majors</th><th>Backlog</th><th>Detail</th></tr>
{''.join(rows_html)}
</table>
</main>
</body>
</html>
"""
    REPORT.write_text(doc, encoding="utf-8")
    print(f"\nHTML report written to {REPORT}")


def main():
    readouts = load_readouts()
    if not readouts:
        print("No readouts found in assessment/readouts/ yet.")
        print("Run the assessment sessions first (see playbooks/).")
        return 1
    print_table(readouts)
    write_html(readouts)
    return 0


if __name__ == "__main__":
    sys.exit(main())
