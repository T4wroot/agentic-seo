#!/usr/bin/env python3
"""Check reference-file freshness markers."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path


UPDATED_RE = re.compile(r"<!--\s*Updated:\s*(\d{4}-\d{2}-\d{2})\s*-->")


@dataclass
class ReferenceStatus:
    path: str
    updated: str | None
    age_days: int | None
    status: str
    message: str


def check_file(path: Path, today: date, max_age_days: int) -> ReferenceStatus:
    text = path.read_text(encoding="utf-8")
    match = UPDATED_RE.search(text)
    rel = path.as_posix()
    if not match:
        return ReferenceStatus(rel, None, None, "error", "missing Updated marker")

    raw_date = match.group(1)
    try:
        updated = date.fromisoformat(raw_date)
    except ValueError:
        return ReferenceStatus(rel, raw_date, None, "error", "invalid Updated date")

    if updated > today:
        return ReferenceStatus(rel, raw_date, None, "error", "Updated date is in the future")

    age_days = (today - updated).days
    if age_days > max_age_days:
        return ReferenceStatus(
            rel,
            raw_date,
            age_days,
            "stale",
            f"older than {max_age_days} days",
        )

    return ReferenceStatus(rel, raw_date, age_days, "ok", "fresh")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate <!-- Updated: YYYY-MM-DD --> markers in reference markdown files."
    )
    parser.add_argument(
        "path",
        nargs="?",
        default="resources/references",
        help="Reference file or directory to check.",
    )
    parser.add_argument("--max-age-days", type=int, default=90, help="Freshness warning threshold.")
    parser.add_argument(
        "--fail-stale",
        action="store_true",
        help="Return a non-zero exit code for stale files, not only missing/invalid markers.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable results.")
    args = parser.parse_args()

    target = Path(args.path)
    if target.is_dir():
        files = sorted(target.glob("*.md"))
    else:
        files = [target]

    today = date.today()
    statuses = [check_file(path, today, args.max_age_days) for path in files]
    hard_failures = [item for item in statuses if item.status == "error"]
    stale = [item for item in statuses if item.status == "stale"]

    if args.json:
        print(json.dumps([asdict(item) for item in statuses], indent=2, sort_keys=True))
    else:
        for item in statuses:
            label = {"ok": "OK", "stale": "WARN", "error": "ERROR"}[item.status]
            age = "" if item.age_days is None else f" ({item.age_days} days old)"
            print(f"{label}: {item.path}: {item.message}{age}")

    if hard_failures or (args.fail_stale and stale):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
