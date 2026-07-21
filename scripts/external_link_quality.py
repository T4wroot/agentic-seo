#!/usr/bin/env python3
"""Audit external links for status, redirects, rel attributes, and trust patterns."""

from __future__ import annotations

import argparse
from collections import Counter
from urllib.parse import urlparse

from seo_common import fetch_url, normalize_url, parse_html, print_json_or_text, same_host


LOW_TRUST_HOST_HINTS = (
    "bit.ly",
    "goo.gl",
    "tinyurl.com",
    "t.co",
    "ow.ly",
    "buff.ly",
    "linktr.ee",
    "adf.ly",
    "clickbank.net",
)


def extract_external_links(html: str, page_url: str, site_url: str) -> list[dict]:
    parsed = parse_html(html, page_url)
    output = []
    for link in parsed.get("links", []):
        href = link.get("href") or ""
        if not href or same_host(site_url, href):
            continue
        rel = [str(v).lower() for v in (link.get("rel") or [])]
        output.append(
            {
                "source": page_url,
                "url": normalize_url(href, page_url),
                "anchor": link.get("text") or "",
                "rel": rel,
                "nofollow": "nofollow" in rel,
                "sponsored": "sponsored" in rel,
                "ugc": "ugc" in rel,
            }
        )
    return output


def _check_external_url(url: str, timeout: int) -> dict:
    head = fetch_url(url, method="HEAD", timeout=timeout, allow_redirects=True, max_bytes=0)
    if head.get("status") in (405, 403, None) and head.get("error"):
        return fetch_url(url, method="GET", timeout=timeout, allow_redirects=True, max_bytes=200_000)
    return head


def audit_external_links(urls: list[str], check_status: bool = True, timeout: int = 15, max_links: int = 200) -> dict:
    pages = []
    links = []
    errors = []
    for source in urls:
        source_url = normalize_url(source)
        fetched = fetch_url(source_url, timeout=timeout, max_bytes=2_000_000)
        pages.append({"url": source_url, "status": fetched.get("status"), "error": fetched.get("error")})
        if fetched.get("status") != 200 or not fetched.get("text"):
            errors.append({"url": source_url, "status": fetched.get("status"), "error": fetched.get("error")})
            continue
        links.extend(extract_external_links(fetched["text"], fetched.get("url") or source_url, source_url))

    deduped = {}
    for link in links:
        deduped.setdefault(link["url"], link)

    checked = []
    for link in list(deduped.values())[:max_links]:
        row = dict(link)
        host = urlparse(link["url"]).netloc.lower()
        row["host"] = host
        row["low_trust_pattern"] = any(host == hint or host.endswith(f".{hint}") for hint in LOW_TRUST_HOST_HINTS)
        if check_status:
            fetched = _check_external_url(link["url"], timeout=timeout)
            row["status"] = fetched.get("status")
            row["final_url"] = fetched.get("url")
            row["redirect_chain"] = fetched.get("redirect_chain", [])
            row["error"] = fetched.get("error")
        checked.append(row)

    broken = [l for l in checked if l.get("status") and l["status"] >= 400]
    redirects = [l for l in checked if l.get("redirect_chain")]
    low_trust = [l for l in checked if l.get("low_trust_pattern")]
    commercial_without_rel = [l for l in checked if not (l.get("nofollow") or l.get("sponsored") or l.get("ugc")) and _looks_commercial(l)]
    hosts = Counter(l["host"] for l in checked if l.get("host"))
    issues = []
    if broken:
        issues.append({"severity": "error", "type": "broken_external_links", "count": len(broken), "message": "External links return 4xx/5xx"})
    if redirects:
        issues.append({"severity": "warning", "type": "redirecting_external_links", "count": len(redirects), "message": "External links redirect"})
    if low_trust:
        issues.append({"severity": "warning", "type": "low_trust_patterns", "count": len(low_trust), "message": "External links match shortener or low-trust host patterns"})
    if commercial_without_rel:
        issues.append({"severity": "info", "type": "commercial_rel_review", "count": len(commercial_without_rel), "message": "Commercial-looking links may need rel=sponsored/nofollow review"})

    return {
        "sources": urls,
        "pages": pages,
        "summary": {
            "external_links_found": len(links),
            "unique_external_links": len(deduped),
            "checked_links": len(checked),
            "broken_links": len(broken),
            "redirecting_links": len(redirects),
            "low_trust_pattern_links": len(low_trust),
            "commercial_rel_review": len(commercial_without_rel),
        },
        "top_external_hosts": [{"host": host, "count": count} for host, count in hosts.most_common(25)],
        "links": checked,
        "issues": issues,
        "errors": errors,
    }


def _looks_commercial(link: dict) -> bool:
    text = f"{link.get('anchor', '')} {link.get('url', '')}".lower()
    return any(token in text for token in ("affiliate", "sponsor", "coupon", "deal", "promo", "ref=", "utm_medium=affiliate"))


def _read_url_file(path: str) -> list[str]:
    with open(path, "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.lstrip().startswith("#")]


def main() -> None:
    parser = argparse.ArgumentParser(description="Audit external link quality")
    parser.add_argument("url", nargs="?", help="Page URL to audit")
    parser.add_argument("--url-file", help="File containing page URLs to audit")
    parser.add_argument("--no-check-status", action="store_true", help="Skip status/redirect checks")
    parser.add_argument("--max-links", type=int, default=200, help="Maximum unique external links to check")
    parser.add_argument("--timeout", type=int, default=15)
    parser.add_argument("--json", "-j", action="store_true", help="Output JSON")
    args = parser.parse_args()

    urls = []
    if args.url:
        urls.append(args.url)
    if args.url_file:
        urls.extend(_read_url_file(args.url_file))
    if not urls:
        parser.error("Provide a URL or --url-file")

    result = audit_external_links(urls, check_status=not args.no_check_status, timeout=args.timeout, max_links=args.max_links)
    lines = [
        f"External link quality audit for {len(urls)} page(s)",
        (
            f"Unique external links: {result['summary']['unique_external_links']}  "
            f"Broken: {result['summary']['broken_links']}  "
            f"Redirects: {result['summary']['redirecting_links']}"
        ),
    ]
    lines.extend(f"[{issue['severity']}] {issue['message']}: {issue['count']}" for issue in result["issues"])
    print_json_or_text(result, args.json, lines)


if __name__ == "__main__":
    main()
