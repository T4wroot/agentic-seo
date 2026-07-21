#!/usr/bin/env python3
"""Discover and validate XML sitemaps."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone

from seo_common import (
    discover_sitemap_urls,
    fetch_url,
    issue,
    normalize_url,
    parse_html,
    parse_sitemap_xml,
    print_json_or_text,
    same_host,
)


def check_sitemaps(site_url: str, sitemap_urls: list[str] | None = None, fetch_urls: bool = False, timeout: int = 15, max_urls: int = 100) -> dict:
    sitemap_urls = sitemap_urls or discover_sitemap_urls(site_url, timeout=timeout)
    result = {
        "site": normalize_url(site_url),
        "sitemaps_checked": [],
        "urls": [],
        "summary": {"sitemaps": 0, "urls": 0, "indexes": 0, "issues": 0},
        "issues": [],
    }
    queue = list(dict.fromkeys(sitemap_urls))
    seen_sitemaps = set()
    seen_urls = set()

    while queue and len(seen_sitemaps) < 25:
        sm_url = normalize_url(queue.pop(0), site_url)
        if sm_url in seen_sitemaps:
            continue
        seen_sitemaps.add(sm_url)
        fetched = fetch_url(sm_url, timeout=timeout, max_bytes=8_000_000)
        entry = {
            "url": sm_url,
            "status": fetched.get("status"),
            "final_url": fetched.get("url"),
            "redirects": fetched.get("redirect_chain", []),
            "type": None,
            "url_count": 0,
            "sitemap_count": 0,
            "error": fetched.get("error"),
        }
        if fetched.get("status") != 200:
            result["issues"].append(issue("error", f"Sitemap returned HTTP {fetched.get('status')}", sm_url, fetched.get("error")))
            result["sitemaps_checked"].append(entry)
            continue
        parsed = parse_sitemap_xml(fetched.get("text") or "", sm_url)
        entry["type"] = parsed["type"]
        entry["error"] = parsed["error"]
        entry["url_count"] = len(parsed["urls"])
        entry["sitemap_count"] = len(parsed["sitemaps"])
        if parsed["error"]:
            result["issues"].append(issue("error", f"Invalid sitemap XML: {parsed['error']}", sm_url))
        if parsed["type"] == "sitemapindex":
            result["summary"]["indexes"] += 1
            queue.extend(item["loc"] for item in parsed["sitemaps"])
        if parsed["type"] == "urlset" and len(parsed["urls"]) > 50000:
            result["issues"].append(issue("error", "Sitemap exceeds 50,000 URL limit", sm_url, str(len(parsed["urls"]))))

        for row in parsed["urls"]:
            loc = row["loc"]
            if loc in seen_urls:
                result["issues"].append(issue("warning", "Duplicate URL in sitemap set", loc))
                continue
            seen_urls.add(loc)
            url_entry = {"url": loc, **{k: v for k, v in row.items() if k != "loc"}, "checks": {}}
            if not loc.startswith("https://"):
                result["issues"].append(issue("warning", "Sitemap URL is not HTTPS", loc))
            if not same_host(site_url, loc):
                result["issues"].append(issue("warning", "Sitemap URL is cross-host", loc))
            if not row.get("lastmod"):
                result["issues"].append(issue("info", "Sitemap URL missing lastmod", loc))
            elif not re.match(r"^\d{4}-\d{2}-\d{2}", row["lastmod"]):
                result["issues"].append(issue("warning", "Sitemap lastmod is not ISO-like", loc, row["lastmod"]))
            elif row["lastmod"][:10] > datetime.now(timezone.utc).date().isoformat():
                result["issues"].append(issue("warning", "Sitemap lastmod is in the future", loc, row["lastmod"]))

            if fetch_urls and len(result["urls"]) < max_urls:
                page = fetch_url(loc, timeout=timeout, max_bytes=1_000_000)
                url_entry["checks"]["status"] = page.get("status")
                url_entry["checks"]["final_url"] = page.get("url")
                url_entry["checks"]["redirects"] = page.get("redirect_chain", [])
                if page.get("status") and page["status"] >= 400:
                    result["issues"].append(issue("error", f"Sitemap URL returns HTTP {page['status']}", loc))
                if page.get("redirect_chain"):
                    result["issues"].append(issue("warning", "Sitemap URL redirects", loc, " -> ".join(page["redirect_chain"] + [page.get("url", "")])))
                ctype = page.get("headers", {}).get("content-type", "")
                if page.get("text") and "html" in ctype:
                    html = parse_html(page["text"], page.get("url") or loc)
                    url_entry["checks"]["meta_robots"] = html.get("meta_robots")
                    url_entry["checks"]["canonical"] = html.get("canonical")
                    if html.get("meta_robots") and "noindex" in html["meta_robots"].lower():
                        result["issues"].append(issue("error", "Sitemap URL has meta noindex", loc, html["meta_robots"]))
                    if html.get("canonical") and normalize_url(html["canonical"]) != normalize_url(page.get("url") or loc):
                        result["issues"].append(issue("warning", "Canonical does not match sitemap URL", loc, html["canonical"]))
            result["urls"].append(url_entry)
        result["sitemaps_checked"].append(entry)

    result["summary"]["sitemaps"] = len(result["sitemaps_checked"])
    result["summary"]["urls"] = len(result["urls"])
    result["summary"]["issues"] = len(result["issues"])
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Discover and validate XML sitemaps")
    parser.add_argument("site", help="Site URL")
    parser.add_argument("--sitemap", action="append", help="Explicit sitemap URL; can be repeated")
    parser.add_argument("--fetch-urls", action="store_true", help="Fetch sitemap URLs for status/noindex/canonical checks")
    parser.add_argument("--max-urls", type=int, default=100, help="Max sitemap URLs to fetch when --fetch-urls is used")
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--json", "-j", action="store_true", help="Output JSON")
    args = parser.parse_args()
    result = check_sitemaps(args.site, args.sitemap, args.fetch_urls, args.timeout, args.max_urls)
    lines = [
        f"Sitemap check for {result['site']}",
        f"Sitemaps: {result['summary']['sitemaps']}  URLs: {result['summary']['urls']}  Issues: {result['summary']['issues']}",
    ] + [f"[{i['severity']}] {i['message']}: {i.get('url') or ''}" for i in result["issues"][:25]]
    print_json_or_text(result, args.json, lines)


if __name__ == "__main__":
    main()
