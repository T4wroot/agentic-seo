#!/usr/bin/env python3
"""Find sitemap URLs that are not reachable from an internal crawl."""

from __future__ import annotations

import argparse
from collections import deque
from urllib.parse import urlparse

from seo_common import (
    discover_sitemap_urls,
    fetch_url,
    normalize_url,
    parse_html,
    parse_sitemap_xml,
    print_json_or_text,
    same_host,
)


def _page_key(url: str) -> str:
    parsed = urlparse(normalize_url(url))
    path = parsed.path or "/"
    if path != "/":
        path = path.rstrip("/")
    return f"{parsed.scheme}://{parsed.netloc}{path}"


def load_sitemap_urls(site_url: str, sitemap_urls: list[str] | None = None, timeout: int = 15, max_sitemaps: int = 25) -> dict:
    queue = list(dict.fromkeys(sitemap_urls or discover_sitemap_urls(site_url, timeout=timeout)))
    seen_sitemaps = set()
    urls = []
    errors = []

    while queue and len(seen_sitemaps) < max_sitemaps:
        sitemap_url = normalize_url(queue.pop(0), site_url)
        if sitemap_url in seen_sitemaps:
            continue
        seen_sitemaps.add(sitemap_url)
        fetched = fetch_url(sitemap_url, timeout=timeout, max_bytes=8_000_000)
        if fetched.get("status") != 200 or not fetched.get("text"):
            errors.append({"url": sitemap_url, "status": fetched.get("status"), "error": fetched.get("error")})
            continue
        parsed = parse_sitemap_xml(fetched["text"], sitemap_url)
        if parsed.get("error"):
            errors.append({"url": sitemap_url, "error": parsed["error"]})
            continue
        queue.extend(item["loc"] for item in parsed.get("sitemaps", []))
        urls.extend(item["loc"] for item in parsed.get("urls", []))

    deduped = []
    seen = set()
    for url in urls:
        key = _page_key(url)
        if key not in seen:
            seen.add(key)
            deduped.append(key)
    return {"sitemaps_checked": sorted(seen_sitemaps), "urls": deduped, "errors": errors}


def crawl_reachable_pages(start_url: str, depth: int = 2, max_pages: int = 100, timeout: int = 15) -> dict:
    start_url = normalize_url(start_url)
    queue = deque([(start_url, 0)])
    reachable = {}
    errors = []

    while queue and len(reachable) < max_pages:
        url, current_depth = queue.popleft()
        key = _page_key(url)
        if key in reachable or current_depth > depth:
            continue
        fetched = fetch_url(url, timeout=timeout, max_bytes=2_000_000)
        reachable[key] = {
            "url": key,
            "status": fetched.get("status"),
            "final_url": fetched.get("url"),
            "depth": current_depth,
            "in_sitemap": False,
        }
        if fetched.get("status") != 200 or not fetched.get("text"):
            errors.append({"url": url, "status": fetched.get("status"), "error": fetched.get("error")})
            continue
        if current_depth >= depth:
            continue
        html = parse_html(fetched["text"], fetched.get("url") or url)
        for link in html.get("links", []):
            href = link.get("href") or ""
            if href and same_host(start_url, href):
                target = _page_key(href)
                if target not in reachable and len(reachable) + len(queue) < max_pages:
                    queue.append((target, current_depth + 1))

    return {"pages": reachable, "errors": errors}


def find_orphan_pages(site_url: str, sitemap_urls: list[str] | None = None, depth: int = 2, max_pages: int = 100, timeout: int = 15) -> dict:
    site_url = normalize_url(site_url)
    sitemap = load_sitemap_urls(site_url, sitemap_urls=sitemap_urls, timeout=timeout)
    crawl = crawl_reachable_pages(site_url, depth=depth, max_pages=max_pages, timeout=timeout)
    sitemap_set = set(sitemap["urls"])
    reachable_set = set(crawl["pages"])
    for page in crawl["pages"].values():
        page["in_sitemap"] = page["url"] in sitemap_set

    orphan_urls = sorted(sitemap_set - reachable_set)
    discovered_not_in_sitemap = sorted(reachable_set - sitemap_set)
    issues = []
    if orphan_urls:
        issues.append({"severity": "warning", "type": "sitemap_orphans", "count": len(orphan_urls), "message": "Sitemap URLs were not reached by crawl"})
    if discovered_not_in_sitemap:
        issues.append({"severity": "info", "type": "crawl_only_pages", "count": len(discovered_not_in_sitemap), "message": "Crawled URLs are not present in sitemap"})

    return {
        "site": site_url,
        "summary": {
            "sitemaps_checked": len(sitemap["sitemaps_checked"]),
            "sitemap_urls": len(sitemap_set),
            "reachable_pages": len(reachable_set),
            "orphan_pages": len(orphan_urls),
            "discovered_not_in_sitemap": len(discovered_not_in_sitemap),
        },
        "sitemaps_checked": sitemap["sitemaps_checked"],
        "orphan_pages": orphan_urls,
        "discovered_not_in_sitemap": discovered_not_in_sitemap,
        "reachable_pages": list(crawl["pages"].values()),
        "issues": issues,
        "errors": {"sitemap": sitemap["errors"], "crawl": crawl["errors"]},
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Find sitemap URLs not reachable from an internal crawl")
    parser.add_argument("site", help="Website URL")
    parser.add_argument("--sitemap", action="append", help="Explicit sitemap URL; can be repeated")
    parser.add_argument("--depth", type=int, default=2, help="Internal crawl depth (default: 2)")
    parser.add_argument("--max-pages", type=int, default=100, help="Maximum crawl pages (default: 100)")
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--json", "-j", action="store_true", help="Output JSON")
    args = parser.parse_args()

    result = find_orphan_pages(args.site, sitemap_urls=args.sitemap, depth=args.depth, max_pages=args.max_pages, timeout=args.timeout)
    lines = [
        f"Orphan page check for {result['site']}",
        (
            f"Sitemap URLs: {result['summary']['sitemap_urls']}  "
            f"Reachable pages: {result['summary']['reachable_pages']}  "
            f"Orphans: {result['summary']['orphan_pages']}"
        ),
    ]
    lines.extend(f"Orphan: {url}" for url in result["orphan_pages"][:25])
    print_json_or_text(result, args.json, lines)


if __name__ == "__main__":
    main()
