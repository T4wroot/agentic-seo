#!/usr/bin/env python3
"""Robots-aware shallow site crawler with SEO metadata checks."""

from __future__ import annotations

import argparse
import json
from collections import Counter, defaultdict, deque

from seo_common import (
    clean_url,
    discover_sitemap_urls,
    fetch_robots,
    fetch_url,
    issue,
    normalize_url,
    parse_html,
    parse_sitemap_xml,
    print_json_or_text,
    robots_allowed,
    same_host,
)


def sitemap_seeds(site: str, timeout: int, limit: int) -> list[str]:
    seeds = []
    for sm in discover_sitemap_urls(site, timeout=timeout)[:10]:
        fetched = fetch_url(sm, timeout=timeout, max_bytes=8_000_000)
        if fetched.get("status") != 200:
            continue
        parsed = parse_sitemap_xml(fetched.get("text") or "", sm)
        if parsed["type"] == "urlset":
            seeds.extend(row["loc"] for row in parsed["urls"])
        elif parsed["type"] == "sitemapindex":
            for child in parsed["sitemaps"][:5]:
                child_fetch = fetch_url(child["loc"], timeout=timeout, max_bytes=8_000_000)
                child_parsed = parse_sitemap_xml(child_fetch.get("text") or "", child["loc"])
                seeds.extend(row["loc"] for row in child_parsed["urls"])
        if len(seeds) >= limit:
            break
    return list(dict.fromkeys(seeds))[:limit]


def crawl(site: str, max_pages: int = 50, depth: int = 2, timeout: int = 15, use_sitemap: bool = True) -> dict:
    start = normalize_url(site)
    robots = fetch_robots(start, timeout=timeout)
    parsed_robots = robots.get("parsed")
    queue = deque([(start, 0, "seed")])
    if use_sitemap:
        for seed in sitemap_seeds(start, timeout, max_pages):
            if same_host(start, seed):
                queue.append((seed, 0, "sitemap"))

    seen = set()
    pages = {}
    inbound = defaultdict(set)
    issues = []
    title_counter = Counter()
    desc_counter = Counter()
    h1_counter = Counter()

    while queue and len(seen) < max_pages:
        url, current_depth, source = queue.popleft()
        url = clean_url(url)
        if url in seen or not same_host(start, url):
            continue
        seen.add(url)
        allowed, robots_rule = robots_allowed(parsed_robots, url, "Googlebot")
        if not allowed:
            pages[url] = {"url": url, "source": source, "depth": current_depth, "robots_allowed": False, "robots_rule": robots_rule}
            issues.append(issue("warning", "URL blocked by robots.txt", url, robots_rule))
            continue
        fetched = fetch_url(url, timeout=timeout, max_bytes=2_000_000)
        page = {
            "url": url,
            "final_url": fetched.get("url"),
            "source": source,
            "depth": current_depth,
            "status": fetched.get("status"),
            "redirects": fetched.get("redirect_chain", []),
            "robots_allowed": True,
            "robots_rule": robots_rule,
            "title": None,
            "meta_description": None,
            "h1": [],
            "canonical": None,
            "meta_robots": None,
            "word_count": 0,
            "outlinks": [],
            "error": fetched.get("error"),
        }
        ctype = fetched.get("headers", {}).get("content-type", "")
        if fetched.get("status") and fetched["status"] >= 400:
            issues.append(issue("error", f"HTTP {fetched['status']}", url))
        if fetched.get("redirect_chain"):
            issues.append(issue("info", "URL redirects", url))
        if fetched.get("text") and "html" in ctype:
            html = parse_html(fetched["text"], fetched.get("url") or url)
            page.update({
                "title": html["title"],
                "meta_description": html["meta_description"],
                "h1": html["headings"]["h1"],
                "canonical": html["canonical"],
                "meta_robots": html["meta_robots"],
                "word_count": html["word_count"],
                "outlinks": [link["href"] for link in html["links"] if same_host(start, link["href"])],
            })
            if page["title"]:
                title_counter[page["title"]] += 1
            else:
                issues.append(issue("warning", "Missing title", url))
            if page["meta_description"]:
                desc_counter[page["meta_description"]] += 1
            else:
                issues.append(issue("info", "Missing meta description", url))
            if page["h1"]:
                h1_counter[page["h1"][0]] += 1
            else:
                issues.append(issue("warning", "Missing H1", url))
            if page["meta_robots"] and "noindex" in page["meta_robots"].lower():
                issues.append(issue("warning", "Page has meta noindex", url, page["meta_robots"]))
            if page["canonical"] and not same_host(start, page["canonical"]):
                issues.append(issue("warning", "Cross-host canonical", url, page["canonical"]))

            if current_depth < depth:
                for link in page["outlinks"]:
                    clean = clean_url(link)
                    inbound[clean].add(url)
                    if clean not in seen:
                        queue.append((clean, current_depth + 1, "link"))
        pages[url] = page

    for label, counter in (("duplicate title", title_counter), ("duplicate meta description", desc_counter), ("duplicate H1", h1_counter)):
        for value, count in counter.items():
            if count > 1:
                issues.append(issue("warning", f"{label}: {count} pages", evidence=value[:160]))

    orphan_candidates = [url for url, page in pages.items() if page.get("source") == "sitemap" and not inbound.get(url) and url != start]
    for url in orphan_candidates[:50]:
        issues.append(issue("info", "Sitemap URL was not discovered through internal links in this crawl", url))

    result = {
        "site": start,
        "robots_url": robots["url"],
        "pages_crawled": len(pages),
        "max_depth": depth,
        "pages": pages,
        "status_counts": dict(Counter(str(p.get("status")) for p in pages.values())),
        "duplicates": {
            "titles": {k: v for k, v in title_counter.items() if v > 1},
            "meta_descriptions": {k: v for k, v in desc_counter.items() if v > 1},
            "h1": {k: v for k, v in h1_counter.items() if v > 1},
        },
        "orphan_candidates": orphan_candidates,
        "issues": issues,
    }
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a pragmatic crawl audit")
    parser.add_argument("site")
    parser.add_argument("--max-pages", type=int, default=50)
    parser.add_argument("--depth", type=int, default=2)
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--no-sitemap", action="store_true")
    parser.add_argument("--json", "-j", action="store_true")
    args = parser.parse_args()
    result = crawl(args.site, args.max_pages, args.depth, args.timeout, not args.no_sitemap)
    lines = [
        f"Crawl audit for {result['site']}",
        f"Pages crawled: {result['pages_crawled']}  Issues: {len(result['issues'])}",
    ] + [f"[{i['severity']}] {i['message']} {i.get('url') or ''}" for i in result["issues"][:25]]
    print_json_or_text(result, args.json, lines)


if __name__ == "__main__":
    main()
