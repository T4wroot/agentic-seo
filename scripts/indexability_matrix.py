#!/usr/bin/env python3
"""Build per-URL indexability verdicts."""

from __future__ import annotations

import argparse
import json

from seo_common import (
    discover_sitemap_urls,
    fetch_robots,
    fetch_url,
    parse_html,
    parse_sitemap_xml,
    read_urls,
    robots_allowed,
    normalize_url,
)


def urls_from_sitemaps(site: str, timeout: int) -> set[str]:
    urls = set()
    for sm in discover_sitemap_urls(site, timeout=timeout)[:10]:
        fetched = fetch_url(sm, timeout=timeout, max_bytes=8_000_000)
        parsed = parse_sitemap_xml(fetched.get("text") or "", sm)
        urls.update(row["loc"] for row in parsed["urls"])
    return urls


def evaluate(urls: list[str], site: str | None = None, timeout: int = 15) -> dict:
    base = site or (urls[0] if urls else "")
    robots = fetch_robots(base, timeout=timeout) if base else {"parsed": None}
    sitemap_urls = urls_from_sitemaps(base, timeout) if base else set()
    rows = []
    for url in urls:
        url = normalize_url(url)
        allowed, robots_rule = robots_allowed(robots.get("parsed"), url, "Googlebot")
        fetched = fetch_url(url, timeout=timeout, max_bytes=1_500_000)
        headers = fetched.get("headers", {})
        xrobots = headers.get("x-robots-tag") or headers.get("X-Robots-Tag")
        html = {}
        ctype = headers.get("content-type", "")
        if fetched.get("text") and "html" in ctype:
            html = parse_html(fetched["text"], fetched.get("url") or url)
        blockers = []
        if not allowed:
            blockers.append("robots.txt disallow")
        if fetched.get("status") != 200:
            blockers.append(f"HTTP {fetched.get('status')}")
        if html.get("meta_robots") and "noindex" in html["meta_robots"].lower():
            blockers.append("meta robots noindex")
        if xrobots and "noindex" in xrobots.lower():
            blockers.append("x-robots-tag noindex")
        if html.get("canonical") and normalize_url(html["canonical"]) != normalize_url(fetched.get("url") or url):
            blockers.append("canonicalized to different URL")
        rows.append({
            "url": url,
            "final_url": fetched.get("url"),
            "status": fetched.get("status"),
            "robots_allowed": allowed,
            "robots_rule": robots_rule,
            "meta_robots": html.get("meta_robots"),
            "x_robots_tag": xrobots,
            "canonical": html.get("canonical"),
            "in_sitemap": url in sitemap_urls,
            "redirects": fetched.get("redirect_chain", []),
            "verdict": "indexable" if not blockers else "not_indexable",
            "blockers": blockers,
            "error": fetched.get("error"),
        })
    return {"site": normalize_url(base) if base else None, "count": len(rows), "rows": rows}


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate an indexability matrix")
    parser.add_argument("urls", nargs="*")
    parser.add_argument("--url-file")
    parser.add_argument("--site", help="Site URL for robots/sitemap context")
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--json", "-j", action="store_true")
    args = parser.parse_args()
    urls = read_urls(args.urls, args.url_file)
    result = evaluate(urls, args.site, args.timeout)
    if args.json:
        print(json.dumps(result, indent=2))
    else:
        for row in result["rows"]:
            print(f"{row['verdict']}\t{row['status']}\t{row['url']}\t{', '.join(row['blockers'])}")


if __name__ == "__main__":
    main()
