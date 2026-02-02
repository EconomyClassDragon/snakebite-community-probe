#!/usr/bin/env python3
"""Validate submitted JSONL files for Snakebite community probe.

- Enforces schema.json (no extra fields)
- Rejects obviously sensitive fields (anything that looks like source code)
- Sanitizes error strings for local path leakage (best-effort)

Usage:
  python3 scripts/validate.py results

Exit 0 on success, non-zero on failure.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from typing import Any, Dict


SCHEMA_PATH = Path(__file__).resolve().parents[1] / "schema.json"

# Fields that must never appear
BANNED_KEYS = {
    "source",
    "code",
    "prompt",
    "messages",
    "completion",
    "content",
    "input",
    "output",
}

PATH_RE = re.compile(r"(/[^\s:\"]+)+")


def load_schema() -> Dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def sanitize_error(s: str) -> str:
    # Replace absolute paths with basename-ish placeholders.
    def repl(m: re.Match) -> str:
        p = m.group(0)
        base = p.split("/")[-1]
        return f"<path>/{base}"

    s = PATH_RE.sub(repl, s)
    if len(s) > 2000:
        s = s[:2000] + "…"
    return s


def validate_row(row: Dict[str, Any], allowed_keys: set[str]) -> None:
    extra = set(row.keys()) - allowed_keys
    if extra:
        raise ValueError(f"extra keys not allowed: {sorted(extra)}")

    # banned keys (even if schema doesn't allow them, be explicit)
    lowered = {k.lower() for k in row.keys()}
    if lowered & BANNED_KEYS:
        raise ValueError(f"banned keys present: {sorted(lowered & BANNED_KEYS)}")

    # basic types
    if not isinstance(row.get("model"), str) or not row["model"].strip():
        raise ValueError("model must be non-empty string")
    if not isinstance(row.get("sha256"), str) or not re.fullmatch(r"[a-f0-9]{64}", row["sha256"]):
        raise ValueError("sha256 must be 64 lowercase hex chars")
    if not isinstance(row.get("syntax_valid_before"), bool) or not isinstance(row.get("syntax_valid_after"), bool):
        raise ValueError("syntax_valid_before/after must be boolean")
    if not isinstance(row.get("fix_count"), int) or row["fix_count"] < 0:
        raise ValueError("fix_count must be non-negative int")

    # sanitize error strings (best effort) and ensure they remain strings
    for k in ("error_before", "error_after", "error"):
        if k in row and row[k] is not None:
            if not isinstance(row[k], str):
                raise ValueError(f"{k} must be string")
            row[k] = sanitize_error(row[k])


def main(argv: list[str]) -> int:
    root = Path(argv[0] if argv else "results").resolve()
    if not root.exists():
        print(f"missing: {root}", file=sys.stderr)
        return 2

    schema = load_schema()
    allowed_keys = set(schema.get("properties", {}).keys())

    jsonl_files = [p for p in root.rglob("*.jsonl") if p.is_file()]
    if not jsonl_files:
        print("No .jsonl files found (ok)")
        return 0

    bad = 0
    for p in jsonl_files:
        rel = p.relative_to(root)
        with p.open("r", encoding="utf-8") as f:
            for i, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                    if not isinstance(row, dict):
                        raise ValueError("row is not object")
                    validate_row(row, allowed_keys)
                except Exception as e:
                    bad += 1
                    print(f"FAIL {rel}:{i}: {e}")

    if bad:
        print(f"Validation failed: {bad} error(s)")
        return 1

    print(f"Validation ok: {len(jsonl_files)} file(s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
