#!/usr/bin/env python3
"""Find backlink reclaim opportunities from a backlink export."""

from __future__ import annotations

import argparse
import csv
import sys
from collections import Counter

from seo_common import fetch_url, normalize_url, print_json_or_text


def _first_existing(row: dict, names: list[str]) -> str:
    lowered = {str(k).lower().strip(): v for k, v in row.items()}
    for name in names:
        if name.lower() in lowered and lowered[name.lower()]:
            return str(lowered[name.lower()]).strip()
    return ""


def read_backlink_export(path: str, source_column: str | None = None, target_column: str | None = None) -> list[dict]:
    stream = sys.stdin if path == "-" else open(path, "r", encoding="utf-8-sig", newline="")
    with stream:
        sample = stream.read(4096)
        stream.seek(0)
        dialect = csv.Sniffer().sniff(sample) if sample else csv.excel
        reader = csv.DictReader(stream, dialect=dialect)
        rows = []
        for row in reader:
            source = row.get(source_column) if source_column else _first_existing(row, ["source_url", "source", "referring_page", "referrer", "backlink"])
            target = row.get(target_column) if target_column else _first_existing(row, ["target_url", "target", "linked_url", "destination", "url"])
            if not target:
                continue
            rows.append({"source_url": (source or "").strip(), "target_url": normalize_url(target.strip()), "raw": dict(row)})
        return rows


def analyze_backlinks(rows: list[dict], timeout: int = 15, max_rows: int = 500, long_chain_threshold: int = 2) -> dict:
    checked = []
    opportunities = []
    target_counter = Counter(row["target_url"] for row in rows)
    unique_targets = list(target_counter)[:max_rows]

    target_status = {}
    for target in unique_targets:
        fetched = fetch_url(target, method="HEAD", timeout=timeout, allow_redirects=True, max_bytes=0)
        if fetched.get("status") in (405, 403, None) and fetched.get("error"):
            fetched = fetch_url(target, method="GET", timeout=timeout, allow_redirects=True, max_bytes=200_000)
        row = {
            "target_url": target,
            "backlink_count": target_counter[target],
            "status": fetched.get("status"),
            "final_url": fetched.get("url"),
            "redirect_chain": fetched.get("redirect_chain", []),
            "error": fetched.get("error"),
        }
        target_status[target] = row
        checked.append(row)

    for row in rows:
        status = target_status.get(row["target_url"], {})
        code = status.get("status")
        chain = status.get("redirect_chain") or []
        if code and code >= 400:
            opportunities.append(
                {
                    "type": "broken_backlink_target",
                    "severity": "high",
                    "source_url": row.get("source_url"),
                    "target_url": row["target_url"],
                    "status": code,
                    "fix": "Restore the URL or 301 redirect it to the closest relevant live page.",
                }
            )
        elif len(chain) > long_chain_threshold:
            opportunities.append(
                {
                    "type": "long_redirect_chain",
                    "severity": "medium",
                    "source_url": row.get("source_url"),
                    "target_url": row["target_url"],
                    "final_url": status.get("final_url"),
                    "redirect_hops": len(chain),
                    "fix": "Update redirects so the backlink target resolves in one hop.",
                }
            )

    return {
        "summary": {
            "backlink_rows": len(rows),
            "unique_targets": len(target_counter),
            "targets_checked": len(checked),
            "opportunities": len(opportunities),
            "broken_targets": sum(1 for item in checked if item.get("status") and item["status"] >= 400),
            "long_redirect_chains": sum(1 for item in checked if len(item.get("redirect_chain") or []) > long_chain_threshold),
        },
        "targets": checked,
        "opportunities": opportunities,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Find backlink reclaim opportunities from a CSV export")
    parser.add_argument("csv_file", help="Backlink CSV/TSV export path, or '-' for stdin")
    parser.add_argument("--source-column", help="Column containing the referring/source page URL")
    parser.add_argument("--target-column", help="Column containing the linked target URL")
    parser.add_argument("--max-rows", type=int, default=500, help="Maximum unique target URLs to check")
    parser.add_argument("--long-chain-threshold", type=int, default=2, help="Redirect hops above this count are flagged")
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--json", "-j", action="store_true", help="Output JSON")
    args = parser.parse_args()

    rows = read_backlink_export(args.csv_file, source_column=args.source_column, target_column=args.target_column)
    result = analyze_backlinks(rows, timeout=args.timeout, max_rows=args.max_rows, long_chain_threshold=args.long_chain_threshold)
    lines = [
        "Redirect/backlink reclaim audit",
        (
            f"Rows: {result['summary']['backlink_rows']}  "
            f"Targets checked: {result['summary']['targets_checked']}  "
            f"Opportunities: {result['summary']['opportunities']}"
        ),
    ]
    lines.extend(
        f"{item['type']}: {item['target_url']} ({item.get('status') or item.get('redirect_hops')})"
        for item in result["opportunities"][:25]
    )
    print_json_or_text(result, args.json, lines)


if __name__ == "__main__":
    main()
