#!/usr/bin/env python3
"""Audit internal anchor text quality and diversity."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict, deque
from urllib.parse import urlparse

from seo_common import fetch_url, normalize_url, parse_html, print_json_or_text, same_host


GENERIC_ANCHORS = {
    "",
    "click here",
    "here",
    "learn more",
    "read more",
    "more",
    "this",
    "link",
    "website",
    "page",
    "continue reading",
}


def _canonical_page(url: str) -> str:
    parsed = urlparse(normalize_url(url))
    path = parsed.path or "/"
    if path != "/":
        path = path.rstrip("/")
    return f"{parsed.scheme}://{parsed.netloc}{path}"


def extract_internal_anchors(html: str, page_url: str, site_url: str) -> list[dict]:
    parsed = parse_html(html, page_url)
    links = []
    for link in parsed.get("links", []):
        href = link.get("href") or ""
        if not href or not same_host(site_url, href):
            continue
        rel = [str(v).lower() for v in (link.get("rel") or [])]
        text = (link.get("text") or "").strip()
        links.append(
            {
                "source": _canonical_page(page_url),
                "target": _canonical_page(href),
                "anchor": text,
                "rel": rel,
                "nofollow": "nofollow" in rel,
            }
        )
    return links


def crawl_internal_anchors(start_url: str, depth: int = 1, max_pages: int = 25, timeout: int = 15) -> dict:
    start_url = normalize_url(start_url)
    queue = deque([(start_url, 0)])
    seen = set()
    pages = {}
    links = []
    fetch_errors = []

    while queue and len(seen) < max_pages:
        url, current_depth = queue.popleft()
        page_key = _canonical_page(url)
        if page_key in seen or current_depth > depth:
            continue
        seen.add(page_key)
        fetched = fetch_url(url, timeout=timeout, max_bytes=2_000_000)
        pages[page_key] = {
            "url": page_key,
            "status": fetched.get("status"),
            "final_url": fetched.get("url"),
            "error": fetched.get("error"),
            "depth": current_depth,
        }
        if fetched.get("error") or fetched.get("status") != 200 or not fetched.get("text"):
            fetch_errors.append({"url": url, "status": fetched.get("status"), "error": fetched.get("error")})
            continue
        page_links = extract_internal_anchors(fetched["text"], fetched.get("url") or url, start_url)
        links.extend(page_links)
        if current_depth < depth:
            for link in page_links:
                if link["target"] not in seen and len(seen) + len(queue) < max_pages:
                    queue.append((link["target"], current_depth + 1))

    return {"pages": pages, "links": links, "fetch_errors": fetch_errors}


def audit_anchor_text(start_url: str, depth: int = 1, max_pages: int = 25, timeout: int = 15) -> dict:
    crawl = crawl_internal_anchors(start_url, depth=depth, max_pages=max_pages, timeout=timeout)
    links = crawl["links"]
    by_target: dict[str, list[str]] = defaultdict(list)
    text_counter = Counter()
    generic = []
    empty = []
    nofollow = []

    for link in links:
        text = (link.get("anchor") or "").strip()
        normalized_text = " ".join(text.lower().split())
        by_target[link["target"]].append(text)
        if text:
            text_counter[normalized_text] += 1
        if not text:
            empty.append(link)
        elif normalized_text in GENERIC_ANCHORS:
            generic.append(link)
        if link.get("nofollow"):
            nofollow.append(link)

    target_rows = []
    overused_exact = []
    low_diversity = []
    for target, anchors in sorted(by_target.items()):
        normalized = [" ".join(a.lower().split()) for a in anchors if a.strip()]
        total = len(anchors)
        unique = len(set(normalized))
        diversity_ratio = round(unique / max(1, len(normalized)), 2) if normalized else 0
        top_anchor, top_count = ("", 0)
        if normalized:
            top_anchor, top_count = Counter(normalized).most_common(1)[0]
        row = {
            "target": target,
            "total_internal_links": total,
            "unique_anchor_texts": unique,
            "diversity_ratio": diversity_ratio,
            "top_anchor": top_anchor,
            "top_anchor_count": top_count,
        }
        target_rows.append(row)
        if top_count >= 5 and top_count / max(1, len(normalized)) >= 0.8:
            overused_exact.append(row)
        if total >= 3 and diversity_ratio < 0.34:
            low_diversity.append(row)

    issues = []
    if empty:
        issues.append({"severity": "error", "type": "empty_anchor", "count": len(empty), "message": "Internal links with empty anchor text"})
    if generic:
        issues.append({"severity": "warning", "type": "generic_anchor", "count": len(generic), "message": "Generic internal anchor text is overused"})
    if nofollow:
        issues.append({"severity": "warning", "type": "internal_nofollow", "count": len(nofollow), "message": "Internal links use nofollow"})
    if overused_exact:
        issues.append({"severity": "warning", "type": "exact_match_overuse", "count": len(overused_exact), "message": "Targets have highly repetitive anchor text"})
    if low_diversity:
        issues.append({"severity": "info", "type": "low_anchor_diversity", "count": len(low_diversity), "message": "Targets have low anchor diversity"})

    return {
        "start_url": normalize_url(start_url),
        "pages_crawled": len(crawl["pages"]),
        "links_analyzed": len(links),
        "summary": {
            "unique_targets": len(by_target),
            "empty_anchors": len(empty),
            "generic_anchors": len(generic),
            "nofollow_internal_links": len(nofollow),
            "overused_exact_match_targets": len(overused_exact),
            "low_diversity_targets": len(low_diversity),
        },
        "top_anchor_texts": [{"anchor": text, "count": count} for text, count in text_counter.most_common(25)],
        "targets": target_rows,
        "examples": {
            "empty_anchors": empty[:20],
            "generic_anchors": generic[:20],
            "nofollow_internal_links": nofollow[:20],
            "overused_exact_match_targets": overused_exact[:20],
            "low_diversity_targets": low_diversity[:20],
        },
        "issues": issues,
        "fetch_errors": crawl["fetch_errors"],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit internal anchor text diversity and quality")
    parser.add_argument("url", help="Website URL to crawl")
    parser.add_argument("--depth", type=int, default=1, help="Internal crawl depth (default: 1)")
    parser.add_argument("--max-pages", type=int, default=25, help="Maximum pages to crawl (default: 25)")
    parser.add_argument("--timeout", type=int, default=15, help="Request timeout in seconds")
    parser.add_argument("--json", "-j", action="store_true", help="Output JSON")
    args = parser.parse_args()

    result = audit_anchor_text(args.url, depth=args.depth, max_pages=args.max_pages, timeout=args.timeout)
    lines = [
        f"Anchor text audit for {result['start_url']}",
        f"Pages crawled: {result['pages_crawled']}  Links analyzed: {result['links_analyzed']}",
        (
            "Issues: "
            f"empty={result['summary']['empty_anchors']} "
            f"generic={result['summary']['generic_anchors']} "
            f"nofollow={result['summary']['nofollow_internal_links']} "
            f"exact_match_targets={result['summary']['overused_exact_match_targets']}"
        ),
    ]
    lines.extend(f"[{issue['severity']}] {issue['message']}: {issue['count']}" for issue in result["issues"])
    print_json_or_text(result, args.json, lines)


if __name__ == "__main__":
    main()
