#!/usr/bin/env python3
"""Analyze server logs for crawl budget and bot status-code patterns."""

from __future__ import annotations

import argparse
import gzip
import json
import re
from collections import Counter, defaultdict
from datetime import datetime

from seo_common import print_json_or_text


LOG_RE = re.compile(
    r'(?P<ip>\S+) \S+ \S+ \[(?P<time>[^\]]+)\] "(?P<method>[A-Z]+) (?P<path>\S+) (?P<protocol>[^"]+)" '
    r"(?P<status>\d{3}) (?P<bytes>\S+)(?: \"(?P<referrer>[^\"]*)\" \"(?P<ua>[^\"]*)\")?"
)

BOT_PATTERNS = {
    "Googlebot": re.compile(r"googlebot|adsbot-google|google-inspectiontool", re.I),
    "Bingbot": re.compile(r"bingbot", re.I),
    "GPTBot": re.compile(r"gptbot|chatgpt-user|oai-searchbot", re.I),
    "ClaudeBot": re.compile(r"claudebot|claude-user", re.I),
    "PerplexityBot": re.compile(r"perplexitybot", re.I),
    "Applebot": re.compile(r"applebot", re.I),
    "OtherBot": re.compile(r"bot|crawler|spider|slurp", re.I),
}


def _open_log(path: str):
    if path.endswith(".gz"):
        return gzip.open(path, "rt", encoding="utf-8", errors="replace")
    return open(path, "r", encoding="utf-8", errors="replace")


def parse_log_line(line: str) -> dict | None:
    match = LOG_RE.search(line)
    if not match:
        return None
    data = match.groupdict()
    data["status"] = int(data["status"])
    try:
        data["bytes"] = int(data["bytes"]) if data["bytes"] != "-" else 0
    except ValueError:
        data["bytes"] = 0
    data["bot"] = classify_bot(data.get("ua") or "")
    data["date"] = parse_log_date(data.get("time") or "")
    return data


def parse_log_date(value: str) -> str:
    try:
        return datetime.strptime(value.split()[0], "%d/%b/%Y:%H:%M:%S").date().isoformat()
    except Exception:
        return ""


def classify_bot(user_agent: str) -> str:
    for name, pattern in BOT_PATTERNS.items():
        if pattern.search(user_agent or ""):
            return name
    return "Human/Unknown"


def analyze_logs(paths: list[str], max_lines: int | None = None) -> dict:
    total = 0
    parsed_count = 0
    status_counter = Counter()
    bot_counter = Counter()
    bot_status = defaultdict(Counter)
    wasted = []
    top_paths = Counter()
    google_paths = Counter()
    daily_googlebot = Counter()
    parse_errors = 0

    for path in paths:
        with _open_log(path) as fh:
            for line in fh:
                total += 1
                if max_lines and total > max_lines:
                    break
                row = parse_log_line(line)
                if not row:
                    parse_errors += 1
                    continue
                parsed_count += 1
                status = row["status"]
                bot = row["bot"]
                path_only = row["path"].split("?", 1)[0]
                status_counter[str(status)] += 1
                bot_counter[bot] += 1
                bot_status[bot][str(status)] += 1
                top_paths[path_only] += 1
                if bot == "Googlebot":
                    google_paths[path_only] += 1
                    if row["date"]:
                        daily_googlebot[row["date"]] += 1
                if bot != "Human/Unknown" and (status >= 400 or "?" in row["path"]):
                    wasted.append(
                        {
                            "bot": bot,
                            "status": status,
                            "path": row["path"],
                            "user_agent": row.get("ua") or "",
                        }
                    )
            if max_lines and total > max_lines:
                break

    issues = []
    bot_hits = parsed_count - bot_counter.get("Human/Unknown", 0)
    bot_errors = sum(1 for item in wasted if item["status"] >= 400)
    if bot_errors:
        issues.append({"severity": "warning", "type": "bot_errors", "count": bot_errors, "message": "Bots are hitting 4xx/5xx URLs"})
    parameter_hits = sum(1 for item in wasted if "?" in item["path"])
    if parameter_hits:
        issues.append({"severity": "info", "type": "parameter_crawl", "count": parameter_hits, "message": "Bots are crawling parameterized URLs"})

    return {
        "summary": {
            "lines_read": min(total, max_lines or total),
            "parsed_lines": parsed_count,
            "parse_errors": parse_errors,
            "bot_hits": bot_hits,
            "googlebot_hits": bot_counter.get("Googlebot", 0),
            "bot_error_hits": bot_errors,
            "parameterized_bot_hits": parameter_hits,
        },
        "status_codes": dict(status_counter.most_common()),
        "bot_hits": dict(bot_counter.most_common()),
        "bot_status_codes": {bot: dict(counter.most_common()) for bot, counter in bot_status.items()},
        "top_paths": [{"path": path, "hits": hits} for path, hits in top_paths.most_common(50)],
        "top_googlebot_paths": [{"path": path, "hits": hits} for path, hits in google_paths.most_common(50)],
        "daily_googlebot_hits": dict(sorted(daily_googlebot.items())),
        "wasted_crawl_examples": wasted[:100],
        "issues": issues,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze server logs for crawl budget patterns")
    parser.add_argument("log_files", nargs="+", help="Common/combined access logs, optionally .gz")
    parser.add_argument("--max-lines", type=int, help="Maximum log lines to read")
    parser.add_argument("--json", "-j", action="store_true", help="Output JSON")
    args = parser.parse_args()

    result = analyze_logs(args.log_files, max_lines=args.max_lines)
    lines = [
        "Log file crawl analysis",
        (
            f"Parsed: {result['summary']['parsed_lines']}  "
            f"Bot hits: {result['summary']['bot_hits']}  "
            f"Googlebot hits: {result['summary']['googlebot_hits']}  "
            f"Bot errors: {result['summary']['bot_error_hits']}"
        ),
    ]
    lines.extend(f"[{issue['severity']}] {issue['message']}: {issue['count']}" for issue in result["issues"])
    print_json_or_text(result, args.json, lines)


if __name__ == "__main__":
    main()
