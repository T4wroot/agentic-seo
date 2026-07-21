#!/usr/bin/env python3
"""Detect content decay and striking-distance keywords from CSV exports."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import date, datetime


def _float(value, default: float = 0.0) -> float:
    try:
        return float(str(value or "").replace(",", ""))
    except ValueError:
        return default


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    value = value.strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(value[:10], fmt).date()
        except ValueError:
            continue
    return None


def _read_rows(path: str, args) -> list[dict]:
    with open(path, newline="", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        rows = []
        for raw in reader:
            row = {key.lower().strip(): value for key, value in raw.items() if key}
            rows.append({
                "url": row.get(args.url_column.lower()) or row.get("page") or row.get("landing page") or "",
                "query": row.get(args.query_column.lower()) or row.get("keyword") or "",
                "date": _parse_date(row.get(args.date_column.lower())),
                "clicks": _float(row.get(args.clicks_column.lower())),
                "impressions": _float(row.get(args.impressions_column.lower())),
                "position": _float(row.get(args.position_column.lower())),
            })
    return [row for row in rows if row["url"]]


def detect_decay(
    path: str,
    args,
    split_date: date | None = None,
    decline_threshold: float = 0.2,
    min_impressions: float = 100.0,
) -> dict:
    rows = _read_rows(path, args)
    dated_rows = [row for row in rows if row["date"]]
    if split_date is None and dated_rows:
        dates = sorted(row["date"] for row in dated_rows)
        split_date = dates[len(dates) // 2]

    grouped = defaultdict(lambda: {"previous": [], "recent": []})
    for row in rows:
        period = "recent"
        if split_date and row["date"]:
            period = "recent" if row["date"] >= split_date else "previous"
        grouped[row["url"]][period].append(row)

    declining_pages = []
    striking_distance = []
    for url, periods in grouped.items():
        previous_clicks = sum(row["clicks"] for row in periods["previous"])
        recent_clicks = sum(row["clicks"] for row in periods["recent"])
        previous_impressions = sum(row["impressions"] for row in periods["previous"])
        recent_impressions = sum(row["impressions"] for row in periods["recent"])
        drop = (previous_clicks - recent_clicks) / previous_clicks if previous_clicks else 0.0
        if previous_clicks > 0 and drop >= decline_threshold and max(previous_impressions, recent_impressions) >= min_impressions:
            declining_pages.append({
                "url": url,
                "previous_clicks": round(previous_clicks, 2),
                "recent_clicks": round(recent_clicks, 2),
                "click_drop_pct": round(drop * 100, 2),
                "previous_impressions": round(previous_impressions, 2),
                "recent_impressions": round(recent_impressions, 2),
            })

        by_query = defaultdict(list)
        for row in periods["recent"]:
            if row["query"]:
                by_query[row["query"]].append(row)
        for query, query_rows in by_query.items():
            impressions = sum(row["impressions"] for row in query_rows)
            if impressions < min_impressions:
                continue
            avg_position = sum(row["position"] * row["impressions"] for row in query_rows) / max(1.0, impressions)
            if 4.0 <= avg_position <= 20.0:
                striking_distance.append({
                    "url": url,
                    "query": query,
                    "recent_impressions": round(impressions, 2),
                    "avg_position": round(avg_position, 2),
                    "recent_clicks": round(sum(row["clicks"] for row in query_rows), 2),
                })

    declining_pages.sort(key=lambda row: row["click_drop_pct"], reverse=True)
    striking_distance.sort(key=lambda row: (row["avg_position"], -row["recent_impressions"]))
    return {
        "rows": len(rows),
        "split_date": split_date.isoformat() if split_date else None,
        "declining_pages": declining_pages,
        "striking_distance_keywords": striking_distance[:200],
        "issues": [
            {"severity": "warning", "message": "No date column could be parsed; all rows treated as recent."}
        ] if not split_date else [],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Detect declining pages and striking-distance keywords from GSC-style CSV.")
    parser.add_argument("csv_file", nargs="?", help="CSV export path")
    parser.add_argument("--csv", dest="csv_path", help="CSV export path")
    parser.add_argument("--split-date", help="Boundary date YYYY-MM-DD. Earlier rows are previous; later rows are recent.")
    parser.add_argument("--decline-threshold", type=float, default=0.2, help="Click drop ratio required for decay.")
    parser.add_argument("--min-impressions", type=float, default=100.0)
    parser.add_argument("--date-column", default="date")
    parser.add_argument("--url-column", default="url")
    parser.add_argument("--query-column", default="query")
    parser.add_argument("--clicks-column", default="clicks")
    parser.add_argument("--impressions-column", default="impressions")
    parser.add_argument("--position-column", default="position")
    parser.add_argument("--json", "-j", action="store_true", help="Output JSON")
    args = parser.parse_args()
    path = args.csv_path or args.csv_file
    if not path:
        parser.error("CSV path required as positional csv_file or --csv")
    split = _parse_date(args.split_date) if args.split_date else None
    result = detect_decay(path, args, split, args.decline_threshold, args.min_impressions)
    text = f"Declining pages: {len(result['declining_pages'])} Striking-distance keywords: {len(result['striking_distance_keywords'])}"
    print(json.dumps(result, indent=2) if args.json else text)


if __name__ == "__main__":
    main()
