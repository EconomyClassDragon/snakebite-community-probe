#!/usr/bin/env python3
"""Aggregate Snakebite JSONL results into human-friendly summaries.

Outputs:
- public/summary.json
- public/summary.md

Usage:
  python3 scripts/aggregate.py
"""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
PUBLIC = ROOT / "public"


def iter_rows() -> Iterable[Dict[str, Any]]:
    for p in RESULTS.rglob("*.jsonl"):
        if not p.is_file():
            continue
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                    if isinstance(row, dict):
                        yield row
                except Exception:
                    continue


def err_class(s: str) -> str:
    if not s:
        return ""
    if "IndentationError" in s:
        return "IndentationError"
    if "SyntaxError" in s:
        return "SyntaxError"
    if "TabError" in s:
        return "TabError"
    if "EOL while scanning" in s or "unexpected EOF" in s:
        return "EOF"
    return "Other"


def pct(n: int, d: int) -> float:
    return (100.0 * n / d) if d else 0.0


def main() -> int:
    rows = list(iter_rows())

    by_model = defaultdict(list)
    for r in rows:
        m = str(r.get("model") or "unknown")
        by_model[m].append(r)

    summary = {
        "generatedAt": datetime.now().isoformat(timespec="seconds"),
        "totalRows": len(rows),
        "models": {},
    }

    md_lines = []
    md_lines.append(f"# Snakebite community summary\n")
    md_lines.append(f"Generated: {summary['generatedAt']}\n")
    md_lines.append(f"Total rows: **{len(rows)}**\n")

    md_lines.append("## Per-model stats\n")
    md_lines.append("| Model | Rows | Syntax valid (before) | Syntax valid (after) | Repaired (before→after) | Avg fix count | Top error classes (before) |")
    md_lines.append("| --- | ---: | ---: | ---: | ---: | ---: | --- |")

    for model, rs in sorted(by_model.items(), key=lambda kv: len(kv[1]), reverse=True):
        total = len(rs)
        before_ok = sum(1 for r in rs if r.get("syntax_valid_before") is True)
        after_ok = sum(1 for r in rs if r.get("syntax_valid_after") is True)
        repaired = sum(1 for r in rs if (r.get("syntax_valid_before") is False and r.get("syntax_valid_after") is True))
        fix_counts = [int(r.get("fix_count") or 0) for r in rs]
        avg_fix = (sum(fix_counts) / total) if total else 0.0

        errc = Counter()
        for r in rs:
            if r.get("syntax_valid_before") is True:
                continue
            eb = str(r.get("error_before") or r.get("error") or "")
            errc[err_class(eb)] += 1
        top_err = ", ".join([f"{k}:{v}" for k, v in errc.most_common(3)]) if errc else ""

        summary["models"][model] = {
            "rows": total,
            "syntaxValidBefore": before_ok,
            "syntaxValidAfter": after_ok,
            "repaired": repaired,
            "avgFixCount": avg_fix,
            "topErrorClassesBefore": errc,
        }

        md_lines.append(
            f"| {model} | {total} | {pct(before_ok,total):.1f}% | {pct(after_ok,total):.1f}% | {pct(repaired,total):.1f}% | {avg_fix:.2f} | {top_err} |"
        )

    PUBLIC.mkdir(parents=True, exist_ok=True)
    (PUBLIC / "summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False, default=lambda o: dict(o)), encoding="utf-8")
    (PUBLIC / "summary.md").write_text("\n".join(md_lines) + "\n", encoding="utf-8")

    # Tiny static HTML page for humans (GitHub Pages friendly).
    rows_html = []
    for model, stats in summary["models"].items():
        rows_html.append(
            f"<tr><td><code>{model}</code></td>"
            f"<td style='text-align:right'>{stats['rows']}</td>"
            f"<td style='text-align:right'>{pct(int(stats['syntaxValidBefore']), int(stats['rows'])):.1f}%</td>"
            f"<td style='text-align:right'>{pct(int(stats['syntaxValidAfter']), int(stats['rows'])):.1f}%</td>"
            f"<td style='text-align:right'>{pct(int(stats['repaired']), int(stats['rows'])):.1f}%</td>"
            f"<td style='text-align:right'>{stats['avgFixCount']:.2f}</td></tr>"
        )

    index_html = f"""<!doctype html>
<html lang=\"en\">
<head>
  <meta charset=\"utf-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1\" />
  <title>Snakebite community probe</title>
  <style>
    body {{ font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; max-width: 980px; margin: 32px auto; padding: 0 16px; }}
    table {{ border-collapse: collapse; width: 100%; }}
    th, td {{ border-bottom: 1px solid #ddd; padding: 8px; vertical-align: top; }}
    th {{ text-align: left; background: #f6f6f6; }}
    code {{ background: #f3f3f3; padding: 1px 4px; border-radius: 4px; }}
    .muted {{ color: #666; }}
  </style>
</head>
<body>
  <h1>Snakebite community probe</h1>
  <p class=\"muted\">Generated: {summary['generatedAt']} · Total rows: <b>{summary['totalRows']}</b></p>

  <p>
    <a href=\"summary.md\">summary.md</a> ·
    <a href=\"summary.json\">summary.json</a>
  </p>

  <h2>Per-model stats</h2>
  <table>
    <thead>
      <tr>
        <th>Model</th>
        <th style=\"text-align:right\">Rows</th>
        <th style=\"text-align:right\">Syntax valid (before)</th>
        <th style=\"text-align:right\">Syntax valid (after)</th>
        <th style=\"text-align:right\">Repaired (before→after)</th>
        <th style=\"text-align:right\">Avg fix count</th>
      </tr>
    </thead>
    <tbody>
      {''.join(rows_html) if rows_html else '<tr><td colspan="6" class="muted">No data yet.</td></tr>'}
    </tbody>
  </table>

  <h2>How to contribute</h2>
  <p>See <code>README.md</code> and <code>CONTRIBUTING.md</code> in the repo.</p>
</body>
</html>
"""

    (PUBLIC / "index.html").write_text(index_html, encoding="utf-8")

    print(f"wrote public/index.html, summary.md, summary.json ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
