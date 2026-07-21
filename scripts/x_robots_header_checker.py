#!/usr/bin/env python3
"""Inspect X-Robots-Tag headers."""

from __future__ import annotations

import argparse
import json

from seo_common import extract_directives, fetch_url, read_urls


def check_headers(urls: list[str], timeout: int = 15) -> dict:
    rows = []
    for url in urls:
        fetched = fetch_url(url, method="HEAD", timeout=timeout)
        if fetched.get("status") in (405, 403) or fetched.get("error"):
            fetched = fetch_url(url, method="GET", timeout=timeout, max_bytes=100_000)
        headers = fetched.get("headers", {})
        value = headers.get("x-robots-tag") or headers.get("X-Robots-Tag")
        directives = sorted(extract_directives(value))
        rows.append({
            "url": url,
            "status": fetched.get("status"),
            "final_url": fetched.get("url"),
            "x_robots_tag": value,
            "directives": directives,
            "indexing_effect": "blocked" if "noindex" in directives or "none" in directives else "allowed",
            "follow_effect": "blocked" if "nofollow" in directives or "none" in directives else "allowed",
            "archive_effect": "blocked" if "noarchive" in directives else "allowed",
            "snippet_rules": [d for d in directives if d.startswith(("max-snippet", "max-image-preview", "max-video-preview", "nosnippet"))],
            "error": fetched.get("error"),
        })
    return {"count": len(rows), "rows": rows}


def main() -> None:
    parser = argparse.ArgumentParser(description="Check X-Robots-Tag headers")
    parser.add_argument("urls", nargs="*")
    parser.add_argument("--url-file")
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--json", "-j", action="store_true")
    args = parser.parse_args()
    result = check_headers(read_urls(args.urls, args.url_file), args.timeout)
    print(json.dumps(result, indent=2) if args.json else "\n".join(f"{r['indexing_effect']}\t{r['x_robots_tag'] or '-'}\t{r['url']}" for r in result["rows"]))


if __name__ == "__main__":
    main()
