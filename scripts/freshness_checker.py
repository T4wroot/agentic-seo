#!/usr/bin/env python3
"""Check content freshness signals and stale references."""

from __future__ import annotations

import argparse
import json
import os
import re
from datetime import date, datetime

from seo_common import load_html, parse_html


DATE_RE = re.compile(
    r"\b(?:20\d{2}|19\d{2})[-/](?:0?[1-9]|1[0-2])[-/](?:0?[1-9]|[12]\d|3[01])\b|"
    r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Sept|Oct|Nov|Dec)[a-z]*\.?\s+"
    r"(?:0?[1-9]|[12]\d|3[01]),?\s+(?:20\d{2}|19\d{2})\b",
    re.I,
)
YEAR_RE = re.compile(r"\b(20\d{2}|19\d{2})\b")
STAT_RE = re.compile(r"\b(\d+(?:\.\d+)?%|\$[\d,.]+|\d[\d,.]+\s+(?:users|customers|people|studies|respondents|pages))\b", re.I)


def _load_source(source: str, timeout: int) -> tuple[str, str, dict]:
    if os.path.exists(source):
        with open(source, "r", encoding="utf-8") as fh:
            return fh.read(), "", {"url": source, "status": None, "headers": {}, "error": None}
    return load_html(source, timeout=timeout)


def _parse_date(value: str | None) -> date | None:
    if not value:
        return None
    value = value.strip()
    for candidate in (value, value[:10]):
        try:
            return datetime.fromisoformat(candidate.replace("Z", "+00:00")).date()
        except ValueError:
            pass
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%B %d, %Y", "%b %d, %Y", "%B %d %Y", "%b %d %Y"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    return None


def _walk_json(value):
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_json(child)
    elif isinstance(value, list):
        for child in value:
            yield from _walk_json(child)


def _schema_dates(schema_items: list) -> dict[str, list[str]]:
    dates = {"datePublished": [], "dateModified": []}
    for item in schema_items:
        for node in _walk_json(item):
            for key in dates:
                if isinstance(node.get(key), str):
                    dates[key].append(node[key])
    return dates


def check_freshness(source: str, timeout: int = 15, today: date | None = None) -> dict:
    today = today or date.today()
    html, url, fetched = _load_source(source, timeout)
    parsed = parse_html(html, url)
    soup = parsed["soup"]
    body = parsed.get("body_text", "")

    meta_dates = {}
    for tag in soup.find_all("meta"):
        key = (tag.get("property") or tag.get("name") or "").lower()
        if key in {"article:published_time", "article:modified_time", "date", "last-modified", "dc.date"}:
            meta_dates[key] = tag.get("content")
    time_dates = [tag.get("datetime") or tag.get_text(" ", strip=True) for tag in soup.find_all("time")]
    schema_dates = _schema_dates(parsed.get("schema", []))

    parsed_dates = []
    for source_name, values in {
        "meta": list(meta_dates.values()),
        "time": time_dates,
        "schema_published": schema_dates["datePublished"],
        "schema_modified": schema_dates["dateModified"],
        "body": DATE_RE.findall(body),
    }.items():
        for raw in values:
            parsed_date = _parse_date(raw)
            if parsed_date:
                parsed_dates.append({"source": source_name, "raw": raw, "date": parsed_date.isoformat()})

    modified_dates = [_parse_date(value) for value in schema_dates["dateModified"] + [meta_dates.get("article:modified_time")]]
    modified_dates = [value for value in modified_dates if value]
    published_dates = [_parse_date(value) for value in schema_dates["datePublished"] + [meta_dates.get("article:published_time")]]
    published_dates = [value for value in published_dates if value]
    latest = max([_parse_date(item["date"]) for item in parsed_dates if _parse_date(item["date"])] or modified_dates or published_dates or [], default=None)

    old_years = sorted({int(year) for year in YEAR_RE.findall(body) if int(year) <= today.year - 3})
    stale_stat_count = 0
    for sentence in re.split(r"(?<=[.!?])\s+", body):
        if STAT_RE.search(sentence) and any(str(year) in sentence for year in old_years):
            stale_stat_count += 1

    mismatch = False
    if modified_dates and published_dates and max(modified_dates) < max(published_dates):
        mismatch = True

    age_days = (today - latest).days if latest else None
    score = 100
    if latest is None:
        score -= 35
    elif age_days is not None:
        score -= min(45, max(0, age_days - 365) // 30)
    score -= min(25, stale_stat_count * 5)
    score -= 15 if mismatch else 0

    issues = []
    if latest is None:
        issues.append({"severity": "warning", "message": "No parseable published or modified date found."})
    elif age_days and age_days > 730:
        issues.append({"severity": "warning", "message": f"Latest visible freshness date is {age_days} days old."})
    if stale_stat_count:
        issues.append({"severity": "warning", "message": f"{stale_stat_count} statistic sentence(s) reference old years."})
    if mismatch:
        issues.append({"severity": "warning", "message": "dateModified appears older than datePublished."})

    return {
        "url": url or source,
        "score": max(0, score),
        "latest_date": latest.isoformat() if latest else None,
        "age_days": age_days,
        "dates": parsed_dates[:50],
        "old_years": old_years,
        "stale_stat_sentences": stale_stat_count,
        "schema_date_mismatch": mismatch,
        "issues": issues,
        "fetch_error": fetched.get("error"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Check published/modified dates, stale stats, and freshness mismatches.")
    parser.add_argument("source", help="URL or local HTML file")
    parser.add_argument("--today", help="Override current date as YYYY-MM-DD for deterministic tests")
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--json", "-j", action="store_true", help="Output JSON")
    args = parser.parse_args()
    today = _parse_date(args.today) if args.today else None

    result = check_freshness(args.source, args.timeout, today)
    print(json.dumps(result, indent=2) if args.json else f"Score: {result['score']} Latest: {result['latest_date']}")


if __name__ == "__main__":
    main()
